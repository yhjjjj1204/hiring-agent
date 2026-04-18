"""FastAPI dependencies (auth, etc.)."""

from __future__ import annotations

from fastapi import HTTPException, Security, Depends, Header, Query, Request
from fastapi.security import APIKeyHeader

import config
from api.auth_repository import get_user
from api.auth_models import User

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_hiring_agent_api_key(x_api_key: str | None = Security(_api_key_header)) -> None:
    """When HIRING_AGENT_API_KEY is set, require matching X-API-Key header."""
    expected = (config.HIRING_AGENT_API_KEY or "").strip()
    if not expected:
        return
    got = (x_api_key or "").strip()
    if not got or got != expected:
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key")

def get_current_user(request: Request) -> User:
    actual_token = None
    
    # 1. Try Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        actual_token = auth_header[7:].strip()
    
    # 2. Try query parameter (useful for direct file downloads)
    if not actual_token:
        actual_token = request.query_params.get("token")

    if not actual_token:
        raise HTTPException(status_code=401, detail="Authentication token missing")

    user_db = get_user(actual_token)
    if not user_db:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")
    
    return User(username=user_db.username, role=user_db.role)

def get_current_user_optional(request: Request) -> User | None:
    try:
        return get_current_user(request)
    except HTTPException:
        return None

def require_role(role: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(status_code=403, detail=f"Role '{role}' required")
        return current_user
    return role_checker
