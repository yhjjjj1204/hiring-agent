from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import HTTPException, BackgroundTasks
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

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import config

def _generate_job_summary(title: str, description: str) -> str:
    """Generate a 2-3 sentence AI summary of the job description."""
    if not config.OPENAI_API_KEY:
        return ""
    
    # Only summarize if it's reasonably long
    if len(description) < 300:
        return ""

    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=config.OPENAI_API_KEY)
        msg = HumanMessage(
            content=f"Title: {title}\nDescription: {description}\n\nProvide a concise 2-sentence summary of this job role and its key requirements."
        )
        res = llm.invoke([
            SystemMessage(content="You are an expert HR assistant. Provide extremely concise summaries."),
            msg
        ])
        return str(res.content).strip()
    except Exception as e:
        print(f"Failed to generate job summary: {e}")
        return ""

def _background_generate_summary(job_id: str, title: str, description: str):
    summary = _generate_job_summary(title, description)
    if summary:
        db = get_database()
        db.jobs.update_one({"id": job_id}, {"$set": {"summary": summary}})

def create_job(title: str, description: str, current_user: User, background_tasks: Optional[BackgroundTasks] = None) -> dict[str, Any]:
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_database()
    job_id = str(uuid.uuid4())
    
    summary = ""
    if len(description) >= 300:
        summary = "generating"
        if background_tasks:
            background_tasks.add_task(_background_generate_summary, job_id, title, description)
        else:
            # Fallback for when background_tasks is not provided (e.g. some internal calls)
            summary = _generate_job_summary(title, description)
    
    job_doc = {
        "id": job_id,
        "title": title,
        "description": description,
        "summary": summary,
        "created_at": _utcnow(),
    }
    db.jobs.insert_one(job_doc)
    job_doc.pop("_id", None)
    return job_doc

def update_job(job_id: str, title: Optional[str], description: Optional[str], current_user: User, background_tasks: Optional[BackgroundTasks] = None) -> dict[str, Any]:
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_database()
    update_data = {}
    if title: update_data["title"] = title
    if description: update_data["description"] = description
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Re-generate summary if description or title changed
    if title or description:
        existing = db.jobs.find_one({"id": job_id})
        if existing:
            new_title = title or existing.get("title")
            new_desc = description or existing.get("description")
            if len(new_desc) >= 300:
                update_data["summary"] = "generating"
                if background_tasks:
                    background_tasks.add_task(_background_generate_summary, job_id, new_title, new_desc)
                else:
                    update_data["summary"] = _generate_job_summary(new_title, new_desc)
            else:
                update_data["summary"] = ""

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
