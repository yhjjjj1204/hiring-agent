from __future__ import annotations

import os
import shutil
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, BackgroundTasks, UploadFile

from api.auth_models import User
from db.mongo import get_database
from agents.ocr_agent import is_allowed_upload_suffix
from dashboard.repository import insert_candidate_ranking

logger = logging.getLogger(__name__)

_UPLOAD_DIR = Path("uploads/resumes")
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
_ALLOWED_EXT_HELP = ".pdf / .png / .jpg / .jpeg / .webp / .gif / .bmp / .tiff / .tif"

async def submit_resume_for_analysis(
    background_tasks: BackgroundTasks,
    resume: UploadFile,
    job_id: str,
    current_user: User,
    candidate_github: Optional[str] = None,
    google_scholar_url: Optional[str] = None,
    candidate_name_override: Optional[str] = None,
) -> dict[str, Any]:
    db = get_database()
    
    # 1. Resolve job requirements
    job = db.jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    hr_requirement_text = job.get("description")

    # 2. Validate file type
    raw_name = resume.filename or "upload"
    suffix = Path(raw_name).suffix
    if not is_allowed_upload_suffix(suffix):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type {suffix or '(no extension)'}; allowed: {_ALLOWED_EXT_HELP}",
        )

    # 3. Check for existing submission
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
                "summary": "AI agents are re-evaluating your resume...",
                "scorecard_snapshot": None,
                "arranged_resume": None,
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

    # 4. Save resume file
    dest_path = _UPLOAD_DIR / f"{ranking_id}{suffix}"
    with dest_path.open("wb") as buffer:
        shutil.copyfileobj(resume.file, buffer)

    # 5. Start background task (import here to avoid circularity)
    from api.routes_analyze import _background_evaluate_resume
    background_tasks.add_task(
        _background_evaluate_resume,
        ranking_id=ranking_id,
        resume_path=dest_path,
        hr_requirement_text=hr_requirement_text,
        job_spec_json=None,
        candidate_github=candidate_github,
        google_scholar_url=google_scholar_url,
        candidate_name_override=candidate_name_override,
    )

    return {"ranking_id": ranking_id, "status": "evaluating"}
