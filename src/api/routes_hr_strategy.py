"""HR Strategy Agent HTTP API."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

import config
from agents.hr_strategy.graph import build_hr_strategy_graph
from agents.hr_strategy.messages_io import messages_to_records, records_to_messages
from agents.hr_strategy.models import HRJobSpec, HR_STRATEGY_JSON_SCHEMA, SPEC_SCHEMA_VERSION
from monitoring.registry import get_monitor
from agents.hr_strategy.repository import (
    create_session,
    get_latest_job_spec,
    get_session,
    insert_job_spec,
    replace_session_messages,
)

router = APIRouter(prefix="/hr-strategy", tags=["hr-strategy"])

_graph = build_hr_strategy_graph()


class CreateSessionResponse(BaseModel):
    session_id: str
    status: str


class ChatBody(BaseModel):
    content: str = Field(..., min_length=1, description="HR message for this turn")


class ChatResponse(BaseModel):
    session_id: str
    status: str
    reply: str | None = None
    completed_spec: dict[str, Any] | None = None


class SessionResponse(BaseModel):
    session_id: str
    status: str
    messages: list[dict[str, Any]]


class SchemaResponse(BaseModel):
    schema_version: int
    job_spec_json_schema: dict[str, Any]
    mongo_collections: dict[str, Any]


@router.post("/sessions", response_model=CreateSessionResponse)
def open_session():
    if not config.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not set")
    sid = str(uuid.uuid4())
    create_session(sid)
    return CreateSessionResponse(session_id=sid, status="collecting")


@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
def post_message(session_id: str, body: ChatBody):
    if not config.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not set")
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    mon = get_monitor()
    mon.http_activity("hr_strategy_chat", correlation_id=session_id, phase="start")
    ok = True
    err: str | None = None
    try:
        prior = records_to_messages(session.get("messages") or [])
        state = _graph.invoke({"messages": [*prior, HumanMessage(content=body.content)]})

        final_msgs = state.get("messages") or []
        completed = state.get("completed_spec")

        status = session.get("status", "collecting")
        if completed is not None:
            spec = HRJobSpec.model_validate(completed)
            insert_job_spec(session_id, spec)
            status = "completed"

        replace_session_messages(session_id, messages_to_records(final_msgs), status=status)

        reply = _last_assistant_text(final_msgs)
        return ChatResponse(
            session_id=session_id,
            status=status,
            reply=reply,
            completed_spec=completed,
        )
    except Exception as e:
        ok = False
        err = str(e)
        raise
    finally:
        mon.http_activity("hr_strategy_chat", correlation_id=session_id, phase="end", ok=ok, error=err)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def read_session(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(
        session_id=session_id,
        status=session.get("status", "collecting"),
        messages=session.get("messages") or [],
    )


@router.get("/sessions/{session_id}/spec", response_model=dict[str, Any])
def read_latest_spec(session_id: str):
    doc = get_latest_job_spec(session_id)
    if not doc:
        raise HTTPException(status_code=404, detail="No structured spec generated yet")
    return {"session_id": session_id, "spec": doc.get("spec"), "created_at": doc.get("created_at")}


@router.get("/schema", response_model=SchemaResponse)
def read_schema():
    """Return HRJobSpec JSON Schema and Mongo collection notes for clients."""
    return SchemaResponse(
        schema_version=SPEC_SCHEMA_VERSION,
        job_spec_json_schema=HR_STRATEGY_JSON_SCHEMA,
        mongo_collections={
            "hr_strategy_sessions": {
                "description": "Conversation and state",
                "fields": {
                    "session_id": "str, unique",
                    "status": "collecting | completed",
                    "messages": "list[dict] serialized messages",
                    "created_at": "datetime",
                    "updated_at": "datetime",
                },
            },
            "hr_job_specs": {
                "description": "Finalized structured hiring brief",
                "fields": {
                    "session_id": "str",
                    "schema_version": "int",
                    "spec": "object, same shape as HRJobSpec",
                    "json_schema_snapshot": "object, Pydantic JSON Schema snapshot",
                    "created_at": "datetime",
                },
            },
        },
    )


def _last_assistant_text(messages: list[Any]) -> str | None:
    from langchain_core.messages import AIMessage

    for m in reversed(messages):
        if isinstance(m, AIMessage) and m.content:
            c = m.content
            if isinstance(c, str) and c.strip():
                return c
    return None
