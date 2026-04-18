"""从流水线终态写入排名看板数据。"""

from __future__ import annotations

import uuid
from typing import Any

from hiring_agent.dashboard.repository import insert_candidate_ranking


def record_pipeline_ranking(thread_id: str, state: dict[str, Any]) -> str | None:
    """若存在 scorecard，则写入 candidate_rankings。返回 ranking_id 或 None。"""
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
        overall_score=float(overall),
        dimensions=dimensions,
        summary=str(sc.get("summary") or ""),
        scorecard=sc,
    )
    return rid
