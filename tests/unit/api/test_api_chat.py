import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from api.routes_chat import run_chat_logic
from api.auth_models import User
from langchain_core.messages import AIMessage, HumanMessage

@pytest.fixture
def mock_usage_recording(monkeypatch):
    mock_record = MagicMock()
    monkeypatch.setattr("monitoring.usage_service.record_openai_usage", mock_record)
    return mock_record

@pytest.mark.asyncio
async def test_run_chat_logic_simple_reply(mock_get_database, recruiter_user, mock_chat_openai, monkeypatch, mock_usage_recording):
    # Setup
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    mock_get_database.chat_history.find.return_value.sort.return_value = []
    
    # Mock safety check
    mock_moderate = MagicMock()
    mock_moderate.blocked = False
    monkeypatch.setattr("api.routes_chat.moderate_text", lambda *args, **kwargs: mock_moderate)
    
    # Mock LLM reply
    mock_chat_openai.invoke.return_value = AIMessage(content="Hello! How can I help you today?")
    
    # Mock send_func
    send_func = AsyncMock()
    
    # Execute
    await run_chat_logic(
        user_message="Hi",
        context={},
        context_labels={},
        current_user=recruiter_user,
        background_tasks=MagicMock(),
        send_func=send_func
    )
    
    # Assert
    calls = [call.args[0] for call in send_func.call_args_list]
    assert {"status": "Thinking..."} in calls
    # Find the reply call
    reply_call = next((c for c in calls if "reply" in c), None)
    assert reply_call is not None
    assert "Hello! How can I help you today?" in reply_call["reply"]

@pytest.mark.asyncio
async def test_run_chat_logic_tool_call(mock_get_database, recruiter_user, mock_chat_openai, monkeypatch, mock_usage_recording):
    # Setup
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    mock_get_database.chat_history.find.return_value.sort.return_value = []
    
    # Mock safety check
    mock_moderate = MagicMock()
    mock_moderate.blocked = False
    monkeypatch.setattr("api.routes_chat.moderate_text", lambda *args, **kwargs: mock_moderate)
    
    # Mock first LLM call with a tool call
    mock_tool_call = {
        "name": "list_jobs",
        "args": {},
        "id": "call_1"
    }
    mock_chat_openai.bind_tools.return_value.invoke.return_value = AIMessage(content="", tool_calls=[mock_tool_call])
    
    # Mock second LLM call with final answer
    mock_chat_openai.invoke.return_value = AIMessage(content="Here are the jobs: [[JOB:1]]")
    
    # Mock list_jobs service
    monkeypatch.setattr("api.routes_chat.list_jobs", lambda u: [{"id": "1", "title": "Dev"}])
    
    send_func = AsyncMock()
    
    # Execute
    await run_chat_logic(
        user_message="List jobs",
        context={},
        context_labels={},
        current_user=recruiter_user,
        background_tasks=MagicMock(),
        send_func=send_func
    )
    
    # Assert
    calls = [call.args[0] for call in send_func.call_args_list]
    assert {"status": "Calling Tools..."} in calls
    reply_call = next((c for c in calls if "reply" in c), None)
    assert reply_call is not None
    assert "[[JOB:1]]" in reply_call["reply"]

@pytest.mark.asyncio
async def test_run_chat_logic_blocked_input(mock_get_database, candidate_user, monkeypatch):
    # Mock safety check to block
    mock_moderate = MagicMock()
    mock_moderate.blocked = True
    monkeypatch.setattr("api.routes_chat.moderate_text", lambda *args, **kwargs: mock_moderate)
    
    send_func = AsyncMock()
    
    await run_chat_logic(
        user_message="bad message",
        context={},
        context_labels={},
        current_user=candidate_user,
        background_tasks=MagicMock(),
        send_func=send_func
    )
    
    send_func.assert_called_once_with({"reply": "Your message cannot be processed due to safety policy. Please rephrase and try again."})
