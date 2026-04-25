import pytest
from unittest.mock import MagicMock, patch
from db.mongo import get_database, generate_embedding, save_document_with_embedding, create_vector_index, vector_search
import config

def test_get_database(mock_get_database):
    db = get_database()
    assert db == mock_get_database

def test_generate_embedding(mock_openai, monkeypatch):
    monkeypatch.setattr(config, "OPENAI_API_KEY", "test-key")
    
    # We need to find the embeddings.create mock
    # mock_openai is actually the side_effect or the completion.create mock depending on conftest
    # Let's re-patch locally to be very sure
    mock_client = MagicMock()
    monkeypatch.setattr("db.mongo.OpenAI", lambda **kwargs: mock_client)
    
    mock_resp = MagicMock()
    mock_data = MagicMock()
    mock_data.embedding = [0.1, 0.2]
    mock_resp.data = [mock_data]
    mock_resp.usage = MagicMock()
    
    mock_client.embeddings.create.return_value = mock_resp
    
    emb = generate_embedding("hello")
    assert emb == [0.1, 0.2]
    assert mock_client.embeddings.create.called

def test_save_document_with_embedding(mock_get_database, monkeypatch):
    monkeypatch.setattr(config, "OPENAI_API_KEY", "test-key")
    
    mock_client = MagicMock()
    monkeypatch.setattr("db.mongo.OpenAI", lambda **kwargs: mock_client)
    
    # Mock embedding
    mock_resp = MagicMock()
    mock_data = MagicMock()
    mock_data.embedding = [0.5, 0.6]
    mock_resp.data = [mock_data]
    mock_client.embeddings.create.return_value = mock_resp
    
    # Mock MongoDB insert
    mock_get_database["test_coll"].insert_one.return_value.inserted_id = "doc123"
    
    doc = {"name": "test"}
    doc_id = save_document_with_embedding("test_coll", doc, "text to embed")
    
    assert doc_id == "doc123"
    assert doc["embedding"] == [0.5, 0.6]

def test_create_vector_index(mock_get_database):
    create_vector_index("coll", "field", 128, "idx_name")
    mock_get_database.command.assert_called_once()
    args = mock_get_database.command.call_args[0][0]
    assert args["createIndexes"] == "coll"

def test_vector_search(mock_get_database):
    mock_get_database["coll"].aggregate.return_value = [{"id": "1"}]
    
    res = vector_search("coll", [0.1], "field", k=5)
    
    assert len(res) == 1
    assert res[0]["id"] == "1"
    mock_get_database["coll"].aggregate.assert_called_once()
