"""HR Strategy 相关 MongoDB 访问与索引。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database

from hiring_agent.agents.hr_strategy.models import (
    HRJobSpec,
    HR_STRATEGY_JSON_SCHEMA,
    SPEC_SCHEMA_VERSION,
)
from hiring_agent.db.mongo import get_database


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_hr_strategy_indexes(db: Database[Any] | None = None) -> None:
    """创建 HR Strategy 相关集合索引（幂等）。"""
    d = db or get_database()
    sessions: Collection[Any] = d["hr_strategy_sessions"]
    specs: Collection[Any] = d["hr_job_specs"]

    sessions.create_index([("session_id", ASCENDING)], unique=True, name="uniq_session_id")
    sessions.create_index([("updated_at", DESCENDING)], name="session_updated")

    specs.create_index([("session_id", ASCENDING), ("created_at", DESCENDING)], name="spec_by_session_time")
    specs.create_index([("session_id", ASCENDING)], name="spec_by_session")


def create_session(session_id: str, db: Database[Any] | None = None) -> dict[str, Any]:
    d = db or get_database()
    now = _utcnow()
    doc = {
        "session_id": session_id,
        "status": "collecting",
        "messages": [],
        "created_at": now,
        "updated_at": now,
    }
    d["hr_strategy_sessions"].insert_one(doc)
    return doc


def get_session(session_id: str, db: Database[Any] | None = None) -> dict[str, Any] | None:
    d = db or get_database()
    return d["hr_strategy_sessions"].find_one({"session_id": session_id})


def replace_session_messages(
    session_id: str,
    messages: list[dict[str, Any]],
    status: str,
    db: Database[Any] | None = None,
) -> None:
    d = db or get_database()
    d["hr_strategy_sessions"].update_one(
        {"session_id": session_id},
        {
            "$set": {
                "messages": messages,
                "status": status,
                "updated_at": _utcnow(),
            }
        },
    )


def insert_job_spec(session_id: str, spec: HRJobSpec, db: Database[Any] | None = None) -> None:
    d = db or get_database()
    d["hr_job_specs"].insert_one(
        {
            "session_id": session_id,
            "schema_version": SPEC_SCHEMA_VERSION,
            "spec": spec.model_dump(mode="json"),
            "json_schema_snapshot": HR_STRATEGY_JSON_SCHEMA,
            "created_at": _utcnow(),
        },
    )


def get_latest_job_spec(session_id: str, db: Database[Any] | None = None) -> dict[str, Any] | None:
    d = db or get_database()
    return d["hr_job_specs"].find_one(
        {"session_id": session_id},
        sort=[("created_at", DESCENDING)],
    )
