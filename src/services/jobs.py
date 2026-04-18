from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import HTTPException
from api.auth_models import User
from db.mongo import get_database

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

def list_jobs(current_user: Optional[User] = None) -> List[dict[str, Any]]:
    db = get_database()
    cur = db.jobs.find().sort("created_at", -1)
    
    submitted_job_ids = set()
    if current_user:
        submissions = db.candidate_rankings.find({"candidate_ref": current_user.username}, {"job_id": 1})
        for s in submissions:
            jid = s.get("job_id")
            if jid:
                submitted_job_ids.add(jid)

    jobs = []
    for doc in cur:
        doc.pop("_id", None)
        doc["submitted"] = doc["id"] in submitted_job_ids
        jobs.append(doc)
    return jobs

def get_job(job_id: str) -> dict[str, Any]:
    db = get_database()
    doc = db.jobs.find_one({"id": job_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Job not found")
    doc.pop("_id", None)
    return doc

def create_job(title: str, description: str, current_user: User) -> dict[str, Any]:
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_database()
    job_id = str(uuid.uuid4())
    job_doc = {
        "id": job_id,
        "title": title,
        "description": description,
        "created_at": _utcnow(),
    }
    db.jobs.insert_one(job_doc)
    return job_doc

def update_job(job_id: str, title: Optional[str], description: Optional[str], current_user: User) -> dict[str, Any]:
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_database()
    update_data = {}
    if title: update_data["title"] = title
    if description: update_data["description"] = description
    
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
    return res

def delete_job(job_id: str, current_user: User) -> bool:
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_database()
    res = db.jobs.delete_one({"id": job_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return True
