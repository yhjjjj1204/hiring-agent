from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import StructuredTool

import config
from api.auth_models import User
from api.deps import get_current_user
from db.mongo import get_database
from services.jobs import list_jobs, get_job, create_job
from services.rankings import list_candidate_rankings

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    role: str # 'user' or 'assistant'
    content: str
    timestamp: datetime

class ChatRequest(BaseModel):
    message: str
    context: Optional[dict[str, Any]] = None

class ChatResponse(BaseModel):
    reply: str

# --- TOOL DEFINITIONS ---

def get_job_list_tool(user: User):
    def tool_func():
        """List all available job positions. Use 'id' from the returned list for any JOB card or detail fetch."""
        return list_jobs(user)
    return StructuredTool.from_function(func=tool_func, name="list_jobs", description="List all open job positions")

def get_job_details_tool(user: User):
    def tool_func(job_id: str):
        """Get full details of a specific job. Requires a technical job_id (UUID), not a title."""
        return get_job(job_id)
    return StructuredTool.from_function(func=tool_func, name="get_job_details", description="Get details of a specific job by its technical job_id")

def get_candidate_rankings_tool(user: User):
    def tool_func(job_id: Optional[str] = None):
        """List candidate applications. Use 'ranking_id' from the returned list for any CANDIDATE card or detail fetch."""
        return list_candidate_rankings(user, job_id=job_id)
    return StructuredTool.from_function(func=tool_func, name="list_rankings", description="List candidate applications and their scores")

def get_candidate_details_tool(user: User):
    def tool_func(ranking_id: str):
        """Get full details of a specific candidate application. Requires a technical ranking_id (UUID), not a name."""
        from db.mongo import get_database
        db = get_database()
        doc = db.candidate_rankings.find_one({"ranking_id": ranking_id})
        if doc:
            doc.pop("_id", None)
            return doc
        return {"error": f"Candidate ranking with id {ranking_id} not found. Ensure you are using the ranking_id (UUID)."}
    return StructuredTool.from_function(func=tool_func, name="get_candidate_details", description="Get full details of a specific candidate by their ranking_id")

def _get_chat_model() -> ChatOpenAI:
    if not config.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY not configured")
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0, 
        api_key=config.OPENAI_API_KEY
    )

@router.get("/history", response_model=List[ChatMessage])
async def get_chat_history(current_user: User = Depends(get_current_user)):
    db = get_database()
    history = list(db.chat_history.find({"username": current_user.username}).sort("timestamp", 1))
    for msg in history:
        msg.pop("_id", None)
    return history

@router.post("/message", response_model=ChatResponse)
async def chat_message(
    req: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    db = get_database()
    model = _get_chat_model()
    
    tools = [
        get_job_list_tool(current_user),
        get_job_details_tool(current_user),
        get_candidate_rankings_tool(current_user),
        get_candidate_details_tool(current_user)
    ]
    
    model_with_tools = model.bind_tools(tools)
    raw_history = list(db.chat_history.find({"username": current_user.username}).sort("timestamp", 1))
    
    system_prompt = f"""You are a helpful AI assistant for the Hiring Agent platform.
User role: {current_user.role}.
Current page context: {req.context or 'General'}.

GUIDELINES:
1. You have access to the current page context.
2. CRITICAL: Technical IDs like 'job_id' and 'candidate_id' (which is the ranking_id) are provided in the context. 
   - ALWAYS use the technical UUIDs for tool calls and card injections. 
   - NEVER use the human name (e.g. 'aleksana') as an ID.
3. INJECTION FORMAT (MANDATORY): You MUST ALWAYS use the format [[JOB:job_id]] or [[CANDIDATE:ranking_id]] when mentioning a specific entity.
   - Example: If context says 'candidate_id: 0824c576...', use [[CANDIDATE:0824c576...]]
4. When summarizing tool outputs, be extremely concise. Provide only relevant facts.
5. NEVER print raw UUIDs in your conversational text.
"""
    messages = [SystemMessage(content=system_prompt)]
    for m in raw_history:
        if m["role"] == "user":
            messages.append(HumanMessage(content=m["content"]))
        else:
            messages.append(AIMessage(content=m["content"]))
    messages.append(HumanMessage(content=req.message))
    
    try:
        response = model_with_tools.invoke(messages)
        
        if response.tool_calls:
            messages.append(response)
            for tc in response.tool_calls:
                tname = tc["name"]
                targs = tc["args"]
                target_tool = next((t for t in tools if t.name == tname), None)
                
                if target_tool:
                    tool_res = target_tool.invoke(targs)
                    messages.append(ToolMessage(content=str(tool_res), tool_call_id=tc["id"]))
                else:
                    messages.append(ToolMessage(content=f"Error: Tool {tname} not permitted.", tool_call_id=tc["id"]))
            
            final_response = model.invoke(messages)
            reply_content = str(final_response.content)
        else:
            reply_content = str(response.content)
        
        now = datetime.now(timezone.utc)
        db.chat_history.insert_many([
            {"username": current_user.username, "role": "user", "content": req.message, "timestamp": now},
            {"username": current_user.username, "role": "assistant", "content": reply_content, "timestamp": now}
        ])
        
        return ChatResponse(reply=reply_content)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get AI response")

@router.post("/clear")
async def clear_chat(current_user: User = Depends(get_current_user)):
    db = get_database()
    db.chat_history.delete_many({"username": current_user.username})
    return {"status": "cleared"}
