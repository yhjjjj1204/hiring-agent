"""LangChain 消息与 Mongo 文档之间的序列化（不含 System，由运行时注入）。"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage


def messages_to_records(messages: list[BaseMessage]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for m in messages:
        if isinstance(m, HumanMessage):
            out.append({"type": "human", "content": _text(m.content)})
        elif isinstance(m, AIMessage):
            rec: dict[str, Any] = {
                "type": "ai",
                "content": _text(m.content) if m.content else "",
            }
            if m.tool_calls:
                rec["tool_calls"] = m.tool_calls
            out.append(rec)
        elif isinstance(m, ToolMessage):
            out.append(
                {
                    "type": "tool",
                    "content": _text(m.content),
                    "tool_call_id": m.tool_call_id,
                    "name": m.name or "",
                }
            )
    return out


def records_to_messages(records: list[dict[str, Any]]) -> list[BaseMessage]:
    msgs: list[BaseMessage] = []
    for r in records:
        t = r.get("type")
        if t == "human":
            msgs.append(HumanMessage(content=r.get("content", "")))
        elif t == "ai":
            tc = r.get("tool_calls")
            if tc:
                msgs.append(
                    AIMessage(content=r.get("content", ""), tool_calls=tc),
                )
            else:
                msgs.append(AIMessage(content=r.get("content", "")))
        elif t == "tool":
            msgs.append(
                ToolMessage(
                    content=r.get("content", ""),
                    tool_call_id=r.get("tool_call_id", ""),
                    name=r.get("name", ""),
                ),
            )
    return msgs


def _text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return json.dumps(content, ensure_ascii=False)
    return str(content)
