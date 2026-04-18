"""Agent monitor: worker status, run paths, SSE stream."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException, Query
from starlette.responses import StreamingResponse

from monitoring.registry import WORKER_AGENTS, get_monitor

router = APIRouter(prefix="/monitor", tags=["monitor"])


@router.get("/agents")
def list_agents_catalog():
    """Worker catalog plus runtime aggregate status."""
    snap = get_monitor().snapshot()
    return {
        "catalog": WORKER_AGENTS,
        "agents_runtime": snap["agents_runtime"],
        "active_runs": [r for r in snap["runs"] if r.get("status") == "running"][:20],
    }


@router.get("/runs")
def list_runs(limit: int = Query(30, ge=1, le=100)):
    """Recent pipeline runs (with path)."""
    snap = get_monitor().snapshot()
    return {"runs": snap["runs"][:limit], "http_recent": snap.get("http_recent", [])}


@router.get("/runs/{thread_id}")
def get_run_detail(thread_id: str):
    doc = get_monitor().get_run(thread_id)
    if not doc:
        raise HTTPException(status_code=404, detail="No run record for this thread_id")
    return doc


@router.get("/stream")
async def monitor_stream(poll_interval: float = Query(1.0, ge=0.3, le=5.0)):
    """
    Server-Sent Events: push full snapshots on an interval for live dashboards.
    Example client: `new EventSource('/monitor/stream?poll_interval=1')`
    """

    async def event_gen():
        mon = get_monitor()
        while True:
            payload = mon.snapshot()
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            await asyncio.sleep(poll_interval)

    return StreamingResponse(event_gen(), media_type="text/event-stream")
