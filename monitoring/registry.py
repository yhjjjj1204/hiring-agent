"""Agent 运行状态与路径的进程内注册表（供 Monitor API / SSE 使用）。"""

from __future__ import annotations

import threading
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

StepStatus = Literal["running", "completed", "failed", "interrupted"]


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StepRecord:
    agent_id: str
    status: StepStatus
    started_at: str
    ended_at: str | None = None
    error: str | None = None
    context: str = "pipeline"  # pipeline | http


@dataclass
class RunRecord:
    thread_id: str
    context: str
    status: Literal["running", "completed", "failed", "interrupted"] = "running"
    path: list[StepRecord] = field(default_factory=list)
    current_agent_id: str | None = None
    started_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)
    meta: dict[str, Any] = field(default_factory=dict)


# 前端展示用的 Worker 目录（与 pipeline 节点 / HTTP 入口对齐）
WORKER_AGENTS: list[dict[str, str]] = [
    {"id": "hr_ingest", "label": "HR requirement structuring", "group": "intake"},
    {"id": "resume_ocr", "label": "Resume OCR", "group": "data"},
    {"id": "resume_arrange", "label": "Resume structuring", "group": "data"},
    {"id": "background_analysis", "label": "Background analysis", "group": "verify"},
    {"id": "fairness_blinding", "label": "Fairness blinding", "group": "fairness"},
    {"id": "auto_score", "label": "Auto scoring", "group": "decision"},
    {"id": "hr_strategy_chat", "label": "HR Strategy chat", "group": "intake"},
    {"id": "data_ocr_api", "label": "OCR API", "group": "data"},
    {"id": "data_arrange_api", "label": "Resume arrange API", "group": "data"},
    {"id": "background_analyze_api", "label": "Background analyze API", "group": "verify"},
]


class AgentMonitorRegistry:
    """线程安全；最近 N 条运行记录环形缓冲。"""

    def __init__(self, max_runs: int = 200) -> None:
        self._lock = threading.RLock()
        self._runs: dict[str, RunRecord] = {}
        self._order: deque[str] = deque(maxlen=max_runs)
        self._http_spikes: dict[str, dict[str, Any]] = {}  # correlation_id -> last activity

    def start_run(self, thread_id: str, context: str = "pipeline", meta: dict[str, Any] | None = None) -> None:
        """在 HTTP 层首次启动流水线时调用；resume 同一 thread 时只合并 meta。"""
        with self._lock:
            if thread_id in self._runs:
                self._runs[thread_id].meta.update(meta or {})
                self._runs[thread_id].updated_at = _utcnow()
                return
            rec = RunRecord(thread_id=thread_id, context=context, meta=meta or {})
            self._runs[thread_id] = rec
            self._order.append(thread_id)

    def begin_step(self, thread_id: str, agent_id: str, ctx: str = "pipeline") -> None:
        with self._lock:
            run = self._runs.setdefault(thread_id, RunRecord(thread_id=thread_id, context=ctx))
            run.current_agent_id = agent_id
            run.status = "running"
            run.updated_at = _utcnow()
            run.path.append(
                StepRecord(
                    agent_id=agent_id,
                    status="running",
                    started_at=run.updated_at,
                    context=ctx,
                ),
            )

    def end_step(
        self,
        thread_id: str,
        agent_id: str,
        *,
        ok: bool,
        error: str | None = None,
        interrupted: bool = False,
    ) -> None:
        with self._lock:
            run = self._runs.get(thread_id)
            if not run or not run.path:
                return
            last = run.path[-1]
            if last.agent_id != agent_id:
                return
            last.ended_at = _utcnow()
            last.error = error
            if interrupted:
                last.status = "interrupted"
            else:
                last.status = "completed" if ok else "failed"
            run.updated_at = last.ended_at
            run.current_agent_id = None

    def finish_run(
        self,
        thread_id: str,
        *,
        status: Literal["completed", "failed", "interrupted"] = "completed",
    ) -> None:
        with self._lock:
            run = self._runs.get(thread_id)
            if not run:
                return
            run.status = status
            run.current_agent_id = None
            run.updated_at = _utcnow()

    def http_activity(
        self,
        agent_id: str,
        *,
        correlation_id: str | None = None,
        phase: Literal["start", "end"] = "start",
        ok: bool = True,
        error: str | None = None,
    ) -> str:
        """记录非 pipeline 的 HTTP 级 Worker 调用；返回 correlation_id。"""
        cid = correlation_id or str(uuid.uuid4())
        now = _utcnow()
        with self._lock:
            if phase == "start":
                self._http_spikes[cid] = {
                    "agent_id": agent_id,
                    "status": "running",
                    "started_at": now,
                }
            else:
                spike = self._http_spikes.get(cid, {})
                spike["status"] = "completed" if ok else "failed"
                spike["ended_at"] = now
                spike["error"] = error
                self._http_spikes[cid] = spike
            while len(self._http_spikes) > 120:
                oldest = next(iter(self._http_spikes), None)
                if oldest is None:
                    break
                self._http_spikes.pop(oldest, None)
        return cid

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            runs_out = []
            for tid in reversed(self._order):
                r = self._runs.get(tid)
                if not r:
                    continue
                runs_out.append(self._serialize_run(r))
            agents_status = self._aggregate_agent_status()
            http_recent = list(self._http_spikes.values())[-30:]
            return {
                "generated_at": _utcnow(),
                "agents_catalog": WORKER_AGENTS,
                "agents_runtime": agents_status,
                "runs": runs_out,
                "http_recent": http_recent,
            }

    def get_run(self, thread_id: str) -> dict[str, Any] | None:
        with self._lock:
            r = self._runs.get(thread_id)
            if not r:
                return None
            return self._serialize_run(r)

    def _serialize_run(self, r: RunRecord) -> dict[str, Any]:
        return {
            "thread_id": r.thread_id,
            "context": r.context,
            "status": r.status,
            "current_agent_id": r.current_agent_id,
            "started_at": r.started_at,
            "updated_at": r.updated_at,
            "meta": r.meta,
            "path": [
                {
                    "agent_id": s.agent_id,
                    "status": s.status,
                    "started_at": s.started_at,
                    "ended_at": s.ended_at,
                    "error": s.error,
                    "context": s.context,
                }
                for s in r.path
            ],
        }

    def _aggregate_agent_status(self) -> list[dict[str, Any]]:
        """每个 catalog agent：是否有运行中 / 最近一条路径节点状态。"""
        by_id: dict[str, dict[str, Any]] = {a["id"]: {"id": a["id"], "active": False, "last_step": None} for a in WORKER_AGENTS}
        for tid in self._order:
            r = self._runs.get(tid)
            if not r:
                continue
            if r.current_agent_id and r.current_agent_id in by_id:
                by_id[r.current_agent_id]["active"] = True
            for s in r.path:
                if s.agent_id in by_id:
                    by_id[s.agent_id]["last_step"] = {"thread_id": tid, "status": s.status, "ended_at": s.ended_at}
        return list(by_id.values())


_registry = AgentMonitorRegistry()


def get_monitor() -> AgentMonitorRegistry:
    return _registry
