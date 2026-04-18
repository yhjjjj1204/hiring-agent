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
    overall_score: float,
    dimensions: list[dict[str, Any]],
    summary: str,
    scorecard: dict[str, Any],
    db: Database[Any] | None = None,
) -> None:
    d = db or get_database()
    d["candidate_rankings"].insert_one(
        {
            "ranking_id": ranking_id,
            "candidate_ref": candidate_ref,
            "thread_id": thread_id,
            "overall_score": overall_score,
            "dimensions": dimensions,
            "summary": summary,
            "scorecard_snapshot": scorecard,
            "created_at": _utcnow(),
        },
    )


def list_rankings(
    limit: int = 50,
    sort_by: str = "overall_score",
    db: Database[Any] | None = None,
) -> list[dict[str, Any]]:
    d = db or get_database()
    col = d["candidate_rankings"]
    sort_field = sort_by if sort_by in ("overall_score", "created_at") else "overall_score"
    direction = DESCENDING if sort_field == "overall_score" else DESCENDING
    cur = col.find({}, sort=[(sort_field, direction)]).limit(min(max(limit, 1), 200))
    out = []
    for doc in cur:
        doc.pop("_id", None)
        out.append(doc)
    return out
