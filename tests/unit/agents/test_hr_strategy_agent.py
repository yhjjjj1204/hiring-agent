import pytest
import json
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from agents.hr_strategy.graph import _agent_node, _route_after_agent, _capture_spec_node, HRStrategyState
from langgraph.graph import END

def test_route_after_agent_to_end():
    state: HRStrategyState = {"messages": [AIMessage(content="Hello")]}
    assert _route_after_agent(state) == END

def test_route_after_agent_to_tools():
    tool_call = {"name": "finalize_hr_job_spec", "args": {}, "id": "1"}
    state: HRStrategyState = {"messages": [AIMessage(content="", tool_calls=[tool_call])]}
    assert _route_after_agent(state) == "tools"

def test_agent_node(mock_chat_openai, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    
    mock_reply = AIMessage(content="I can help with that.")
    mock_chat_openai.bind_tools.return_value.invoke.return_value = mock_reply
    
    state: HRStrategyState = {"messages": [HumanMessage(content="Hi")]}
    res = _agent_node(state)
    
    assert res["messages"][0].content == "I can help with that."

def test_capture_spec_node():
    spec_data = {
        "role_title": "Engineer",
        "summary": "Build stuff",
        "required_skills": [{"name": "Python", "minimum_level": "expert"}],
        "culture_fit_metrics": [{"name": "collaboration", "description": "nice"}]
    }
    tool_msg = ToolMessage(
        content=json.dumps(spec_data),
        tool_call_id="1",
        name="finalize_hr_job_spec"
    )
    state: HRStrategyState = {"messages": [tool_msg]}
    
    res = _capture_spec_node(state)
    
    assert res["completed_spec"]["role_title"] == "Engineer"
    assert "Structured job requirements" in res["messages"][0].content

def test_capture_spec_node_invalid_json():
    tool_msg = ToolMessage(
        content="not json",
        tool_call_id="1",
        name="finalize_hr_job_spec"
    )
    state: HRStrategyState = {"messages": [tool_msg]}
    res = _capture_spec_node(state)
    assert "completed_spec" not in res
