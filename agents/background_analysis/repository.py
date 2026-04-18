"""背景分析结果落库。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database

from hiring_agent.agents.background_analysis.models import BACKGROUND_SCHEMA_VERSION, BackgroundAnalysisResult
from hiring_agent.db.mongo import get_database


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_background_analysis_indexes(db: Database[Any] | None = None) -> None:
    d = db or get_database()
    col: Collection[Any] = d["background_analyses"]
    col.create_index([("analysis_id", ASCENDING)], unique=True, name="uniq_bg_analysis_id")
    col.create_index([("created_at", DESCENDING)], name="bg_created")


def insert_background_analysis(
    analysis_id: str,
    request_payload: dict[str, Any],
    result: BackgroundAnalysisResult,
    db: Database[Any] | None = None,
) -> None:
    d = db or get_database()
    now = _utcnow()
    d["background_analyses"].insert_one(
        {
            "analysis_id": analysis_id,
            "schema_version": BACKGROUND_SCHEMA_VERSION,
            "request": request_payload,
            "result": result.model_dump(mode="json"),
            "created_at": now,
        },
    )


def get_background_analysis(analysis_id: str, db: Database[Any] | None = None) -> dict[str, Any] | None:
    d = db or get_database()
    return d["background_analyses"].find_one({"analysis_id": analysis_id})
