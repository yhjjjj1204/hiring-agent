"""FastAPI dependencies (auth, etc.)."""

from __future__ import annotations

from fastapi import HTTPException, Security, Depends, Header
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

def get_current_user(authorization: str | None = Header(None)) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    # Expecting "Bearer <username>" for our simple mock
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
             raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    user_db = get_user(token)
    if not user_db:
        raise HTTPException(status_code=401, detail="User not found or invalid token")
    
    return User(username=user_db.username, role=user_db.role)

def require_role(role: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(status_code=403, detail=f"Role '{role}' required")
        return current_user
    return role_checker
