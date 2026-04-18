from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.auth_models import User
from api.deps import require_role
from db.mongo import get_database

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
    created_at: datetime

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

@router.post("/", response_model=Job)
def create_job(
    job_in: JobCreate,
    current_user: User = Depends(require_role("recruiter")),
):
    db = get_database()
    job_id = str(uuid.uuid4())
    job_doc = {
        "id": job_id,
        "title": job_in.title,
        "description": job_in.description,
        "created_at": _utcnow(),
    }
    db.jobs.insert_one(job_doc)
    return Job(**job_doc)

@router.get("/", response_model=List[Job])
def list_jobs():
    db = get_database()
    cur = db.jobs.find().sort("created_at", -1)
    jobs = []
    for doc in cur:
        doc.pop("_id", None)
        jobs.append(Job(**doc))
    return jobs

@router.get("/{job_id}", response_model=Job)
def get_job(job_id: str):
    db = get_database()
    doc = db.jobs.find_one({"id": job_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Job not found")
    doc.pop("_id", None)
    return Job(**doc)

@router.patch("/{job_id}", response_model=Job)
def update_job(
    job_id: str,
    job_in: JobUpdate,
    current_user: User = Depends(require_role("recruiter")),
):
    db = get_database()
    update_data = {k: v for k, v in job_in.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    res = db.jobs.find_one_and_update(
        {"id": job_id},
        {"$set": update_data},
        return_document=True
    )
    if not res:
        raise HTTPException(status_code=404, detail="Job not found")
    res.pop("_id", None)
    return Job(**res)

@router.delete("/{job_id}")
def delete_job(
    job_id: str,
    current_user: User = Depends(require_role("recruiter")),
):
    db = get_database()
    res = db.jobs.delete_one({"id": job_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": "deleted"}
