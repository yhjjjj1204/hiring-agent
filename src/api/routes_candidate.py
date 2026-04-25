from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, Form, BackgroundTasks

from api.auth_models import User
from api.deps import require_role, get_current_user
from services.jobs import list_jobs, get_job, search_jobs as search_jobs_svc
from services.rankings import get_my_submission
from dashboard.repository import insert_candidate_ranking
from api.routes_analyze import AnalyzeResumeResponse
from api.routes_chat import chat_message, get_chat_history, ChatRequest, ChatResponse, ChatMessage

router = APIRouter(prefix="/candidate", tags=["candidate"])

from db.mongo import get_database
from fastapi import HTTPException, BackgroundTasks, File, UploadFile, Form
from starlette.concurrency import run_in_threadpool
import uuid
from pathlib import Path
import shutil
import config
from agents.ocr_agent import extract_and_arrange_resume_from_path, is_allowed_upload_suffix

_UPLOAD_DIR = Path("uploads/resumes")
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
_ALLOWED_EXT_HELP = ".pdf / .png / .jpg / .jpeg / .webp / .gif / .bmp / .tiff / .tif"

# Jobs
@router.get("/jobs")
def list_candidate_jobs(current_user: User = Depends(require_role("candidate"))):
    return list_jobs(current_user)

@router.get("/jobs/search")
def search_candidate_jobs(q: str, current_user: User = Depends(require_role("candidate"))):
    return search_jobs_svc(q, current_user)

@router.get("/jobs/{job_id}")
def get_candidate_job(job_id: str, current_user: User = Depends(require_role("candidate"))):
    return get_job(job_id)

# Profile Management
@router.get("/profile")
def get_candidate_profile(current_user: User = Depends(require_role("candidate"))):
    db = get_database()
    user = db.users.find_one({"username": current_user.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "github": user.get("github", ""),
        "scholar_url": user.get("scholar_url", ""),
        "name_override": user.get("name_override", ""),
        "resume_filename": user.get("resume_filename", ""),
        "arranged_resume": user.get("arranged_resume"),
        "status": user.get("resume_status", "ready")
    }

@router.post("/profile/resume")
async def update_candidate_resume(
    background_tasks: BackgroundTasks,
    resume: UploadFile = File(...),
    current_user: User = Depends(require_role("candidate"))
):
    db = get_database()
    raw_name = resume.filename or "upload"
    suffix = Path(raw_name).suffix
    if not is_allowed_upload_suffix(suffix):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type {suffix or '(no extension)'}; allowed: {_ALLOWED_EXT_HELP}",
        )

    # Use a fixed naming convention for profile resumes to avoid clashing with job rankings if needed,
    # but we can also just use a unique ID and store it in the user profile.
    resume_id = str(uuid.uuid4())
    dest_path = _UPLOAD_DIR / f"profile_{resume_id}{suffix}"
    
    with dest_path.open("wb") as buffer:
        shutil.copyfileobj(resume.file, buffer)

    db.users.update_one(
        {"username": current_user.username},
        {"$set": {
            "resume_status": "evaluating",
            "resume_filename": raw_name,
            "resume_path": str(dest_path)
        }}
    )

    async def _analyze_profile_resume():
        from api.websockets import manager
        from safety.guardrails import moderate_text
        from monitoring.context import set_execution_context
        set_execution_context(username=current_user.username, user_role="candidate", function_id="profile_resume_analysis")
        try:
            extracted = await run_in_threadpool(extract_and_arrange_resume_from_path, str(dest_path))
            
            # Safety check on extracted text
            dec = moderate_text(
                extracted.ocr_text,
                stage="candidate.profile.resume_ocr",
                role="candidate",
                username=current_user.username
            )
            if dec.blocked:
                db.users.update_one(
                    {"username": current_user.username},
                    {"$set": {
                        "resume_status": "safety_blocked",
                        "safety_meta": dec.as_meta()
                    }}
                )
                await manager.send_to_user(current_user.username, {
                    "type": "profile_update",
                    "status": "safety_blocked",
                    "reason": dec.reason
                })
                return

            arranged = extracted.arranged_profile.model_dump(mode="json")
            db.users.update_one(
                {"username": current_user.username},
                {"$set": {
                    "resume_status": "ready",
                    "arranged_resume": arranged
                }}
            )
            # Notify via WebSocket
            await manager.send_to_user(current_user.username, {
                "type": "profile_update",
                "status": "ready",
                "arranged_resume": arranged,
                "resume_filename": raw_name
            })
        except Exception as e:
            print(f"Profile resume analysis failed for {current_user.username}: {e}")
            db.users.update_one(
                {"username": current_user.username},
                {"$set": {"resume_status": "error"}}
            )
            await manager.send_to_user(current_user.username, {
                "type": "profile_update",
                "status": "error"
            })

    background_tasks.add_task(_analyze_profile_resume)
    return {"status": "evaluating"}

@router.post("/profile/info")
def update_candidate_info(
    github: Optional[str] = Form(None),
    scholar_url: Optional[str] = Form(None),
    name_override: Optional[str] = Form(None),
    current_user: User = Depends(require_role("candidate"))
):
    db = get_database()
    db.users.update_one(
        {"username": current_user.username},
        {"$set": {
            "github": github or "",
            "scholar_url": scholar_url or "",
            "name_override": name_override or ""
        }}
    )
    return {"status": "updated"}

# Analysis / Application
@router.post("/apply/{job_id}", response_model=AnalyzeResumeResponse)
async def candidate_apply_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    personal_statement: Optional[str] = Form(None),
    current_user: User = Depends(require_role("candidate")),
):
    db = get_database()
    user = db.users.find_one({"username": current_user.username})
    if not user or not user.get("resume_path"):
        raise HTTPException(status_code=400, detail="Please upload your resume in the Resume Manager first.")

    # Convert resume_path (string) back to Path object
    resume_path = Path(user["resume_path"])
    if not resume_path.exists():
        raise HTTPException(status_code=400, detail="Stored resume file not found. Please re-upload.")

    job = db.jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    hr_requirement_text = job.get("description")
    
    # Check for existing submission
    existing = db.candidate_rankings.find_one({"candidate_ref": current_user.username, "job_id": job_id})
    
    if existing:
        ranking_id = existing["ranking_id"]
    else:
        ranking_id = str(uuid.uuid4())
        insert_candidate_ranking(
            ranking_id=ranking_id,
            candidate_ref=current_user.username,
            thread_id=None,
            job_id=job_id,
            status="evaluating"
        )

    # Store candidate info and personal statement in ranking
    db.candidate_rankings.update_one(
        {"ranking_id": ranking_id},
        {"$set": {
            "status": "evaluating",
            "personal_statement": personal_statement,
            "resume_path": str(resume_path),
            "candidate_info": {
                "github": user.get("github"),
                "scholar_url": user.get("scholar_url"),
                "name_override": user.get("name_override"),
                "filename": user.get("resume_filename")
            },
            "submitted_at": datetime.now(timezone.utc)
        }}
    )

    # Reuse the background evaluator but we might need to handle the personal statement too.
    # For now, let's keep it simple and just run the existing evaluator.
    from api.routes_analyze import _background_evaluate_resume
    background_tasks.add_task(
        _background_evaluate_resume,
        ranking_id=ranking_id,
        resume_path=resume_path,
        hr_requirement_text=hr_requirement_text,
        job_spec_json=None,
        candidate_github=user.get("github"),
        google_scholar_url=user.get("scholar_url"),
        candidate_name_override=user.get("name_override"),
        username=current_user.username,
        personal_statement=personal_statement,
    )

    return AnalyzeResumeResponse(ranking_id=ranking_id, status="evaluating")

@router.get("/my-submission/{job_id}")
def get_candidate_submission(job_id: str, current_user: User = Depends(require_role("candidate"))):
    from fastapi import HTTPException
    try:
        return get_my_submission(job_id, current_user)
    except HTTPException as e:
        if e.status_code == 404:
            return None # Return null to frontend to avoid 404 spam in terminal
        raise e

# Chat
@router.post("/chat/message")
async def candidate_chat_message(
    req: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role("candidate"))
):
    return await chat_message(req, background_tasks, current_user)

@router.get("/chat/history", response_model=List[ChatMessage])
async def candidate_chat_history(current_user: User = Depends(require_role("candidate"))):
    return await get_chat_history(current_user)

@router.post("/chat/clear")
async def candidate_clear_chat(current_user: User = Depends(require_role("candidate"))):
    from api.routes_chat import clear_chat
    return await clear_chat(current_user)
