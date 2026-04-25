import pytest
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from agents.hr_strategy.messages_io import messages_to_records, records_to_messages

def test_serialization_cycle():
    messages = [
        HumanMessage(content="Hello"),
        AIMessage(content="", tool_calls=[{"name": "test", "args": {}, "id": "1"}]),
        ToolMessage(content="done", tool_call_id="1", name="test")
    ]
    
    records = messages_to_records(messages)
    assert len(records) == 3
    assert records[0]["type"] == "human"
    assert "tool_calls" in records[1]
    assert records[2]["type"] == "tool"
    
    back = records_to_messages(records)
    assert len(back) == 3
    assert isinstance(back[0], HumanMessage)
    assert isinstance(back[1], AIMessage)
    assert len(back[1].tool_calls) == 1
    assert isinstance(back[2], ToolMessage)
    assert back[2].name == "test"
