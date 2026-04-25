import pytest
from unittest.mock import MagicMock
from api.routes_auth import register, login, get_me
from api.auth_models import UserCreate, UserInDB
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm

def test_register_duplicate(mock_get_database, monkeypatch):
    mock_user_db = UserInDB(username="exists", role="candidate", hashed_password="pw")
    monkeypatch.setattr("api.routes_auth.get_user", lambda u: mock_user_db if u == "exists" else None)
    
    user_in = UserCreate(username="exists", password="pw", role="candidate")
    with pytest.raises(HTTPException) as exc:
        register(user_in)
    assert exc.value.status_code == 400

def test_login_failure(mock_get_database, monkeypatch):
    monkeypatch.setattr("api.routes_auth.get_user", lambda u: None)
    
    form_data = MagicMock(spec=OAuth2PasswordRequestForm)
    form_data.username = "wrong"
    form_data.password = "wrong"
    
    with pytest.raises(HTTPException) as exc:
        login(form_data)
    assert exc.value.status_code == 401

def test_get_me_success(mock_get_database, monkeypatch):
    mock_user_db = UserInDB(username="alice", role="recruiter", hashed_password="pw")
    monkeypatch.setattr("api.routes_auth.get_user", lambda t: mock_user_db if t == "valid" else None)
    
    res = get_me("valid")
    assert res.username == "alice"

def test_get_me_invalid_token(mock_get_database, monkeypatch):
    monkeypatch.setattr("api.routes_auth.get_user", lambda t: None)
    with pytest.raises(HTTPException) as exc:
        get_me("invalid")
    assert exc.value.status_code == 401
