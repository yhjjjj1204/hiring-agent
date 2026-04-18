"""简历 OCR + 结构化结果在 MongoDB 中的存储。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database

from hiring_agent.agents.data_arrangement.models import (
    ARRANGEMENT_SCHEMA_VERSION,
    RESUME_PROFILE_JSON_SCHEMA,
    ResumeStructuredProfile,
)
from hiring_agent.db.mongo import get_database


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_resume_ingest_indexes(db: Database[Any] | None = None) -> None:
    d = db or get_database()
    col: Collection[Any] = d["resume_ingests"]
    col.create_index([("ingest_id", ASCENDING)], unique=True, name="uniq_ingest_id")
    col.create_index([("created_at", DESCENDING)], name="ingest_created")


def insert_resume_ingest(
    ingest_id: str,
    source_filename: str,
    mime_type: str | None,
    ocr_text: str,
    arranged: ResumeStructuredProfile,
    ocr_truncated_for_llm: bool,
    injection_sanitize_meta: dict[str, Any] | None = None,
    db: Database[Any] | None = None,
) -> None:
    d = db or get_database()
    now = _utcnow()
    doc: dict[str, Any] = {
        "ingest_id": ingest_id,
        "source_filename": source_filename,
        "mime_type": mime_type,
        "ocr_text": ocr_text,
        "ocr_truncated_for_llm": ocr_truncated_for_llm,
        "arranged_profile": arranged.model_dump(mode="json"),
        "arrangement_schema_version": ARRANGEMENT_SCHEMA_VERSION,
        "arrangement_json_schema_snapshot": RESUME_PROFILE_JSON_SCHEMA,
        "created_at": now,
        "updated_at": now,
    }
    if injection_sanitize_meta:
        doc["injection_sanitize_meta"] = injection_sanitize_meta
    d["resume_ingests"].insert_one(doc)


def get_resume_ingest(ingest_id: str, db: Database[Any] | None = None) -> dict[str, Any] | None:
    d = db or get_database()
    return d["resume_ingests"].find_one({"ingest_id": ingest_id})
