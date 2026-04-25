import pytest
from unittest.mock import MagicMock, patch
from agents.background_analysis.academic_client import parse_google_scholar_user_id, fetch_academic_metrics, citation_impact_index
import httpx

def test_parse_google_scholar_user_id():
    url = "https://scholar.google.com/citations?user=xyz123&hl=en"
    assert parse_google_scholar_user_id(url) == "xyz123"
    assert parse_google_scholar_user_id("not scholar") is None

@pytest.fixture
def mock_httpx(monkeypatch):
    mock_client = MagicMock()
    monkeypatch.setattr("httpx.Client", lambda **kwargs: MagicMock(__enter__=lambda s: mock_client, __exit__=lambda *args: None))
    return mock_client

def test_fetch_academic_metrics_success(mock_httpx):
    # Mock OpenAlex author search
    mock_oa_resp = MagicMock()
    mock_oa_resp.status_code = 200
    mock_oa_resp.json.return_value = {
        "results": [{"id": "https://openalex.org/A1", "display_name": "Test Author", "cited_by_count": 100, "works_count": 10}]
    }
    
    # Mock S2 author search
    mock_s2_resp = MagicMock()
    mock_s2_resp.status_code = 200
    mock_s2_resp.json.return_value = {
        "data": [{"authorId": "S1", "name": "Test Author", "citationCount": 50, "paperCount": 5}]
    }
    
    # Mock OpenAlex works
    mock_oa_works = MagicMock()
    mock_oa_works.status_code = 200
    mock_oa_works.json.return_value = {
        "results": [{"title": "Paper 1", "publication_year": 2020, "cited_by_count": 10, "id": "W1"}]
    }

    # Mock S2 papers
    mock_s2_papers = MagicMock()
    mock_s2_papers.status_code = 200
    mock_s2_papers.json.return_value = {
        "papers": [{"title": "Paper 2", "year": 2021, "citationCount": 5, "url": "U2"}]
    }
    
    mock_httpx.get.side_effect = [mock_oa_resp, mock_s2_resp, mock_oa_works, mock_s2_papers]
    
    res = fetch_academic_metrics("Test Author")
    assert res.display_name == "Test Author"
    assert res.cited_by_count == 100
    # OpenAlex works returned 1, S2 papers returned 1. Merged should be 2.
    assert len(res.top_papers) == 2

def test_fetch_academic_metrics_scholar_only():
    res = fetch_academic_metrics(None, google_scholar_url="https://scholar.google.com/citations?user=123")
    assert res.identity_match == "unverified_claim_url"
    assert res.display_name is None

def test_citation_impact_index():
    assert citation_impact_index(0) == 0.0
    assert 0.0 < citation_impact_index(100) < 1.0
    assert citation_impact_index(1000000) == 1.0
