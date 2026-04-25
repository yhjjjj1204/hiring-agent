import pytest
import os
import sys
from unittest.mock import MagicMock

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from api.auth_models import User

@pytest.fixture
def recruiter_user():
    return User(username="recruiter1", role="recruiter", email="r1@example.com")

@pytest.fixture
def candidate_user():
    return User(username="candidate1", role="candidate", email="c1@example.com")

from fastapi.testclient import TestClient

@pytest.fixture
def mock_get_database(monkeypatch):
    mock_db = MagicMock()
    
    # Patch the function that returns the database
    def get_db_side_effect():
        return mock_db
        
    monkeypatch.setattr("db.mongo.get_database", get_db_side_effect)
    
    # Also patch everywhere it was imported as a name
    for module_name in [
        "services.jobs", "services.rankings", "services.evaluations",
        "monitoring.usage_service", "dashboard.repository", "api.auth_repository",
        "api.routes_auth", "api.routes_candidate", "api.routes_recruiter",
        "agents.data_arrangement.repository", "agents.hr_strategy.repository",
        "agents.background_analysis.repository"
    ]:
        try:
            mod = __import__(module_name, fromlist=["get_database"])
            if hasattr(mod, "get_database"):
                monkeypatch.setattr(f"{module_name}.get_database", get_db_side_effect)
        except ImportError:
            pass
            
    return mock_db

@pytest.fixture
def client(mock_get_database):
    # Important: Import app AFTER patching get_database
    from api.main import app
    with TestClient(app) as c:
        yield c

@pytest.fixture
def mock_llm_response():
    def _create_response(content: str):
        mock = MagicMock()
        mock.content = content
        return mock
    return _create_response

@pytest.fixture
def mock_openai(monkeypatch):
    mock_client = MagicMock()
    mock_completions = MagicMock()
    mock_client.chat.completions = mock_completions
    mock_create = MagicMock()
    
    def side_effect(*args, **kwargs):
        mock_resp = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = mock_create.return_value
        mock_resp.choices = [mock_choice]
        mock_resp.usage = MagicMock()
        return mock_resp
    
    mock_create.side_effect = side_effect
    mock_completions.create = mock_create
    monkeypatch.setattr("agents.ocr_agent.OpenAI", lambda api_key: mock_client)
    return mock_create

@pytest.fixture
def mock_chat_openai(monkeypatch):
    mock_instance = MagicMock()
    mock_structured = MagicMock()
    mock_instance.mock_structured = mock_structured
    
    def mock_with_structured_output(output_schema):
        return mock_structured
        
    mock_instance.with_structured_output = mock_with_structured_output
    
    # Patch all the places ChatOpenAI is imported
    for path in [
        "agents.data_arrangement.agent.ChatOpenAI",
        "agents.scoring.agent.ChatOpenAI",
        "agents.hr_strategy.graph.ChatOpenAI",
        "graph.pipeline.ChatOpenAI",
        "services.jobs.ChatOpenAI"
    ]:
        try:
            monkeypatch.setattr(path, lambda **kwargs: mock_instance)
        except (AttributeError, ImportError):
            pass
    
    return mock_instance
