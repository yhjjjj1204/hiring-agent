from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, BackgroundTasks, Query

from api.auth_models import User
from api.deps import require_role
from services.jobs import list_jobs, get_job, create_job, update_job, delete_job, search_jobs as search_jobs_svc
from services.rankings import list_candidate_rankings, trigger_re_evaluation, trigger_re_evaluation_all
from api.routes_chat import chat_message, get_chat_history, ChatRequest, ChatResponse, ChatMessage
from api.routes_dashboard import get_ranking
from monitoring.usage_service import get_user_usage_summary

from pydantic import BaseModel

class JobCreate(BaseModel):
    title: str
    description: str

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

router = APIRouter(prefix="/recruiter", tags=["recruiter"])

# Jobs
@router.get("/jobs")
def recruiter_list_jobs(current_user: User = Depends(require_role("recruiter"))):
    return list_jobs(current_user)

@router.get("/jobs/search")
def search_recruiter_jobs(q: str, current_user: User = Depends(require_role("recruiter"))):
    return search_jobs_svc(q, current_user)

@router.get("/jobs/{job_id}")
def recruiter_get_job(job_id: str, current_user: User = Depends(require_role("recruiter"))):
    return get_job(job_id)

@router.post("/jobs")
def recruiter_create_job(
    job: JobCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role("recruiter"))
):
    return create_job(job.title, job.description, current_user, background_tasks)

@router.patch("/jobs/{job_id}")
def recruiter_update_job(
    job_id: str,
    job: JobUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role("recruiter"))
):
    return update_job(job_id, job.title, job.description, current_user, background_tasks)


@router.delete("/jobs/{job_id}")
def recruiter_delete_job(job_id: str, current_user: User = Depends(require_role("recruiter"))):
    return delete_job(job_id, current_user)

# Dashboard / Rankings
@router.get("/rankings")
def recruiter_list_rankings(
    limit: int = Query(30),
    sort: str = Query("overall_score"),
    job_id: Optional[str] = Query(None),
    current_user: User = Depends(require_role("recruiter")),
):
    rows = list_candidate_rankings(current_user, job_id=job_id, limit=limit, sort_by=sort)
    return {"count": len(rows), "sort": sort, "items": rows}

@router.get("/ranking/{ranking_id}")
def recruiter_get_ranking(ranking_id: str, current_user: User = Depends(require_role("recruiter"))):
    return get_ranking(ranking_id, current_user)

# Evaluation
@router.post("/re-evaluate/{ranking_id}")
async def recruiter_re_evaluate(
    ranking_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role("recruiter")),
):
    return await trigger_re_evaluation(ranking_id, current_user, background_tasks)

@router.post("/re-evaluate-all/{job_id}")
async def recruiter_re_evaluate_all(
    job_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role("recruiter")),
):
    return await trigger_re_evaluation_all(job_id, current_user, background_tasks)

@router.get("/resume/{ranking_id}")
async def recruiter_get_resume(ranking_id: str, current_user: User = Depends(require_role("recruiter"))):
    from api.routes_analyze import get_resume_file
    return await get_resume_file(ranking_id, current_user)

@router.get("/usage")
async def recruiter_get_usage(current_user: User = Depends(require_role("recruiter"))):
    return get_user_usage_summary(current_user.username)

# Chat
@router.post("/chat/message")
async def recruiter_chat_message(
    req: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role("recruiter"))
):
    return await chat_message(req, background_tasks, current_user)

@router.get("/chat/history", response_model=List[ChatMessage])
async def recruiter_chat_history(current_user: User = Depends(require_role("recruiter"))):
    return await get_chat_history(current_user)

@router.post("/chat/clear")
async def recruiter_clear_chat(current_user: User = Depends(require_role("recruiter"))):
    from api.routes_chat import clear_chat
    return await clear_chat(current_user)
