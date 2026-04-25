import pytest

def test_auth_register_candidate(client, mock_get_database):
    # Setup
    mock_get_database.users.find_one.return_value = None
    
    # Execute
    resp = client.post("/api/auth/register", json={
        "username": "tester",
        "password": "password123",
        "email": "test@example.com",
        "role": "candidate"
    })
    
    # Assert
    assert resp.status_code == 200
    assert resp.json()["username"] == "tester"
    assert mock_get_database.users.insert_one.called

def test_auth_login_success(client, mock_get_database, monkeypatch):
    # Setup
    from api.auth_utils import get_password_hash
    hashed = get_password_hash("password123")
    
    mock_get_database.users.find_one.return_value = {
        "username": "tester",
        "hashed_password": hashed,
        "email": "test@example.com",
        "role": "candidate"
    }
    
    # Execute
    resp = client.post("/api/auth/login", data={
        "username": "tester",
        "password": "password123"
    })
    
    # Assert
    assert resp.status_code == 200
    assert "access_token" in resp.json()
