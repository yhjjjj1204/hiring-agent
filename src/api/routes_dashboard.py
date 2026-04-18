"""Dashboard: candidate rankings."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from dashboard.repository import list_rankings

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/rankings")
def get_rankings(
    limit: int = Query(30, ge=1, le=200),
    sort: str = Query("overall_score", description="overall_score | created_at"),
):
    """Candidate ranking list (default sort: overall_score descending)."""
    rows = list_rankings(limit=limit, sort_by=sort)
    return {"count": len(rows), "sort": sort, "items": rows}


@router.get("/rankings/matrix")
def get_rankings_matrix(limit: int = Query(30, ge=1, le=100)):
    """
    Per-candidate dimension score matrix for heatmaps or radar charts.
    Rows: candidate_ref; columns: dimension name -> score.
    """
    rows = list_rankings(limit=limit, sort_by="overall_score")
    dim_names: list[str] = []
    for r in rows:
        for d in r.get("dimensions") or []:
            if isinstance(d, dict) and d.get("name"):
                n = str(d["name"])
                if n not in dim_names:
                    dim_names.append(n)

    matrix: list[dict[str, Any]] = []
    for r in rows:
        vec: dict[str, float] = {n: 0.0 for n in dim_names}
        for d in r.get("dimensions") or []:
            if isinstance(d, dict) and d.get("name") in vec:
                try:
                    vec[str(d["name"])] = float(d.get("score", 0))
                except (TypeError, ValueError):
                    pass
        matrix.append(
            {
                "candidate_ref": r.get("candidate_ref"),
                "ranking_id": r.get("ranking_id"),
                "overall_score": r.get("overall_score"),
                "thread_id": r.get("thread_id"),
                "dimensions": vec,
                "summary": r.get("summary"),
                "created_at": (
                    r["created_at"].isoformat()
                    if hasattr(r.get("created_at"), "isoformat")
                    else r.get("created_at")
                ),
            },
        )

    return {"dimension_names": dim_names, "rows": matrix}
