from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

import config
from api.auth_models import User
from api.deps import get_current_user
from db.mongo import get_database

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

def _get_chat_model() -> ChatOpenAI:
    if not config.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY not configured")
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
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
    
    # 1. Load history from DB
    raw_history = list(db.chat_history.find({"username": current_user.username}).sort("timestamp", 1))
    
    # 2. Build messages for LLM
    system_prompt = f"""You are a helpful AI assistant for the Hiring Agent platform.
You are interacting with a user whose role is: {current_user.role}.
Current page context: {req.context or 'General'}.

Help the user with their questions. Be professional and concise.
"""
    messages = [SystemMessage(content=system_prompt)]
    
    for m in raw_history:
        if m["role"] == "user":
            messages.append(HumanMessage(content=m["content"]))
        else:
            messages.append(AIMessage(content=m["content"]))
            
    messages.append(HumanMessage(content=req.message))
    
    try:
        # 3. Get AI Response
        response = await model.ainvoke(messages)
        reply_content = str(response.content)
        
        # 4. Save both messages to DB
        now = datetime.now(timezone.utc)
        db.chat_history.insert_many([
            {
                "username": current_user.username,
                "role": "user",
                "content": req.message,
                "timestamp": now
            },
            {
                "username": current_user.username,
                "role": "assistant",
                "content": reply_content,
                "timestamp": now
            }
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
