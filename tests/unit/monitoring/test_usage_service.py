import pytest
from monitoring.usage_service import record_usage, record_openai_usage
from unittest.mock import MagicMock

def test_record_usage(mock_get_database):
    # Execute
    record_usage(
        username="testuser",
        function_id="testfunc",
        input_tokens=10,
        output_tokens=20,
        user_role="recruiter"
    )
    
    # Assert
    mock_get_database.token_usage.update_one.assert_called_once()
    args, kwargs = mock_get_database.token_usage.update_one.call_args
    assert args[0]["username"] == "testuser"
    assert args[0]["function"] == "testfunc"
    assert args[1]["$inc"]["input_tokens"] == 10
    assert args[1]["$inc"]["output_tokens"] == 20

def test_record_openai_usage(mock_get_database, monkeypatch):
    # Setup context
    from monitoring.context import current_username, current_function_id
    current_username.set("alice")
    current_function_id.set("ocr")
    
    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 5
    mock_usage.completion_tokens = 15
    
    # Execute
    record_openai_usage(mock_usage)
    
    # Assert
    mock_get_database.token_usage.update_one.assert_called_once()
    args, kwargs = mock_get_database.token_usage.update_one.call_args
    assert args[0]["username"] == "alice"
    assert args[1]["$inc"]["input_tokens"] == 5
