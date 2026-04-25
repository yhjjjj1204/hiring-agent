import pytest
from unittest.mock import MagicMock
from langchain_core.outputs import LLMResult, Generation
from monitoring.token_callback import TokenUsageCallbackHandler
from uuid import uuid4

def test_token_callback_llm_output(monkeypatch):
    mock_record = MagicMock()
    monkeypatch.setattr("monitoring.token_callback.record_usage_with_context", mock_record)
    
    handler = TokenUsageCallbackHandler(username="alice", function_id="test")
    
    # Mock LLMResult with token_usage in llm_output
    res = LLMResult(
        generations=[],
        llm_output={"token_usage": {"prompt_tokens": 10, "completion_tokens": 5}}
    )
    
    handler.on_llm_end(res, run_id=uuid4())
    
    mock_record.assert_called_once_with(
        input_tokens=10,
        output_tokens=5,
        username="alice",
        function_id="test",
        default_function_id="unknown"
    )

def test_token_callback_generations(monkeypatch):
    mock_record = MagicMock()
    monkeypatch.setattr("monitoring.token_callback.record_usage_with_context", mock_record)
    
    handler = TokenUsageCallbackHandler()
    
    # Mock generation info style usage
    gen = Generation(text="hello", generation_info={"token_usage": {"prompt_tokens": 3, "completion_tokens": 2}})
    res = LLMResult(generations=[[gen]])
    
    handler.on_llm_end(res, run_id=uuid4())
    
    mock_record.assert_called_once_with(
        input_tokens=3,
        output_tokens=2,
        username=None,
        function_id=None,
        default_function_id="unknown"
    )
