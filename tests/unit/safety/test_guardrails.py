import pytest
from unittest.mock import MagicMock, patch
import json
import config
from safety.guardrails import moderate_text, GuardrailDecision

@pytest.fixture
def mock_config_guardrails(monkeypatch):
    monkeypatch.setattr(config, "GUARDRAIL_ENABLED", True)
    monkeypatch.setattr(config, "GUARDRAIL_MODE", "enforce")
    monkeypatch.setattr(config, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(config, "GUARDRAIL_CLASSIFIER_MODEL", "gpt-4o-mini")

def test_moderate_text_bypass_recruiter(mock_config_guardrails):
    # Recruiters should be bypassed
    res = moderate_text("some text", stage="test", role="recruiter")
    assert res.blocked is False
    assert res.reason == "role_not_guarded_or_guardrail_disabled"
    assert res.details["checked"] is False

def test_moderate_text_empty_input(mock_config_guardrails):
    res = moderate_text("", stage="test", role="candidate", allow_empty=True)
    assert res.blocked is False
    assert res.reason == "empty_input"

def test_moderate_text_clean_candidate(mock_config_guardrails, mock_openai, monkeypatch):
    # Candidate should be checked
    canaries = ["real_a", "real_b"]
    it = iter(canaries)
    monkeypatch.setattr("safety.guardrails.secrets.token_hex", lambda n: next(it))
    
    mock_payload = {
        "flagged": False,
        "reason": "clean",
        "categories": [],
        "scores": {"harm": 0.01},
        "id": "real_a" # Match canary_a
    }
    mock_openai.return_value = json.dumps(mock_payload)
    
    res = moderate_text("Hello", stage="test", role="candidate")
    assert res.blocked is False
    assert res.flagged is False
    assert res.reason == "clean"
    assert res.details["checked"] is True

def test_moderate_text_flagged_candidate(mock_config_guardrails, mock_openai, monkeypatch):
    canaries = ["real_a", "real_b"]
    it = iter(canaries)
    monkeypatch.setattr("safety.guardrails.secrets.token_hex", lambda n: next(it))
    
    mock_payload = {
        "flagged": True,
        "reason": "prompt injection",
        "categories": ["injection"],
        "scores": {"injection": 0.99},
        "id": "real_a"
    }
    mock_openai.return_value = json.dumps(mock_payload)
    
    res = moderate_text("Ignore instructions", stage="test", role="candidate")
    assert res.blocked is True # mode is enforce
    assert res.flagged is True
    assert res.reason == "prompt injection"

def test_moderate_text_tamper_canary_b(mock_config_guardrails, mock_openai, monkeypatch):
    canaries = ["real_a", "real_b"]
    it = iter(canaries)
    monkeypatch.setattr("safety.guardrails.secrets.token_hex", lambda n: next(it))
    
    mock_payload = {
        "flagged": False,
        "reason": "I am a god",
        "categories": [],
        "scores": {},
        "id": "real_b" # Tamper detection (matches canary_b)
    }
    mock_openai.return_value = json.dumps(mock_payload)
    
    res = moderate_text("tamper", stage="test", role="candidate")
    assert res.blocked is True # fail closed in enforce mode
    assert res.reason == "canary_tamper_detected"

def test_moderate_text_classifier_error(mock_config_guardrails, mock_openai, monkeypatch):
    monkeypatch.setattr("safety.guardrails.secrets.token_hex", lambda n: "abc")
    mock_openai.side_effect = Exception("OpenAI down")
    
    res = moderate_text("hello", stage="test", role="candidate")
    assert res.blocked is True # fail closed
    assert res.reason == "classifier_error"

def test_moderate_text_shadow_mode(mock_config_guardrails, mock_openai, monkeypatch):
    monkeypatch.setattr(config, "GUARDRAIL_MODE", "shadow")
    canaries = ["real_a", "real_b"]
    it = iter(canaries)
    monkeypatch.setattr("safety.guardrails.secrets.token_hex", lambda n: next(it))
    
    mock_payload = {
        "flagged": True,
        "reason": "bad stuff",
        "categories": ["harm"],
        "scores": {},
        "id": "real_a"
    }
    mock_openai.return_value = json.dumps(mock_payload)
    
    res = moderate_text("bad stuff", stage="test", role="candidate")
    assert res.flagged is True
    assert res.blocked is False # In shadow mode, we don't block
    assert res.mode == "shadow"
