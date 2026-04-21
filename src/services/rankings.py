from __future__ import annotations

import os
from pathlib import Path
from typing import Any, List, Optional

from fastapi import HTTPException, BackgroundTasks
from api.auth_models import User
from db.mongo import get_database
from dashboard.repository import list_rankings as list_rankings_repo
import config

_UPLOAD_DIR = Path(config.UPLOADS_DIR) / "resumes"

def list_candidate_rankings(
    current_user: User,
    job_id: Optional[str] = None,
    limit: int = 50,
    sort_by: str = "overall_score"
) -> List[dict[str, Any]]:
    # Permission hardening: Candidates can only see their own rankings
    candidate_ref = None
    if current_user.role == "candidate":
        candidate_ref = current_user.username
    
    return list_rankings_repo(limit=limit, sort_by=sort_by, job_id=job_id, candidate_ref=candidate_ref)

def get_my_submission(job_id: str, current_user: User) -> dict[str, Any]:
    if current_user.role != "candidate":
        raise HTTPException(status_code=403, detail="Only candidates can fetch their own submission")
    
    db = get_database()
    ranking = db.candidate_rankings.find_one({"candidate_ref": current_user.username, "job_id": job_id})
    if not ranking:
        raise HTTPException(status_code=404, detail="No submission found")
    ranking.pop("_id", None)
    return ranking

async def trigger_re_evaluation(
    ranking_id: str,
    current_user: User,
    background_tasks: BackgroundTasks
) -> dict[str, Any]:
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Import here to avoid circular imports
    from api.routes_analyze import _background_evaluate_resume
    
    db = get_database()
    ranking = db.candidate_rankings.find_one({"ranking_id": ranking_id})
    if not ranking:
        raise HTTPException(status_code=404, detail="Ranking not found")
    
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
        username=current_user.username,
    )

    return {"status": "evaluating"}

async def trigger_re_evaluation_all(
    job_id: str,
    current_user: User,
    background_tasks: BackgroundTasks
) -> dict[str, Any]:
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    from api.routes_analyze import _background_evaluate_resume
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
        if not files: continue
        
        db.candidate_rankings.update_one({"ranking_id": ranking_id}, {"$set": {"status": "evaluating"}})
        
        cinfo = r.get("candidate_info") or {}
        background_tasks.add_task(
            _background_evaluate_resume,
            ranking_id=ranking_id,
            resume_path=files[0],
            hr_requirement_text=hr_requirement_text,
            job_spec_json=None,
            candidate_github=cinfo.get("github"),
            google_scholar_url=google_scholar_url,
            candidate_name_override=cinfo.get("name_override"),
            username=current_user.username,
        )
        count += 1
        
    return {"status": "evaluating", "count": count}
