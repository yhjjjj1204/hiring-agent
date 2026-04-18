"""OCR (OpenAI GPT-4o) and resume structuring (Data Arrangement) API."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from hiring_agent import config
from hiring_agent.agents.data_arrangement.agent import arrange_resume_from_ocr_text
from hiring_agent.agents.data_arrangement.models import (
    ARRANGEMENT_SCHEMA_VERSION,
    RESUME_PROFILE_JSON_SCHEMA,
)
from hiring_agent.agents.data_arrangement.repository import (
    get_resume_ingest,
    insert_resume_ingest,
)
from hiring_agent.agents.ocr_agent import (
    extract_and_arrange_resume_from_path,
    extract_resume_text_from_path,
    is_allowed_upload_suffix,
)
from hiring_agent.monitoring.registry import get_monitor
from hiring_agent.fairness.injection_sanitize import sanitize_resume_text

router = APIRouter(prefix="/data", tags=["data"])


class OcrResponse(BaseModel):
    text: str
    char_count: int


class ArrangeRequest(BaseModel):
    ocr_text: str = Field(..., min_length=1, description="Raw OCR Markdown text")


class ArrangeResponse(BaseModel):
    arranged: dict[str, Any]
    ocr_truncated_for_llm: bool
    injection_sanitize_meta: dict[str, Any] | None = None


class IngestResponse(BaseModel):
    ingest_id: str
    arranged: dict[str, Any]
    ocr_char_count: int
    ocr_truncated_for_llm: bool
    injection_sanitize_meta: dict[str, Any] | None = None


_ALLOWED_EXT_HELP = ".pdf / .png / .jpg / .jpeg / .webp / .gif / .bmp / .tiff / .tif"


class SchemaBody(BaseModel):
    arrangement_schema_version: int
    resume_profile_json_schema: dict[str, Any]
    mongo_collection: dict[str, Any]


@router.post("/ocr", response_model=OcrResponse)
async def run_ocr(file: UploadFile = File(...)):
    """OCR only: upload PDF or image, return Markdown text (not persisted)."""
    raw_name = file.filename or "upload"
    suffix = Path(raw_name).suffix
    if not is_allowed_upload_suffix(suffix):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type {suffix or '(no extension)'}; allowed: {_ALLOWED_EXT_HELP}",
        )
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    try:
        try:
            text = await run_in_threadpool(extract_resume_text_from_path, tmp_path)
        except ValueError as e:
            raise HTTPException(status_code=503, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"OCR failed: {e!s}") from e
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return OcrResponse(text=text, char_count=len(text))


@router.post("/arrange", response_model=ArrangeResponse)
def run_arrange(body: ArrangeRequest):
    """Structure only: map OCR Markdown to JSON (not persisted)."""
    if not config.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not set")
    cid = str(uuid.uuid4())
    mon = get_monitor()
    mon.http_activity("data_arrange_api", correlation_id=cid, phase="start")
    ok = True
    err: str | None = None
    try:
        profile, truncated, inj = arrange_resume_from_ocr_text(body.ocr_text)
    except Exception as e:
        ok = False
        err = str(e)
        raise HTTPException(status_code=502, detail=f"Structuring failed: {e!s}") from e
    finally:
        mon.http_activity("data_arrange_api", correlation_id=cid, phase="end", ok=ok, error=err)
    return ArrangeResponse(
        arranged=profile.model_dump(mode="json"),
        ocr_truncated_for_llm=truncated,
        injection_sanitize_meta=inj,
    )


@router.post("/ingest", response_model=IngestResponse)
async def run_full_ingest(file: UploadFile = File(...)):
    """OCR + structuring, persisted to MongoDB collection `resume_ingests`."""
    if not config.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not set")

    raw_name = file.filename or "upload"
    suffix = Path(raw_name).suffix
    if not is_allowed_upload_suffix(suffix):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix or '(no extension)'}; allowed: {_ALLOWED_EXT_HELP}",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        try:
            extracted = await run_in_threadpool(extract_and_arrange_resume_from_path, tmp_path)
        except ValueError as e:
            raise HTTPException(status_code=503, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"OCR failed: {e!s}") from e

        safe_ocr, ocr_inj = sanitize_resume_text(extracted.ocr_text)
        arranged = extracted.arranged_profile

        ingest_id = str(uuid.uuid4())
        insert_resume_ingest(
            ingest_id=ingest_id,
            source_filename=raw_name,
            mime_type=file.content_type,
            ocr_text=safe_ocr,
            arranged=arranged,
            ocr_truncated_for_llm=False,
            injection_sanitize_meta={"ocr_pass": ocr_inj, "arrange_pass": {"mode": "gpt4o_single_pass"}},
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return IngestResponse(
        ingest_id=ingest_id,
        arranged=arranged.model_dump(mode="json"),
        ocr_char_count=len(safe_ocr),
        ocr_truncated_for_llm=False,
        injection_sanitize_meta={"ocr_pass": ocr_inj, "arrange_pass": {"mode": "gpt4o_single_pass"}},
    )


@router.get("/ingest/{ingest_id}")
def get_ingest(ingest_id: str, include_ocr: bool = True):
    doc = get_resume_ingest(ingest_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Ingest not found")
    out = {
        "ingest_id": doc["ingest_id"],
        "source_filename": doc.get("source_filename"),
        "mime_type": doc.get("mime_type"),
        "arranged_profile": doc.get("arranged_profile"),
        "arrangement_schema_version": doc.get("arrangement_schema_version"),
        "ocr_truncated_for_llm": doc.get("ocr_truncated_for_llm"),
        "injection_sanitize_meta": doc.get("injection_sanitize_meta"),
        "created_at": doc.get("created_at"),
    }
    if include_ocr:
        out["ocr_text"] = doc.get("ocr_text")
    return out


@router.get("/schema", response_model=SchemaBody)
def get_data_schema():
    return SchemaBody(
        arrangement_schema_version=ARRANGEMENT_SCHEMA_VERSION,
        resume_profile_json_schema=RESUME_PROFILE_JSON_SCHEMA,
        mongo_collection={
            "name": "resume_ingests",
            "fields": {
                "ingest_id": "str, unique",
                "source_filename": "str",
                "mime_type": "str | null",
                "ocr_text": "str, OCR after prompt-injection sanitize (stored)",
                "ocr_truncated_for_llm": "bool, whether input was truncated for LLM calls",
                "injection_sanitize_meta": "object | null, sanitizer statistics",
                "arranged_profile": "object, same shape as ResumeStructuredProfile",
                "arrangement_schema_version": "int",
                "arrangement_json_schema_snapshot": "object",
                "created_at": "datetime",
                "updated_at": "datetime",
            },
        },
    )
