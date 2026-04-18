"""Single request: resume upload + job text → OCR, structuring, background, score (no LangGraph HITL)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from hiring_agent import config
from hiring_agent.agents.background_analysis.agent import run_background_analysis
from hiring_agent.agents.hr_strategy.models import HRJobSpec
from hiring_agent.agents.ocr_agent import extract_and_arrange_resume_from_path, is_allowed_upload_suffix
from hiring_agent.agents.scoring.agent import score_match
from hiring_agent.api.deps import verify_hiring_agent_api_key
from hiring_agent.fairness.injection_sanitize import sanitize_resume_text
from hiring_agent.graph.pipeline import extract_hr_job_spec_from_text

router = APIRouter(prefix="/analyze", tags=["analyze"])

_ALLOWED_EXT_HELP = ".pdf / .png / .jpg / .jpeg / .webp / .gif / .bmp / .tiff / .tif"


class AnalyzeResumeResponse(BaseModel):
    scorecard: dict[str, Any]
    job_spec: dict[str, Any]
    arranged_resume: dict[str, Any]
    background_result: dict[str, Any]
    ocr_char_count: int
    injection_sanitize_meta: dict[str, Any] | None = None
    hitl_style_note: str | None = Field(
        default=None,
        description="Note when the model suggests human review; the endpoint still returns the automatic score draft.",
    )


def _resolve_job_spec(
    hr_requirement_text: str | None,
    job_spec_json: str | None,
) -> dict[str, Any]:
    if job_spec_json and job_spec_json.strip():
        try:
            return HRJobSpec.model_validate_json(job_spec_json.strip()).model_dump(mode="json")
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(status_code=400, detail=f"job_spec_json is not valid HRJobSpec: {e!s}") from e
    text = (hr_requirement_text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Provide hr_requirement_text or valid job_spec_json")
    if not config.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not set; cannot extract job spec from text")
    try:
        return extract_hr_job_spec_from_text(text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


async def _analyze_resume_core(
    resume: UploadFile,
    hr_requirement_text: str | None,
    job_spec_json: str | None,
    candidate_github: str | None,
    google_scholar_url: str | None,
    candidate_name_override: str | None,
) -> AnalyzeResumeResponse:
    if not config.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not set")

    raw_name = resume.filename or "upload"
    suffix = Path(raw_name).suffix
    if not is_allowed_upload_suffix(suffix):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type {suffix or '(no extension)'}; allowed: {_ALLOWED_EXT_HELP}",
        )

    content = await resume.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    job_spec = _resolve_job_spec(hr_requirement_text, job_spec_json)

    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        try:
            extracted = await run_in_threadpool(extract_and_arrange_resume_from_path, tmp_path)
        except ValueError as e:
            raise HTTPException(status_code=503, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Resume parsing failed: {e!s}") from e

        safe_ocr, ocr_inj = sanitize_resume_text(extracted.ocr_text)
        arranged = extracted.arranged_profile.model_dump(mode="json")

        arr = arranged
        name = (arr.get("candidate_name") or "").strip() or (candidate_name_override or "").strip() or None
        bg = run_background_analysis(name, candidate_github, google_scholar_url)
        bg_dict = bg.model_dump(mode="json")

        sc = score_match(job_spec, arranged, bg_dict)
        sc_dict = sc.model_dump(mode="json")

        note: str | None = None
        if sc.hitl_suggested or sc.overall_confidence < 0.55:
            parts = []
            if sc.hitl_reason:
                parts.append(sc.hitl_reason)
            parts.append(
                f"Model confidence {sc.overall_confidence:.2f}; human review is recommended. "
                "Below is the automatic score draft."
            )
            note = " ".join(parts)

        inj_meta: dict[str, Any] = {"ocr_pass": ocr_inj, "arrange_pass": {"mode": "gpt4o_single_pass"}}

        return AnalyzeResumeResponse(
            scorecard=sc_dict,
            job_spec=job_spec,
            arranged_resume=arranged,
            background_result=bg_dict,
            ocr_char_count=len(safe_ocr),
            injection_sanitize_meta=inj_meta,
            hitl_style_note=note,
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@router.post("/resume", response_model=AnalyzeResumeResponse)
async def analyze_resume(
    _: None = Depends(verify_hiring_agent_api_key),
    resume: UploadFile = File(..., description="Resume PDF or image file"),
    hr_requirement_text: str | None = Form(
        default=None,
        description="Free-text job description (alternatively provide job_spec_json)",
    ),
    job_spec_json: str | None = Form(
        default=None,
        description="Optional HRJobSpec as JSON string; if set, hr_requirement_text is ignored",
    ),
    candidate_github: str | None = Form(default=None),
    google_scholar_url: str | None = Form(default=None),
    candidate_name_override: str | None = Form(default=None),
):
    return await _analyze_resume_core(
        resume,
        hr_requirement_text,
        job_spec_json,
        candidate_github,
        google_scholar_url,
        candidate_name_override,
    )
