from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime

from api.auth_models import User
from api.deps import require_role, get_current_user_optional, get_current_user
from services.jobs import (
    list_jobs as list_jobs_svc,
    get_job as get_job_svc,
    create_job as create_job_svc,
    update_job as update_job_svc,
    delete_job as delete_job_svc,
    search_jobs as search_jobs_svc
)

router = APIRouter(prefix="/jobs", tags=["jobs"])

class JobCreate(BaseModel):
    title: str
    description: str

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class Job(BaseModel):
    id: str
    title: str
    description: str
    summary: Optional[str] = None
    created_at: datetime
    submitted: bool = False

@router.post("/", response_model=Job)
def create_job(
    job_in: JobCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role("recruiter")),
):
    return create_job_svc(job_in.title, job_in.description, current_user, background_tasks)

@router.get("/", response_model=List[Job])
def list_jobs(current_user: Optional[User] = Depends(get_current_user_optional)):
    return list_jobs_svc(current_user)

@router.get("/search", response_model=List[Job])
def search_jobs(
    q: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    return search_jobs_svc(q, current_user)

@router.get("/{job_id}", response_model=Job)
def get_job(job_id: str):
    return get_job_svc(job_id)

@router.patch("/{job_id}", response_model=Job)
def update_job(
    job_id: str,
    job_in: JobUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role("recruiter")),
):
    return update_job_svc(job_id, job_in.title, job_in.description, current_user, background_tasks)

@router.delete("/{job_id}")
def delete_job(
    job_id: str,
    current_user: User = Depends(require_role("recruiter")),
):
    delete_job_svc(job_id, current_user)
    return {"status": "deleted"}
