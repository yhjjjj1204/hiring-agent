"""Writes ranking dashboard data from the pipeline's final state."""

from __future__ import annotations

import uuid
from typing import Any

from dashboard.repository import insert_candidate_ranking


def record_pipeline_ranking(thread_id: str, state: dict[str, Any]) -> str | None:
    """If a scorecard exists, writes to candidate_rankings. Returns ranking_id or None."""
    sc = state.get("scorecard")
    if not isinstance(sc, dict):
        return None
    overall = sc.get("overall_score")
    if overall is None:
        return None

    ref = (state.get("candidate_ref") or "").strip() or f"thread-{thread_id[:8]}"

    dims_raw = sc.get("dimensions") or []
    dimensions: list[dict[str, Any]] = []
    if isinstance(dims_raw, list):
        for d in dims_raw:
            if isinstance(d, dict) and "name" in d and "score" in d:
                dimensions.append(
                    {"name": d.get("name"), "score": float(d.get("score", 0)), "rationale": d.get("rationale", "")},
                )

    rid = str(uuid.uuid4())
    insert_candidate_ranking(
        ranking_id=rid,
        candidate_ref=ref,
        thread_id=thread_id,
        job_id=state.get("job_id"),
        overall_score=float(overall),
        dimensions=dimensions,
        summary=str(sc.get("summary") or ""),
        scorecard=sc,
    )
    return rid
