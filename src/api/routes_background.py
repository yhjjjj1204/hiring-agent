"""Background Analysis Agent API."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from monitoring.registry import get_monitor
from agents.background_analysis.agent import run_background_analysis
from agents.background_analysis.repository import (
    get_background_analysis,
    insert_background_analysis,
)


router = APIRouter(prefix="/background", tags=["background"])


class AnalyzeRequest(BaseModel):
    candidate_name: str | None = Field(default=None, description="Candidate name for academic name search")
    github_url_or_username: str | None = Field(
        default=None,
        description="GitHub username or profile URL like https://github.com/{login}",
    )
    google_scholar_url: str | None = Field(
        default=None,
        description="Google Scholar profile URL (reference node only; metrics from OpenAlex/S2)",
    )
    persist: bool = Field(default=True, description="Whether to persist to MongoDB collection background_analyses")


class AnalyzeResponse(BaseModel):
    analysis_id: str | None = None
    persisted: bool = False
    result: dict[str, Any]


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    if not req.candidate_name and not req.github_url_or_username and not req.google_scholar_url:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one of candidate_name, github_url_or_username, google_scholar_url",
        )

    cid = str(uuid.uuid4())
    mon = get_monitor()
    mon.http_activity("background_analyze_api", correlation_id=cid, phase="start")
    ok = True
    err: str | None = None
    try:
        result = run_background_analysis(
            candidate_name=req.candidate_name,
            github_url_or_username=req.github_url_or_username,
            google_scholar_url=req.google_scholar_url,
        )

        aid: str | None = None
        if req.persist:
            aid = str(uuid.uuid4())
            insert_background_analysis(
                aid,
                request_payload=req.model_dump(),
                result=result,
            )

        return AnalyzeResponse(
            analysis_id=aid,
            persisted=req.persist,
            result=result.model_dump(mode="json"),
        )
    except Exception as e:
        ok = False
        err = str(e)
        raise
    finally:
        mon.http_activity("background_analyze_api", correlation_id=cid, phase="end", ok=ok, error=err)


@router.get("/analyze/{analysis_id}")
def get_analysis(analysis_id: str):
    doc = get_background_analysis(analysis_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Analysis record not found")
    return {"analysis_id": doc["analysis_id"], "request": doc.get("request"), "result": doc.get("result"), "created_at": doc.get("created_at")}
