"""轻量占位图。完整招聘流水线见 `hiring_agent.graph.pipeline`（`build_hiring_pipeline_graph`）。"""

from typing import TypedDict

from langgraph.graph import END, StateGraph


class GraphState(TypedDict, total=False):
    """跨节点共享的状态；按业务字段逐步扩展。"""

    messages: list[str]


def _noop(state: GraphState) -> GraphState:
    base: GraphState = dict(state) if state else {}
    base.setdefault("messages", [])
    return base


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("start", _noop)
    graph.set_entry_point("start")
    graph.add_edge("start", END)
    return graph.compile()
