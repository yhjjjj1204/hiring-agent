"""Single request: resume upload + job text → OCR, structuring, background, score (no LangGraph HITL)."""

from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

import config
from agents.background_analysis.agent import run_background_analysis
from agents.hr_strategy.models import HRJobSpec
from agents.ocr_agent import extract_and_arrange_resume_from_path, is_allowed_upload_suffix
from agents.scoring.agent import score_match
from api.deps import verify_hiring_agent_api_key, require_role
from api.auth_models import User
from dashboard.repository import insert_candidate_ranking, update_candidate_ranking_result
from db.mongo import get_database
from fairness.injection_sanitize import sanitize_resume_text
from graph.pipeline import extract_hr_job_spec_from_text

router = APIRouter(prefix="/analyze", tags=["analyze"])

_UPLOAD_DIR = Path("uploads/resumes")
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

_ALLOWED_EXT_HELP = ".pdf / .png / .jpg / .jpeg / .webp / .gif / .bmp / .tiff / .tif"


class AnalyzeResumeResponse(BaseModel):
    ranking_id: str
    status: str


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


async def _background_evaluate_resume(
    ranking_id: str,
    resume_path: Path,
    hr_requirement_text: str | None,
    job_spec_json: str | None,
    candidate_github: str | None,
    google_scholar_url: str | None,
    candidate_name_override: str | None,
):
    """Background task to perform the full LLM evaluation."""
    try:
        if not config.OPENAI_API_KEY:
            return

        job_spec = _resolve_job_spec(hr_requirement_text, job_spec_json)

        try:
            extracted = await run_in_threadpool(extract_and_arrange_resume_from_path, str(resume_path))
        except Exception as e:
            print(f"Resume parsing failed for {ranking_id}: {e}")
            return

        safe_ocr, _ = sanitize_resume_text(extracted.ocr_text)
        arranged = extracted.arranged_profile.model_dump(mode="json")

        arr = arranged
        name = (arr.get("candidate_name") or "").strip() or (candidate_name_override or "").strip() or None
        bg = run_background_analysis(name, candidate_github, google_scholar_url)
        bg_dict = bg.model_dump(mode="json")

        sc = score_match(job_spec, arranged, bg_dict)
        sc_dict = sc.model_dump(mode="json")

        # Prepare dimensions
        dims_list = []
        for d in sc_dict.get("dimensions") or []:
            if isinstance(d, dict) and "name" in d and "score" in d:
                dims_list.append({
                    "name": d.get("name"),
                    "score": float(d.get("score", 0)),
                    "rationale": d.get("rationale", "")
                })

        update_candidate_ranking_result(
            ranking_id=ranking_id,
            overall_score=float(sc_dict.get("overall_score", 0)),
            dimensions=dims_list,
            summary=str(sc_dict.get("summary") or ""),
            scorecard=sc_dict,
            arranged_resume=arranged
        )
    except Exception as e:
        print(f"Background evaluation failed for {ranking_id}: {e}")


@router.post("/resume", response_model=AnalyzeResumeResponse)
async def analyze_resume(
    background_tasks: BackgroundTasks,
    _: None = Depends(verify_hiring_agent_api_key),
    resume: UploadFile = File(..., description="Resume PDF or image file"),
    job_id: str | None = Form(default=None),
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
    current_user: User = Depends(require_role("candidate")),
):
    db = get_database()
    if job_id and not hr_requirement_text and not job_spec_json:
        job = db.jobs.find_one({"id": job_id})
        if job:
            hr_requirement_text = job.get("description")

    raw_name = resume.filename or "upload"
    suffix = Path(raw_name).suffix
    if not is_allowed_upload_suffix(suffix):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type {suffix or '(no extension)'}; allowed: {_ALLOWED_EXT_HELP}",
        )

    # Check for existing submission to rewrite
    existing = None
    if job_id:
        existing = db.candidate_rankings.find_one({"candidate_ref": current_user.username, "job_id": job_id})
    
    if existing:
        ranking_id = existing["ranking_id"]
        # Delete old file(s)
        for old_file in _UPLOAD_DIR.glob(f"{ranking_id}.*"):
            try: os.unlink(old_file)
            except: pass
        
        # Reset entry
        db.candidate_rankings.update_one(
            {"ranking_id": ranking_id},
            {"$set": {
                "status": "evaluating",
                "overall_score": 0.0,
                "dimensions": [],
                "summary": "",
                "scorecard_snapshot": None,
                "arranged_resume": None,
                "candidate_info": {
                    "github": candidate_github,
                    "scholar_url": google_scholar_url,
                    "name_override": candidate_name_override,
                    "filename": raw_name
                },
                "evaluated_at": None,
                "submitted_at": datetime.now(timezone.utc)
            }}
        )
    else:
        ranking_id = str(uuid.uuid4())
        insert_candidate_ranking(
            ranking_id=ranking_id,
            candidate_ref=current_user.username,
            thread_id=None,
            job_id=job_id,
            candidate_info={
                "github": candidate_github,
                "scholar_url": google_scholar_url,
                "name_override": candidate_name_override,
                "filename": raw_name
            },
            status="evaluating"
        )

    # Save resume file
    dest_path = _UPLOAD_DIR / f"{ranking_id}{suffix}"
    with dest_path.open("wb") as buffer:
        shutil.copyfileobj(resume.file, buffer)

    from datetime import datetime, timezone
    # Start background task
    background_tasks.add_task(
        _background_evaluate_resume,
        ranking_id=ranking_id,
        resume_path=dest_path,
        hr_requirement_text=hr_requirement_text,
        job_spec_json=job_spec_json,
        candidate_github=candidate_github,
        google_scholar_url=google_scholar_url,
        candidate_name_override=candidate_name_override,
    )

    return AnalyzeResumeResponse(ranking_id=ranking_id, status="evaluating")


@router.get("/my-submission/{job_id}")
async def get_my_submission(
    job_id: str,
    current_user: User = Depends(require_role("candidate")),
):
    db = get_database()
    ranking = db.candidate_rankings.find_one({"candidate_ref": current_user.username, "job_id": job_id})
    if not ranking:
        raise HTTPException(status_code=404, detail="No submission found")
    ranking.pop("_id", None)
    return ranking


@router.post("/re-evaluate/{ranking_id}")
async def re_evaluate_resume(
    ranking_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role("recruiter")),
):
    db = get_database()
    ranking = db.candidate_rankings.find_one({"ranking_id": ranking_id})
    if not ranking:
        raise HTTPException(status_code=404, detail="Ranking not found")
    
    # Find the resume file
    files = list(_UPLOAD_DIR.glob(f"{ranking_id}.*"))
    if not files:
        raise HTTPException(status_code=404, detail="Resume file not found")
    resume_path = files[0]

    job_id = ranking.get("job_id")
    hr_requirement_text = None
    if job_id:
        job = db.jobs.find_one({"id": job_id})
        if job:
            hr_requirement_text = job.get("description")

    # Update status back to evaluating
    db.candidate_rankings.update_one(
        {"ranking_id": ranking_id},
        {"$set": {"status": "evaluating"}}
    )

    cinfo = ranking.get("candidate_info") or {}

    background_tasks.add_task(
        _background_evaluate_resume,
        ranking_id=ranking_id,
        resume_path=resume_path,
        hr_requirement_text=hr_requirement_text,
        job_spec_json=None,
        candidate_github=cinfo.get("github"),
        google_scholar_url=cinfo.get("scholar_url"),
        candidate_name_override=cinfo.get("name_override"),
    )

    return {"status": "evaluating"}


@router.post("/re-evaluate-all/{job_id}")
async def re_evaluate_all(
    job_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role("recruiter")),
):
    db = get_database()
    job = db.jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    hr_requirement_text = job.get("description")
    
    rankings = list(db.candidate_rankings.find({"job_id": job_id}))
    count = 0
    for r in rankings:
        ranking_id = r["ranking_id"]
        files = list(_UPLOAD_DIR.glob(f"{ranking_id}.*"))
        if not files:
            continue
        
        resume_path = files[0]
        cinfo = r.get("candidate_info") or {}
        
        db.candidate_rankings.update_one(
            {"ranking_id": ranking_id},
            {"$set": {"status": "evaluating"}}
        )
        
        background_tasks.add_task(
            _background_evaluate_resume,
            ranking_id=ranking_id,
            resume_path=resume_path,
            hr_requirement_text=hr_requirement_text,
            job_spec_json=None,
            candidate_github=cinfo.get("github"),
            google_scholar_url=cinfo.get("scholar_url"),
            candidate_name_override=cinfo.get("name_override"),
        )
        count += 1
        
    return {"status": "evaluating", "count": count}


@router.get("/resume/{ranking_id}")
async def get_resume_file(
    ranking_id: str,
    current_user: User = Depends(require_role("recruiter")),
):
    import re
    from datetime import datetime
    
    files = list(_UPLOAD_DIR.glob(f"{ranking_id}.*"))
    if not files:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    db = get_database()
    ranking = db.candidate_rankings.find_one({"ranking_id": ranking_id})
    
    # Determine candidate name for filename
    candidate_name = "unknown"
    if ranking:
        candidate_name = ranking.get("candidate_info", {}).get("name_override") or ranking.get("candidate_ref") or "unknown"
    
    # Sanitize candidate name for filename
    candidate_name = re.sub(r'[^\w\s-]', '', candidate_name).strip()
    candidate_name = re.sub(r'[-\s]+', '_', candidate_name)

    # Format timestamp
    ts = datetime.now().strftime("%Y%m%d.%H%M")
    
    # Preserve original extension
    suffix = Path(files[0]).suffix
    
    new_filename = f"HiringAgent-{candidate_name}-{ts}{suffix}"

    return FileResponse(
        path=files[0],
        filename=new_filename,
        media_type="application/octet-stream"
    )
