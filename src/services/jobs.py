from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import HTTPException, BackgroundTasks
from api.auth_models import User
from db.mongo import get_database, generate_embedding, vector_search

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

from monitoring.token_callback import get_token_callback
from monitoring.context import set_execution_context

def _generate_job_summary(title: str, description: str, username: Optional[str] = None) -> str:
    """Generate a 2-3 sentence AI summary of the job description."""
    if not config.OPENAI_API_KEY:
        return ""
    
    # Only summarize if it's reasonably long
    if len(description) < 300:
        return ""

    if username:
        set_execution_context(username=username, function_id="job_summary")

    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=0, 
            api_key=config.OPENAI_API_KEY,
            callbacks=get_token_callback(username=username, function_id="job_summary"),
        )
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

from api.websockets import manager
import json

def _background_generate_summary(job_id: str, title: str, description: str, username: str):
    summary = _generate_job_summary(title, description, username)
    if summary:
        db = get_database()
        
        # Generate summary embedding (Title + Summary)
        summary_embedding = None
        try:
            summary_embedding = generate_embedding(f"{title}\n{summary}")
        except Exception as e:
            print(f"Failed to generate summary embedding for {job_id}: {e}")

        update_fields = {"summary": summary}
        if summary_embedding:
            update_fields["summary_embedding"] = summary_embedding
            
        db.jobs.update_one({"id": job_id}, {"$set": update_fields})
        
        # Notify via WebSocket
        import asyncio
        asyncio.run(manager.broadcast_to_topic(f"job:{job_id}", {
            "type": "job_update",
            "job_id": job_id,
            "summary": summary
        }))

def create_job(title: str, description: str, current_user: User, background_tasks: Optional[BackgroundTasks] = None) -> dict[str, Any]:
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_database()
    job_id = str(uuid.uuid4())
    
    # Generate description embedding (Title + Description)
    desc_embedding = None
    try:
        desc_embedding = generate_embedding(f"{title}\n{description}")
    except Exception as e:
        print(f"Failed to generate description embedding for {job_id}: {e}")

    summary = ""
    summary_embedding = None
    if len(description) >= 300:
        summary = "generating"
        if background_tasks:
            background_tasks.add_task(_background_generate_summary, job_id, title, description, current_user.username)
        else:
            # Fallback for when background_tasks is not provided (e.g. some internal calls)
            summary = _generate_job_summary(title, description, current_user.username)
            if summary:
                try:
                    summary_embedding = generate_embedding(f"{title}\n{summary}")
                except Exception as e:
                    print(f"Failed to generate summary embedding for {job_id}: {e}")
    
    job_doc = {
        "id": job_id,
        "title": title,
        "description": description,
        "summary": summary,
        "created_at": _utcnow(),
    }
    if desc_embedding:
        job_doc["desc_embedding"] = desc_embedding
    if summary_embedding:
        job_doc["summary_embedding"] = summary_embedding

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
    
    # Re-generate summary and embeddings if description or title changed
    if title or description:
        existing = db.jobs.find_one({"id": job_id})
        if existing:
            new_title = title or existing.get("title")
            new_desc = description or existing.get("description")
            
            # Re-generate description embedding
            try:
                update_data["desc_embedding"] = generate_embedding(f"{new_title}\n{new_desc}")
            except Exception as e:
                print(f"Failed to re-generate description embedding for {job_id}: {e}")

            if len(new_desc) >= 300:
                update_data["summary"] = "generating"
                if background_tasks:
                    background_tasks.add_task(_background_generate_summary, job_id, new_title, new_desc, current_user.username)
                else:
                    summary = _generate_job_summary(new_title, new_desc, current_user.username)
                    update_data["summary"] = summary
                    if summary:
                        try:
                            update_data["summary_embedding"] = generate_embedding(f"{new_title}\n{summary}")
                        except Exception as e:
                            print(f"Failed to re-generate summary embedding for {job_id}: {e}")
            else:
                update_data["summary"] = ""
                update_data["summary_embedding"] = None

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

def search_jobs(query: str, current_user: Optional[User] = None, limit: int = 5) -> List[dict[str, Any]]:
    if not query.strip():
        return []

    try:
        query_embedding = generate_embedding(query)
    except Exception as e:
        print(f"Failed to generate query embedding for search: {e}")
        return []

    # Search in both description and summary embeddings
    desc_results = vector_search("jobs", query_embedding, "desc_embedding", k=limit)
    summary_results = vector_search("jobs", query_embedding, "summary_embedding", k=limit)

    # Merge results by ID
    merged = {}
    
    # We'll use a simple "best score" merge for now
    # FerretDB returns documents. If there's a similarity score, it's usually in a special field
    # but currently we just get the documents.
    for doc in desc_results + summary_results:
        jid = doc.get("id")
        if jid not in merged:
            doc.pop("_id", None)
            merged[jid] = doc

    # Check submission status if user provided
    if current_user:
        db = get_database()
        submissions = db.candidate_rankings.find({"candidate_ref": current_user.username}, {"job_id": 1})
        submitted_job_ids = {s.get("job_id") for s in submissions if s.get("job_id")}
        for job in merged.values():
            job["submitted"] = job["id"] in submitted_job_ids

    return list(merged.values())[:limit]
