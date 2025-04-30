import pytest
from datetime import datetime
from unittest.mock import Mock

from agentic.db.db_manager import DatabaseManager
from agentic.db.models import RunLog
from agentic.run_manager import RunManager
from agentic.common import RunContext
from agentic.events import (
    PromptStarted,
    FinishCompletion,
    ToolCall,
    ToolResult,
    TurnEnd
)
from litellm import Message

@pytest.fixture
def temp_db_path(tmp_path):
    """Create a temporary database path for testing."""
    return str(tmp_path / "test_runs.db")

@pytest.fixture
def db_manager(temp_db_path):
    """Create a database manager instance with test configuration."""
    return DatabaseManager(db_path=temp_db_path)

@pytest.fixture
def run_manager(temp_db_path):
    """Create a RunManager instance with test configuration."""
    return RunManager(db_path=temp_db_path)

@pytest.fixture
def run_context():
    """Create a RunContext for testing."""
    return RunContext(agent_name="test_agent", agent=Mock(), debug_level=None)

def test_create_run(db_manager):
    """Test creating a new run."""
    run = db_manager.create_run(
        agent_id="test_agent",
        user_id="test_user",
        initial_prompt="Test prompt",
        description="Test description"
    )
    
    assert run.id is not None
    assert run.agent_id == "test_agent"
    assert run.user_id == "test_user"
    assert run.initial_prompt == "Test prompt"
    assert run.description == "Test description"
    assert isinstance(run.created_at, datetime)
    assert isinstance(run.updated_at, datetime)
    assert run.usage_data == {}
    assert run.run_metadata == {}

def test_log_event(db_manager):
    """Test logging an event."""
    # First create a run
    run = db_manager.create_run(
        agent_id="test_agent",
        user_id="test_user",
        initial_prompt="Test prompt"
    )
    
    # Log an event
    log = db_manager.log_event(
        run_id=run.id,
        agent_id="test_agent",
        user_id="test_user",
        role="assistant",
        event_name="test_event",
        event_data={"test": "data"}
    )
    
    assert log.id is not None
    assert log.run_id == run.id
    assert log.agent_id == "test_agent"
    assert log.user_id == "test_user"
    assert log.role == "assistant"
    assert log.event_name == "test_event"
    assert log.event == {"test": "data"}
    assert isinstance(log.created_at, datetime)
    assert log.version == 1

def test_update_run(db_manager):
    """Test updating a run."""
    run = db_manager.create_run(
        agent_id="test_agent",
        user_id="test_user",
        initial_prompt="Test prompt"
    )
    
    updated_run = db_manager.update_run(
        run_id=run.id,
        description="Updated description",
        usage_data={"model": "test-model", "tokens": 100},
        run_metadata={"key": "value"}
    )
    
    assert updated_run is not None
    assert updated_run.description == "Updated description"
    assert updated_run.usage_data == {"model": "test-model", "tokens": 100}
    assert updated_run.run_metadata == {"key": "value"}
    assert updated_run.updated_at > run.updated_at

def test_get_run(db_manager):
    """Test retrieving a run."""
    created_run = db_manager.create_run(
        agent_id="test_agent",
        user_id="test_user",
        initial_prompt="Test prompt"
    )
    
    retrieved_run = db_manager.get_run(created_run.id)
    assert retrieved_run is not None
    assert retrieved_run.id == created_run.id
    assert retrieved_run.agent_id == created_run.agent_id

def test_get_run_logs(db_manager):
    """Test retrieving logs for a run."""
    run = db_manager.create_run(
        agent_id="test_agent",
        user_id="test_user",
        initial_prompt="Test prompt"
    )
    
    # Create multiple logs
    for i in range(3):
        db_manager.log_event(
            run_id=run.id,
            agent_id="test_agent",
            user_id="test_user",
            role="assistant",
            event_name=f"test_event_{i}",
            event_data={"test": f"data_{i}"}
        )
    
    logs = db_manager.get_run_logs(run.id)
    assert len(logs) == 3
    assert all(isinstance(log, RunLog) for log in logs)
    assert all(log.run_id == run.id for log in logs)

def test_get_runs_by_user(db_manager):
    """Test retrieving runs for a specific user."""
    # Create runs for different users
    user1_runs = [
        db_manager.create_run(
            agent_id="test_agent",
            user_id="user1",
            initial_prompt=f"Test prompt {i}"
        )
        for i in range(2)
    ]
    
    user2_run = db_manager.create_run(
        agent_id="test_agent",
        user_id="user2",
        initial_prompt="Test prompt"
    )
    
    retrieved_runs = db_manager.get_runs_by_user("user1")
    assert len(retrieved_runs) == 2
    assert all(run.user_id == "user1" for run in retrieved_runs)

def test_get_runs_by_agent(db_manager):
    """Test retrieving runs for a specific agent."""
    # Create runs for different agents
    agent1_runs = [
        db_manager.create_run(
            agent_id="agent1",
            user_id="test_user",
            initial_prompt=f"Test prompt {i}"
        )
        for i in range(2)
    ]
    
    agent2_run = db_manager.create_run(
        agent_id="agent2",
        user_id="test_user",
        initial_prompt="Test prompt"
    )
    
    retrieved_runs = db_manager.get_runs_by_agent("agent1", user_id=None)
    assert len(retrieved_runs) == 2
    assert all(run.agent_id == "agent1" for run in retrieved_runs)

def test_run_manager_handle_events(db_manager, run_manager, run_context):
    """Test RunManager event handling."""
    # Test handling PromptStarted event
    prompt_event = PromptStarted(agent="test_agent", message="Test prompt")
    run_manager.handle_event(prompt_event, run_context)
    assert run_manager.current_run_id is not None
    
    # Test handling FinishCompletion event
    completion_event = FinishCompletion.create(
        agent="test_agent",
        llm_message=Message(content="Test response", role="assistant"),
        model="test-model",
        cost=0.001,
        input_tokens=10,
        output_tokens=20,
        elapsed_time=1.0
    )
    run_manager.handle_event(completion_event, run_context)
    
    # Test handling tool events
    tool_call = ToolCall(agent="test_agent", name="test_tool", arguments={"arg": "value"})
    run_manager.handle_event(tool_call, run_context)
    
    tool_result = ToolResult(agent="test_agent", name="test_tool", result="success")
    run_manager.handle_event(tool_result, run_context)
    
    # Test handling TurnEnd event
    turn_end = TurnEnd(agent="test_agent", messages=[], run_context=run_context)
    run_manager.handle_event(turn_end, run_context)
    
    # Verify logs were created
    logs = db_manager.get_run_logs(run_manager.current_run_id)
    assert len(logs) > 0
    
    # Verify usage data was tracked
    run = db_manager.get_run(run_manager.current_run_id)
    assert "test-model" in run.usage_data
    assert run.usage_data["test-model"]["input_tokens"] == 10
    assert run.usage_data["test-model"]["output_tokens"] == 20
