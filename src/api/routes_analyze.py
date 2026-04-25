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
from services.rankings import trigger_re_evaluation, trigger_re_evaluation_all, get_my_submission as get_my_submission_svc
from monitoring.context import set_execution_context

router = APIRouter(prefix="/analyze", tags=["analyze"])

_UPLOAD_DIR = Path(config.UPLOADS_DIR) / "resumes"
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
    username: str,
    personal_statement: str | None = None,
):
    """Background task to perform the full LLM evaluation."""
    try:
        if not config.OPENAI_API_KEY:
            return

        # SET CONTEXT FOR AUTOMATIC TOKEN TRACKING
        set_execution_context(username=username, function_id="background_eval", user_role="candidate")

        job_spec = _resolve_job_spec(hr_requirement_text, job_spec_json)

        try:
            extracted = await run_in_threadpool(extract_and_arrange_resume_from_path, str(resume_path))
        except Exception as e:
            print(f"Resume parsing failed for {ranking_id}: {e}")
            return

        # Safety check on extracted text
        from safety.guardrails import moderate_text
        dec = moderate_text(
            extracted.ocr_text,
            stage="pipeline.resume_ocr.background_eval",
            role="candidate",
            username=username
        )
        if dec.blocked:
            from dashboard.repository import update_candidate_ranking_status
            update_candidate_ranking_status(ranking_id, "safety_blocked")
            from db.mongo import get_database
            get_database().candidate_rankings.update_one(
                {"ranking_id": ranking_id},
                {"$set": {"safety_meta": dec.as_meta()}}
            )
            from api.websockets import manager
            await manager.send_to_user(username, {
                "type": "submission_update",
                "status": "safety_blocked",
                "ranking_id": ranking_id,
                "reason": dec.reason
            })
            return

        safe_ocr, _ = sanitize_resume_text(extracted.ocr_text)
        arranged = extracted.arranged_profile.model_dump(mode="json")

        arr = arranged
        name = (arr.get("candidate_name") or "").strip() or (candidate_name_override or "").strip() or None
        bg = await run_in_threadpool(run_background_analysis, name, candidate_github, google_scholar_url)
        bg_dict = bg.model_dump(mode="json")

        sc = await run_in_threadpool(score_match, job_spec, arranged, bg_dict, personal_statement)
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

        # Notify via WebSocket
        from api.websockets import manager
        from services.rankings import get_ranking_by_id
        
        ranking_data = get_ranking_by_id(ranking_id)
        if ranking_data:
            job_id = ranking_data.get("job_id")
            # 1. Notify candidate
            await manager.send_to_user(username, {
                "type": "submission_update",
                "job_id": job_id,
                "status": "ready",
                "data": ranking_data
            })
            
            # 2. Notify recruiter (if watching this job)
            if job_id:
                await manager.broadcast_to_topic(f"job:{job_id}", {
                    "type": "ranking_update",
                    "job_id": job_id,
                    "ranking_id": ranking_id,
                    "status": "ready",
                    "data": ranking_data
                })

    except Exception as e:
        print(f"Background evaluation failed for {ranking_id}: {e}")
        from api.websockets import manager
        await manager.send_to_user(username, {
            "type": "submission_update",
            "ranking_id": ranking_id,
            "status": "error"
        })


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
    personal_statement: str | None = Form(default=None),
    current_user: User = Depends(require_role("candidate")),
):
    from datetime import datetime, timezone
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
                "personal_statement": personal_statement,
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
        if personal_statement:
            db.candidate_rankings.update_one({"ranking_id": ranking_id}, {"$set": {"personal_statement": personal_statement}})

    # Save resume file
    dest_path = _UPLOAD_DIR / f"{ranking_id}{suffix}"
    with dest_path.open("wb") as buffer:
        shutil.copyfileobj(resume.file, buffer)

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
        username=current_user.username,
        personal_statement=personal_statement,
    )

    return AnalyzeResumeResponse(ranking_id=ranking_id, status="evaluating")


@router.get("/my-submission/{job_id}")
async def get_my_submission_endpoint(
    job_id: str,
    current_user: User = Depends(require_role("candidate")),
):
    return get_my_submission_svc(job_id, current_user)


@router.post("/re-evaluate/{ranking_id}")
async def re_evaluate_resume(
    ranking_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role("recruiter")),
):
    return await trigger_re_evaluation(ranking_id, current_user, background_tasks)


@router.post("/re-evaluate-all/{job_id}")
async def re_evaluate_all(
    job_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role("recruiter")),
):
    return await trigger_re_evaluation_all(job_id, current_user, background_tasks)


@router.get("/resume/{ranking_id}")
async def get_resume_file(
    ranking_id: str,
    current_user: User = Depends(require_role("recruiter")),
):
    import re
    from datetime import datetime
    
    db = get_database()
    ranking = db.candidate_rankings.find_one({"ranking_id": ranking_id})
    
    # 1. Try to use resume_path from DB
    resume_path = None
    if ranking and ranking.get("resume_path"):
        p = Path(ranking["resume_path"])
        if p.exists():
            resume_path = p
    
    # 2. Fallback to ranking_id glob (old logic)
    if not resume_path:
        files = list(_UPLOAD_DIR.glob(f"{ranking_id}.*"))
        if files:
            resume_path = files[0]
            
    if not resume_path:
        raise HTTPException(status_code=404, detail="Resume not found")
    
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
    suffix = resume_path.suffix
    
    new_filename = f"HiringAgent-{candidate_name}-{ts}{suffix}"

    return FileResponse(
        path=resume_path,
        filename=new_filename,
        media_type="application/octet-stream"
    )
