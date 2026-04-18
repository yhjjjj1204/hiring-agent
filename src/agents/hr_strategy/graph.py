"""HR Strategy Agent: Conversation + Tooling for finalization via LangGraph."""

from __future__ import annotations

import json
import logging
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, BaseMessage, SystemMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

import config
from agents.hr_strategy.models import HRJobSpec
from agents.hr_strategy.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def _finalize_hr_job_spec(spec: HRJobSpec) -> str:
    """Tool output: Returns full JSON for ToolMessage, to be parsed by downstream nodes."""
    return spec.model_dump_json()


finalize_hr_job_spec = StructuredTool.from_function(
    func=_finalize_hr_job_spec,
    name="finalize_hr_job_spec",
    description=(
        "Call when hiring requirements are complete and HR has confirmed to finalize. "
        "Submit one structured HRJobSpec (role, required skills, bonus items, culture-fit metrics, etc.)."
    ),
    args_schema=HRJobSpec,
)


class HRStrategyState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    completed_spec: dict | None


def _route_after_agent(state: HRStrategyState):
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return END


def _build_model() -> ChatOpenAI:
    if not config.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set; HR Strategy model cannot run")
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        api_key=config.OPENAI_API_KEY,
    )


def _agent_node(state: HRStrategyState) -> dict:
    model = _build_model().bind_tools([finalize_hr_job_spec], strict=False)
    sys = SystemMessage(content=SYSTEM_PROMPT)
    reply = model.invoke([sys, *state["messages"]])
    return {"messages": [reply]}


def _capture_spec_node(state: HRStrategyState) -> dict:
    completed: dict | None = None
    for m in reversed(state["messages"]):
        if isinstance(m, ToolMessage) and m.name == "finalize_hr_job_spec":
            try:
                completed = json.loads(m.content)
                HRJobSpec.model_validate(completed)
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning("finalize_hr_job_spec output is not valid HRJobSpec: %s", e)
            break

    updates: dict = {}
    if completed is not None:
        updates["completed_spec"] = completed
        updates["messages"] = [
            AIMessage(
                content=(
                    "Structured job requirements (JSON) have been generated from this conversation and saved. "
                    "To adjust, describe the changes and continue chatting, or start a new session."
                ),
            ),
        ]
    return updates


def build_hr_strategy_graph():
    tool_node = ToolNode([finalize_hr_job_spec])

    graph = StateGraph(HRStrategyState)
    graph.add_node("agent", _agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("capture_spec", _capture_spec_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges(
        "agent",
        _route_after_agent,
        {"tools": "tools", END: END},
    )
    graph.add_edge("tools", "capture_spec")
    graph.add_edge("capture_spec", END)

    return graph.compile()
