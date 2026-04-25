import pytest
from fastapi import HTTPException, Request
from unittest.mock import MagicMock
from api.deps import verify_hiring_agent_api_key, get_current_user, get_current_user_optional, require_role
from api.auth_models import User, UserInDB
import config

def test_verify_hiring_agent_api_key_no_config(monkeypatch):
    monkeypatch.setattr(config, "HIRING_AGENT_API_KEY", None)
    # Should not raise
    verify_hiring_agent_api_key(None)

def test_verify_hiring_agent_api_key_valid(monkeypatch):
    monkeypatch.setattr(config, "HIRING_AGENT_API_KEY", "secret")
    # Should not raise
    verify_hiring_agent_api_key("secret")

def test_verify_hiring_agent_api_key_invalid(monkeypatch):
    monkeypatch.setattr(config, "HIRING_AGENT_API_KEY", "secret")
    with pytest.raises(HTTPException) as exc:
        verify_hiring_agent_api_key("wrong")
    assert exc.value.status_code == 401

def test_get_current_user_bearer_success(monkeypatch):
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {"Authorization": "Bearer valid-token"}
    mock_request.query_params = {}
    
    mock_user = UserInDB(username="alice", role="recruiter", hashed_password="pw")
    monkeypatch.setattr("api.deps.get_user", lambda t: mock_user if t == "valid-token" else None)
    
    user = get_current_user(mock_request)
    assert user.username == "alice"

def test_get_current_user_query_success(monkeypatch):
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}
    mock_request.query_params = {"token": "query-token"}
    
    mock_user = UserInDB(username="bob", role="candidate", hashed_password="pw")
    monkeypatch.setattr("api.deps.get_user", lambda t: mock_user if t == "query-token" else None)
    
    user = get_current_user(mock_request)
    assert user.username == "bob"

def test_get_current_user_missing(monkeypatch):
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}
    mock_request.query_params = {}
    
    with pytest.raises(HTTPException) as exc:
        get_current_user(mock_request)
    assert exc.value.status_code == 401

def test_get_current_user_optional(monkeypatch):
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}
    mock_request.query_params = {}
    
    assert get_current_user_optional(mock_request) is None

def test_require_role():
    checker = require_role("recruiter")
    user = User(username="alice", role="recruiter")
    # Should work
    assert checker(user) == user
    
    user_cand = User(username="bob", role="candidate")
    with pytest.raises(HTTPException) as exc:
        checker(user_cand)
    assert exc.value.status_code == 403
