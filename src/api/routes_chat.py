from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import StructuredTool
from starlette.concurrency import run_in_threadpool

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
        """List all candidate applications and their scores. Only available for recruiters."""
        return list_candidate_rankings(user, job_id=job_id)
    return StructuredTool.from_function(func=tool_func, name="list_rankings", description="List all candidate applications and their scores")

def get_candidate_details_tool(user: User):
    def tool_func(ranking_id: str):
        """Get full details of a specific candidate's application. Only available for recruiters."""
        from api.routes_dashboard import get_ranking
        try:
            return get_ranking(ranking_id, user)
        except Exception as e:
            return {"error": str(e)}
    return StructuredTool.from_function(func=tool_func, name="get_candidate_details", description="Get full details of a specific candidate application")

def get_my_applications_tool(user: User):
    def tool_func():
        """List all your job applications and their current status. Only available for candidates."""
        return list_candidate_rankings(user)
    return StructuredTool.from_function(func=tool_func, name="get_my_applications", description="List your job applications and status")

def get_application_details_tool(user: User):
    def tool_func(job_id: str):
        """Get details and status of your application for a specific job. Only available for candidates."""
        from services.rankings import get_my_submission
        try:
            return get_my_submission(job_id, user)
        except Exception as e:
            return {"error": str(e)}
    return StructuredTool.from_function(func=tool_func, name="get_application_details", description="Get status of your application for a specific job")

def get_create_job_tool(user: User):
    def tool_func(title: str, description: str):
        """Create a new job position. Only available for recruiters. 
        Requires a 'title' and a 'description' (can be markdown)."""
        return create_job(title, description, user)
    return StructuredTool.from_function(func=tool_func, name="create_job", description="Post a new job position")

def get_update_job_tool(user: User):
    def tool_func(job_id: str, title: Optional[str] = None, description: Optional[str] = None):
        """Update an existing job position. Only available for recruiters.
        Provide the job_id and at least one field to update."""
        from services.jobs import update_job
        return update_job(job_id, title, description, user)
    return StructuredTool.from_function(func=tool_func, name="update_job", description="Update an existing job position")

def get_delete_job_tool(user: User):
    def tool_func(job_id: str):
        """Delete an existing job position. Only available for recruiters."""
        from services.jobs import delete_job
        return delete_job(job_id, user)
    return StructuredTool.from_function(func=tool_func, name="delete_job", description="Delete a job position")

def get_re_evaluate_tool(user: User):
    async def tool_func(ranking_id: str):
        """Trigger a re-evaluation of a specific candidate's resume. Only available for recruiters."""
        from fastapi import BackgroundTasks
        from services.rankings import trigger_re_evaluation
        # Note: BackgroundTasks cannot be easily injected here without more plumbing,
        # but we can trigger it directly if we don't mind the wait, or use a mock background task.
        # For simplicity in the tool, we'll try to use a dummy background task if needed.
        bt = BackgroundTasks()
        res = await trigger_re_evaluation(ranking_id, user, bt)
        # We manually run the tasks if any were added
        for task in bt.tasks:
            await run_in_threadpool(task.func, *task.args, **task.kwargs)
        return res
    return StructuredTool.from_function(func=tool_func, name="re_evaluate_candidate", description="Trigger re-evaluation of a candidate")

def get_re_evaluate_all_tool(user: User):
    async def tool_func(job_id: str):
        """Trigger re-evaluation of ALL candidates for a specific job. Only available for recruiters."""
        from fastapi import BackgroundTasks
        from services.rankings import trigger_re_evaluation_all
        bt = BackgroundTasks()
        res = await trigger_re_evaluation_all(job_id, user, bt)
        for task in bt.tasks:
            # Re-evaluation all might have many tasks, running them sequentially here might be slow
            # but for a tool call it's better than nothing.
            await run_in_threadpool(task.func, *task.args, **task.kwargs)
        return res
    return StructuredTool.from_function(func=tool_func, name="re_evaluate_all_candidates", description="Trigger re-evaluation for all candidates of a job")

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

from fastapi.responses import StreamingResponse
import json

@router.post("/message")
async def chat_message(
    req: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    async def event_generator():
        db = get_database()
        model = _get_chat_model()
        
        tools = [
            get_job_list_tool(current_user),
            get_job_details_tool(current_user)
        ]
        if current_user.role == "recruiter":
            tools.extend([
                get_candidate_rankings_tool(current_user),
                get_candidate_details_tool(current_user),
                get_create_job_tool(current_user),
                get_update_job_tool(current_user),
                get_delete_job_tool(current_user),
                get_re_evaluate_tool(current_user),
                get_re_evaluate_all_tool(current_user)
            ])
        elif current_user.role == "candidate":
            tools.extend([
                get_my_applications_tool(current_user),
                get_application_details_tool(current_user)
            ])
        
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
   - When you create a job, use the returned 'id' to inject a [[JOB:id]] card in your response.
   - PLACEMENT: Cards render as block elements (creating newlines). While they can be placed mid-sentence, choose positions that don't disrupt readability. Specifically: NEVER place a card at the very beginning of a bullet point, and NEVER place it immediately before a punctuation mark (like a period).
4. When summarizing tool outputs, be extremely concise. Provide only relevant facts.
   - When listing entities (jobs or candidates), if the list is short (e.g., 5 or fewer items), use the [[TYPE:ID]] card format for each item to provide a rich UI experience.
5. NEVER print raw UUIDs in your conversational text.
6. ROLE-SPECIFIC CAPABILITIES:
   - RECRUITERS: You can manage the entire job lifecycle, including posting new roles, updating requirements, and removing positions. You also have access to all candidate evaluations, allowing you to review detailed scores, compare rankings, and trigger re-evaluations of resumes when necessary.
   - CANDIDATES: You can view your personal application history and check the current status of your submissions for various roles.
"""
        messages = [SystemMessage(content=system_prompt)]
        for m in raw_history:
            if m["role"] == "user":
                messages.append(HumanMessage(content=m["content"]))
            else:
                messages.append(AIMessage(content=m["content"]))
        messages.append(HumanMessage(content=req.message))
        
        try:
            yield f"data: {json.dumps({'status': 'Thinking...'})}\n\n"
            response = await run_in_threadpool(model_with_tools.invoke, messages)
            
            if response.tool_calls:
                yield f"data: {json.dumps({'status': 'Calling Tools...'})}\n\n"
                messages.append(response)
                for tc in response.tool_calls:
                    tname = tc["name"]
                    targs = tc["args"]
                    target_tool = next((t for t in tools if t.name == tname), None)
                    
                    if target_tool:
                        tool_res = await run_in_threadpool(target_tool.invoke, targs)
                        messages.append(ToolMessage(content=str(tool_res), tool_call_id=tc["id"]))
                    else:
                        messages.append(ToolMessage(content=f"Error: Tool {tname} not permitted.", tool_call_id=tc["id"]))
                
                yield f"data: {json.dumps({'status': 'Thinking...'})}\n\n"
                final_response = await run_in_threadpool(model.invoke, messages)
                reply_content = str(final_response.content)
            else:
                reply_content = str(response.content)
            
            now = datetime.now(timezone.utc)
            db.chat_history.insert_many([
                {"username": current_user.username, "role": "user", "content": req.message, "timestamp": now},
                {"username": current_user.username, "role": "assistant", "content": reply_content, "timestamp": now}
            ])
            
            yield f"data: {json.dumps({'reply': reply_content})}\n\n"
        except Exception as e:
            logger.error(f"Chat error: {e}")
            yield f"data: {json.dumps({'error': 'Failed to get AI response'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/clear")
async def clear_chat(current_user: User = Depends(get_current_user)):
    db = get_database()
    db.chat_history.delete_many({"username": current_user.username})
    return {"status": "cleared"}
