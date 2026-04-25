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
    mock_client = MagicMock()
    mock_client.__getitem__.return_value = mock_db
    
    def get_db_side_effect():
        return mock_db
        
    monkeypatch.setattr("db.mongo.get_mongo_client", lambda: mock_client)
    monkeypatch.setattr("db.mongo.get_database", get_db_side_effect)
    
    for module_name in [
        "db.mongo", "services.jobs", "services.rankings", "services.evaluations",
        "monitoring.usage_service", "dashboard.repository", "api.auth_repository",
        "api.routes_auth", "api.routes_candidate", "api.routes_recruiter", "api.routes_chat",
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
    mock_embeddings = MagicMock()
    mock_client.chat.completions = mock_completions
    mock_client.embeddings = mock_embeddings
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
    mock_embeddings.create = MagicMock()

    for path in ["agents.ocr_agent.OpenAI", "safety.guardrails.OpenAI", "db.mongo.OpenAI"]:
        try:
            monkeypatch.setattr(path, lambda **kwargs: mock_client)
        except (AttributeError, ImportError):
            pass

    return mock_create

@pytest.fixture
def mock_chat_openai(monkeypatch):
    mock_instance = MagicMock()
    mock_structured = MagicMock()
    mock_instance.mock_structured = mock_structured
    
    def mock_with_structured_output(output_schema):
        return mock_structured
        
    mock_instance.with_structured_output = mock_with_structured_output
    
    for path in [
        "agents.data_arrangement.agent.ChatOpenAI",
        "agents.scoring.agent.ChatOpenAI",
        "agents.hr_strategy.graph.ChatOpenAI",
        "graph.pipeline.ChatOpenAI",
        "services.jobs.ChatOpenAI",
        "api.routes_chat.ChatOpenAI"
    ]:
        try:
            monkeypatch.setattr(path, lambda **kwargs: mock_instance)
        except (AttributeError, ImportError):
            pass
    
    return mock_instance
