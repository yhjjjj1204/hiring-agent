import pytest
from unittest.mock import MagicMock, patch
from monitoring.pipeline_hooks import monitored_node

def test_monitored_node_success(monkeypatch):
    mock_mon = MagicMock()
    monkeypatch.setattr("monitoring.pipeline_hooks.get_monitor", lambda: mock_mon)
    monkeypatch.setattr("monitoring.pipeline_hooks._thread_id", lambda: "thread1")
    
    def my_node(state):
        return {"result": "ok"}
    
    wrapped = monitored_node("agent1", my_node)
    res = wrapped({"input": "test"})
    
    assert res["result"] == "ok"
    assert mock_mon.begin_step.called
    assert mock_mon.end_step.called
    args = mock_mon.end_step.call_args[1]
    assert args["ok"] is True

def test_monitored_node_failure(monkeypatch):
    mock_mon = MagicMock()
    monkeypatch.setattr("monitoring.pipeline_hooks.get_monitor", lambda: mock_mon)
    monkeypatch.setattr("monitoring.pipeline_hooks._thread_id", lambda: "thread1")
    
    def failing_node(state):
        raise ValueError("fail")
    
    wrapped = monitored_node("agent1", failing_node)
    with pytest.raises(ValueError):
        wrapped({})
    
    assert mock_mon.end_step.called
    args = mock_mon.end_step.call_args[1]
    assert args["ok"] is False
    assert args["error"] == "ValueError"
