from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, Form, BackgroundTasks

from api.auth_models import User
from api.deps import require_role, get_current_user
from services.jobs import list_jobs, get_job
from services.rankings import get_my_submission
from services.evaluations import submit_resume_for_analysis
from api.routes_analyze import AnalyzeResumeResponse
from api.routes_chat import chat_message, get_chat_history, ChatRequest, ChatResponse, ChatMessage

router = APIRouter(prefix="/candidate", tags=["candidate"])

# Jobs
@router.get("/jobs")
def list_candidate_jobs(current_user: User = Depends(require_role("candidate"))):
    return list_jobs(current_user)

@router.get("/jobs/{job_id}")
def get_candidate_job(job_id: str, current_user: User = Depends(require_role("candidate"))):
    return get_job(job_id)

# Analysis
@router.post("/resume", response_model=AnalyzeResumeResponse)
async def candidate_analyze_resume(
    background_tasks: BackgroundTasks,
    resume: UploadFile = File(...),
    job_id: str = Form(...),
    candidate_github: Optional[str] = Form(None),
    google_scholar_url: Optional[str] = Form(None),
    candidate_name_override: Optional[str] = Form(None),
    current_user: User = Depends(require_role("candidate")),
):
    return await submit_resume_for_analysis(
        background_tasks=background_tasks,
        resume=resume,
        job_id=job_id,
        current_user=current_user,
        candidate_github=candidate_github,
        google_scholar_url=google_scholar_url,
        candidate_name_override=candidate_name_override
    )

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
@router.post("/chat/message", response_model=ChatResponse)
async def candidate_chat_message(req: ChatRequest, current_user: User = Depends(require_role("candidate"))):
    return await chat_message(req, current_user)

@router.get("/chat/history", response_model=List[ChatMessage])
async def candidate_chat_history(current_user: User = Depends(require_role("candidate"))):
    return await get_chat_history(current_user)

@router.post("/chat/clear")
async def candidate_clear_chat(current_user: User = Depends(require_role("candidate"))):
    from api.routes_chat import clear_chat
    return await clear_chat(current_user)
