"""FastAPI dependencies (auth, etc.)."""

from __future__ import annotations

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

import config

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_hiring_agent_api_key(x_api_key: str | None = Security(_api_key_header)) -> None:
    """When HIRING_AGENT_API_KEY is set, require matching X-API-Key header."""
    expected = (config.HIRING_AGENT_API_KEY or "").strip()
    if not expected:
        return
    got = (x_api_key or "").strip()
    if not got or got != expected:
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key")
