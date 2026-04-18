"""Candidate ranking snapshots (MongoDB)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database

from db.mongo import get_database


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_candidate_ranking_indexes(db: Database[Any] | None = None) -> None:
    d = db or get_database()
    col: Collection[Any] = d["candidate_rankings"]
    col.create_index([("created_at", DESCENDING)], name="rank_created")
    col.create_index([("overall_score", DESCENDING)], name="rank_score")
    col.create_index([("candidate_ref", ASCENDING)], name="rank_candidate_ref")


def insert_candidate_ranking(
    *,
    ranking_id: str,
    candidate_ref: str,
    thread_id: str | None,
    job_id: str | None = None,
    candidate_info: dict[str, Any] | None = None,
    status: str = "evaluating",
    overall_score: float = 0.0,
    dimensions: list[dict[str, Any]] | None = None,
    summary: str = "",
    scorecard: dict[str, Any] | None = None,
    db: Database[Any] | None = None,
) -> None:
    d = db or get_database()
    d["candidate_rankings"].insert_one(
        {
            "ranking_id": ranking_id,
            "candidate_ref": candidate_ref,
            "candidate_info": candidate_info or {},
            "thread_id": thread_id,
            "job_id": job_id,
            "status": status,
            "overall_score": overall_score,
            "dimensions": dimensions or [],
            "summary": summary,
            "scorecard_snapshot": scorecard,
            "submitted_at": _utcnow(),
            "evaluated_at": None,
            "created_at": _utcnow(),
        },
    )


def update_candidate_ranking_result(
    ranking_id: str,
    *,
    status: str = "ready",
    overall_score: float,
    dimensions: list[dict[str, Any]],
    summary: str,
    scorecard: dict[str, Any],
    arranged_resume: dict[str, Any] | None = None,
    db: Database[Any] | None = None,
) -> None:
    d = db or get_database()
    d["candidate_rankings"].update_one(
        {"ranking_id": ranking_id},
        {
            "$set": {
                "status": status,
                "overall_score": overall_score,
                "dimensions": dimensions,
                "summary": summary,
                "scorecard_snapshot": scorecard,
                "arranged_resume": arranged_resume,
                "evaluated_at": _utcnow(),
            }
        },
    )


def list_rankings(
    limit: int = 50,
    sort_by: str = "overall_score",
    job_id: str | None = None,
    candidate_ref: str | None = None,
    db: Database[Any] | None = None,
) -> list[dict[str, Any]]:
    d = db or get_database()
    col = d["candidate_rankings"]
    query = {}
    if job_id:
        query["job_id"] = job_id
    if candidate_ref:
        query["candidate_ref"] = candidate_ref
    
    sort_field = sort_by if sort_by in ("overall_score", "submitted_at", "created_at") else "overall_score"
    # If sorting by score, we probably want descending, but submitted_at might be ascending or descending.
    # We'll stick to DESCENDING for both for now (newest/highest first).
    cur = col.find(query, sort=[(sort_field, DESCENDING)]).limit(min(max(limit, 1), 200))
    out = []
    for doc in cur:
        doc.pop("_id", None)
        out.append(doc)
    return out
