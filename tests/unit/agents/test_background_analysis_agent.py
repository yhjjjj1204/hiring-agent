import pytest
from unittest.mock import MagicMock, patch
from agents.background_analysis.agent import run_background_analysis
from agents.background_analysis.models import GitHubMetrics, AcademicMetrics

@pytest.fixture
def mock_clients(monkeypatch):
    mock_gh = MagicMock()
    mock_ac = MagicMock()
    monkeypatch.setattr("agents.background_analysis.agent.fetch_github_metrics", mock_gh)
    monkeypatch.setattr("agents.background_analysis.agent.fetch_academic_metrics", mock_ac)
    return mock_gh, mock_ac

def test_run_background_analysis_full(mock_clients):
    mock_gh, mock_ac = mock_clients
    
    mock_gh.return_value = GitHubMetrics(
        login="testuser",
        profile_url="http://github.com/testuser",
        contributions_last_year=100,
        data_source="github_api"
    )
    
    mock_ac.return_value = AcademicMetrics(
        display_name="Test Author",
        cited_by_count=50,
        works_count=5,
        identity_match="name_search"
    )
    
    res = run_background_analysis("Test Author", "testuser")
    
    assert res.github.login == "testuser"
    assert res.academic.display_name == "Test Author"
    # Verify graph nodes
    node_ids = [n.id for n in res.graph.nodes]
    assert "n_candidate" in node_ids
    assert "n_github" in node_ids
    assert "n_academic" in node_ids
    assert "n_code_metric" in node_ids
    assert "n_cite_metric" in node_ids

def test_run_background_analysis_github_only(mock_clients):
    mock_gh, mock_ac = mock_clients
    mock_gh.return_value = GitHubMetrics(login="testuser", contributions_last_year=10)
    mock_ac.return_value = AcademicMetrics() # Empty
    
    res = run_background_analysis("None", "testuser")
    
    node_ids = [n.id for n in res.graph.nodes]
    assert "n_github" in node_ids
    assert "n_academic" not in node_ids

def test_run_background_analysis_with_scholar_url(mock_clients):
    mock_gh, mock_ac = mock_clients
    mock_gh.return_value = None
    mock_ac.return_value = None
    
    res = run_background_analysis("Alice", google_scholar_url="http://scholar.google.com/alice")
    
    node_ids = [n.id for n in res.graph.nodes]
    assert "n_scholar_claim" in node_ids
    assert res.graph.edges[-1].relation == "claimed_profile_url"
