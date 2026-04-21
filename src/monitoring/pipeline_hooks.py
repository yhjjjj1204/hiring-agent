"""LangGraph node wrapper: Reports step start/end to AgentMonitorRegistry."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from monitoring.context import current_username, current_function_id
from monitoring.registry import get_monitor

try:
    from langgraph.config import get_config
except ImportError:
    get_config = None  # type: ignore[misc, assignment]

S = TypeVar("S", bound=dict[str, Any])


def _thread_id() -> str:
    if get_config is None:
        return "no-graph-context"
    try:
        cfg = get_config()
        tid = (cfg.get("configurable") or {}).get("thread_id")
        return str(tid) if tid else "unknown-thread"
    except Exception:
        return "unknown-thread"


def monitored_node(agent_id: str, fn: Callable[[S], dict[str, Any]]) -> Callable[[S], dict[str, Any]]:
    """Wraps a pipeline node function to record the execution path."""

    def wrapped(state: S) -> dict[str, Any]:
        mon = get_monitor()
        tid = _thread_id()
        mon.begin_step(tid, agent_id, "pipeline")

        # SET CONTEXT FOR LLM CALLBACKS
        run = mon.get_run_record(tid)
        username = run.meta.get("username") if run else None

        token_u = current_username.set(username)
        token_f = current_function_id.set(agent_id)

        ok = True
        err: str | None = None
        intr = False
        try:
            return fn(state)
        except BaseException as e:
            ok = False
            err = type(e).__name__
            intr = "Interrupt" in err
            raise
        finally:
            current_username.reset(token_u)
            current_function_id.reset(token_f)
            mon.end_step(
                tid,
                agent_id,
                ok=ok,
                error=err,
                interrupted=intr,
            )

    return wrapped


def mark_pipeline_run_terminal(thread_id: str, status: str) -> None:
    """Marks the final state of the entire pipeline from outside the graph (e.g., HTTP layer)."""
    st: Any = status
    if st not in ("completed", "failed", "interrupted"):
        st = "completed"
    get_monitor().finish_run(thread_id, status=st)
