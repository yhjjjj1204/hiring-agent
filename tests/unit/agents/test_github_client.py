import pytest
from unittest.mock import MagicMock, patch
from agents.background_analysis.github_client import parse_github_login, fetch_github_metrics
import config

def test_parse_github_login():
    assert parse_github_login("tester") == "tester"
    assert parse_github_login("@tester") == "tester"
    assert parse_github_login("https://github.com/tester") == "tester"
    assert parse_github_login("https://github.com/tester/repo") == "tester"
    assert parse_github_login(None) is None
    assert parse_github_login("https://github.com/orgs/acme") is None # Org not user

@pytest.fixture
def mock_httpx(monkeypatch):
    mock_client = MagicMock()
    # We patch httpx.Client to return our mock_client when used as context manager
    monkeypatch.setattr("httpx.Client", lambda **kwargs: MagicMock(__enter__=lambda s: mock_client, __exit__=lambda *args: None))
    return mock_client

def test_fetch_github_metrics_success(mock_httpx, monkeypatch):
    monkeypatch.setattr(config, "GITHUB_TOKEN", None)
    
    # Mock user profile response
    mock_resp_user = MagicMock()
    mock_resp_user.status_code = 200
    mock_resp_user.json.return_value = {
        "login": "tester",
        "html_url": "http://github.com/tester",
        "public_repos": 5,
        "created_at": "2020-01-01T00:00:00Z"
    }
    
    # Mock events response (fallback since no token)
    mock_resp_events = MagicMock()
    mock_resp_events.status_code = 200
    mock_resp_events.json.return_value = [
        {"type": "PushEvent", "created_at": "2026-01-01T00:00:00Z"}
    ]
    
    mock_httpx.get.side_effect = [mock_resp_user, mock_resp_events]
    
    res = fetch_github_metrics("tester")
    assert res.login == "tester"
    assert res.data_source == "rest_events"
    assert res.contributions_last_year == 1

def test_fetch_github_metrics_404(mock_httpx):
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_httpx.get.return_value = mock_resp
    
    res = fetch_github_metrics("nonexistent")
    assert res is None
