import pytest
from unittest.mock import MagicMock
from monitoring.registry import AgentMonitorRegistry, RunRecord, StepRecord

def test_registry_start_run():
    registry = AgentMonitorRegistry()
    registry.start_run("thread1", meta={"user": "alice"})
    
    run = registry.get_run_record("thread1")
    assert run.thread_id == "thread1"
    assert run.meta["user"] == "alice"

def test_registry_steps(monkeypatch):
    # Mock database recording called in end_step
    monkeypatch.setattr("monitoring.registry.record_usage_with_context", MagicMock())
    
    registry = AgentMonitorRegistry()
    registry.begin_step("thread1", "agent1")
    
    run = registry.get_run_record("thread1")
    assert run.current_agent_id == "agent1"
    assert run.path[0].agent_id == "agent1"
    assert run.path[0].status == "running"
    
    registry.end_step("thread1", "agent1", ok=True)
    assert run.path[0].status == "completed"

def test_registry_max_runs():
    registry = AgentMonitorRegistry(max_runs=2)
    registry.start_run("1")
    registry.start_run("2")
    registry.start_run("3")
    
    assert registry.get_run_record("1") is None
    assert registry.get_run_record("2") is not None
    assert registry.get_run_record("3") is not None

def test_registry_snapshot():
    registry = AgentMonitorRegistry()
    registry.start_run("thread1")
    registry.begin_step("thread1", "agent1")
    
    snap = registry.snapshot()
    assert len(snap["runs"]) == 1
    assert snap["runs"][0]["thread_id"] == "thread1"
    assert snap["runs"][0]["current_agent_id"] == "agent1"
