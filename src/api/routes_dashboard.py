"""Dashboard: candidate rankings."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Depends, HTTPException
from api.deps import require_role, get_current_user
from api.auth_models import User
from services.rankings import list_candidate_rankings

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/rankings")
def get_rankings(
    limit: int = Query(30, ge=1, le=200),
    sort: str = Query("overall_score", description="overall_score | submitted_at"),
    job_id: str | None = Query(None),
    current_user: User = Depends(require_role("recruiter")),
):
    """Candidate ranking list."""
    rows = list_candidate_rankings(current_user, job_id=job_id, limit=limit, sort_by=sort)
    return {"count": len(rows), "sort": sort, "items": rows}


@router.get("/ranking/{ranking_id}")
def get_ranking(
    ranking_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a single ranking by its ID. Recruiters can see all, candidates only their own."""
    from db.mongo import get_database
    db = get_database()
    doc = db.candidate_rankings.find_one({"ranking_id": ranking_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Ranking not found")
    
    # Permission check: if candidate, must be their own
    if current_user.role == "candidate" and doc["candidate_ref"] != current_user.username:
        raise HTTPException(status_code=403, detail="Access denied to this ranking")
        
    doc.pop("_id", None)
    return doc


@router.get("/rankings/matrix")
def get_rankings_matrix(
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(require_role("recruiter")),
):
    """Optional pivot matrix of candidates x dimensions."""
    rows = list_candidate_rankings(current_user, limit=limit)
    if not rows:
        return {"dimension_names": [], "rows": []}

    dim_names = sorted({d["name"] for r in rows for d in r.get("dimensions", [])})

    matrix = []
    for r in rows:
        d_map = {d["name"]: d["score"] for d in r.get("dimensions", [])}
        matrix.append(
            {
                "candidate_ref": r["candidate_ref"],
                "overall_score": r["overall_score"],
                "scores": [d_map.get(name) for name in dim_names],
                "submitted_at": (
                    r["submitted_at"].isoformat()
                    if hasattr(r.get("submitted_at"), "isoformat")
                    else r.get("submitted_at")
                ),
            },
        )

    return {"dimension_names": dim_names, "rows": matrix}
