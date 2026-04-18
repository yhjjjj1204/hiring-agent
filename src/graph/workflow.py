"""Lightweight placeholder graph. For the full recruitment pipeline, see `graph.pipeline` (`build_hiring_pipeline_graph`)."""

from typing import TypedDict

from langgraph.graph import END, StateGraph


class GraphState(TypedDict, total=False):
    """State shared across nodes; gradually extended by business fields."""

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
