"""Stateful LangGraph hiring pipeline API (includes HITL resume)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from langgraph.types import Command
from pydantic import BaseModel, Field

from hiring_agent.dashboard.ranking_service import record_pipeline_ranking
from hiring_agent.graph.pipeline import (
    build_hiring_pipeline_graph,
    extract_interrupts,
    pipeline_config,
)
from hiring_agent.monitoring.pipeline_hooks import mark_pipeline_run_terminal
from hiring_agent.monitoring.registry import get_monitor

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class PipelineInvokeBody(BaseModel):
    """State patch for first or continued runs; use with `resume` when continuing."""

    job_spec: dict[str, Any] | None = None
    hr_requirement_text: str | None = None
    resume_path: str | None = None
    resume_ocr_text: str | None = None
    candidate_github: str | None = None
    google_scholar_url: str | None = None
    candidate_name_override: str | None = None
    candidate_ref: str | None = Field(
        default=None,
        description="Candidate reference for dashboards (anonymous code or business ID); defaults to thread prefix.",
    )


class PipelineInvokeRequest(BaseModel):
    """Run the main workflow."""

    thread_id: str | None = Field(
        default=None,
        description="Stateful thread ID; omit on first call (server generates). Required when resuming HITL.",
    )
    input: PipelineInvokeBody = Field(default_factory=PipelineInvokeBody)
    resume: Any | None = Field(
        default=None,
        description="Human-in-the-loop payload: object or string matching interrupt instructions.",
    )


@router.post("/invoke")
def pipeline_invoke(req: PipelineInvokeRequest):
    if req.resume is not None and not req.thread_id:
        raise HTTPException(status_code=400, detail="thread_id is required when using resume for HITL")

    tid = req.thread_id or str(uuid.uuid4())
    cfg = pipeline_config(tid)
    g = build_hiring_pipeline_graph()
    mon = get_monitor()
    meta = {k: v for k, v in req.input.model_dump().items() if v is not None and k in ("candidate_ref",)}
    mon.start_run(tid, "pipeline", meta=meta)

    if req.resume is not None:
        payload = Command(resume=req.resume, update=req.input.model_dump(exclude_none=True))
        out = g.invoke(payload, cfg)
    else:
        init = {k: v for k, v in req.input.model_dump().items() if v is not None}
        if not init.get("job_spec") and not (init.get("hr_requirement_text") or "").strip():
            raise HTTPException(status_code=400, detail="First call requires job_spec or hr_requirement_text")
        if not init.get("resume_ocr_text") and not init.get("resume_path"):
            raise HTTPException(status_code=400, detail="First call requires resume_ocr_text or resume_path")
        out = g.invoke(init, cfg)

    if not isinstance(out, dict):
        raise HTTPException(status_code=500, detail="Unexpected graph output shape")

    interrupts = extract_interrupts(out)
    done = not interrupts and out.get("pipeline_status") == "completed"
    failed = out.get("pipeline_status") == "failed"

    ranking_id = None
    if done and isinstance(out, dict) and out.get("scorecard"):
        ranking_id = record_pipeline_ranking(tid, out)

    if interrupts:
        mark_pipeline_run_terminal(tid, "interrupted")
    elif failed:
        mark_pipeline_run_terminal(tid, "failed")
    elif done:
        mark_pipeline_run_terminal(tid, "completed")
    else:
        mark_pipeline_run_terminal(tid, "interrupted")

    return {
        "thread_id": tid,
        "interrupts": interrupts,
        "completed": done,
        "failed": failed,
        "last_error": out.get("last_error"),
        "ranking_id": ranking_id,
        "state": {k: v for k, v in out.items() if not str(k).startswith("__")},
    }


@router.get("/thread/{thread_id}/state")
def pipeline_get_state(thread_id: str):
    """Read latest checkpoint state (debug)."""
    g = build_hiring_pipeline_graph()
    snap = g.get_state(pipeline_config(thread_id))
    if snap is None or snap.values is None:
        raise HTTPException(status_code=404, detail="Unknown thread_id or no state yet")
    v = dict(snap.values) if isinstance(snap.values, dict) else {}
    return {"thread_id": thread_id, "state": {k: x for k, x in v.items() if not str(k).startswith("__")}}
