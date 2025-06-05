import pytest
from datetime import datetime
from unittest.mock import Mock

from agentic.db.db_manager import DatabaseManager
from agentic.db.models import ThreadLog
from agentic.thread_manager import ThreadManager
from agentic.common import ThreadContext
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
    return str(tmp_path / "test_threads.db")

@pytest.fixture
def db_manager(temp_db_path):
    """Create a database manager instance with test configuration."""
    return DatabaseManager(db_path=temp_db_path)

@pytest.fixture
def thread_manager(temp_db_path):
    """Create a ThreadManager instance with test configuration."""
    return ThreadManager(db_path=temp_db_path)

@pytest.fixture
def thread_context():
    """Create a ThreadContext for testing."""
    return ThreadContext(agent_name="test_agent", agent=Mock(), debug_level=None)

def test_create_thread(db_manager):
    """Test creating a new thread."""
    thread = db_manager.create_thread(
        agent_id="test_agent",
        user_id="test_user",
        initial_prompt="Test prompt",
        description="Test description"
    )
    
    assert thread.id is not None
    assert thread.agent_id == "test_agent"
    assert thread.user_id == "test_user"
    assert thread.initial_prompt == "Test prompt"
    assert thread.description == "Test description"
    assert isinstance(thread.created_at, datetime)
    assert isinstance(thread.updated_at, datetime)
    assert thread.usage_data == {}
    assert thread.thread_metadata == {}

def test_log_event(db_manager):
    """Test logging an event."""
    # First create a thread
    thread = db_manager.create_thread(
        agent_id="test_agent",
        user_id="test_user",
        initial_prompt="Test prompt"    
    )
    
    # Log an event
    log = db_manager.log_event(
        thread_id=thread.id,
        agent_id="test_agent",
        user_id="test_user",
        role="assistant",
        event_name="test_event",
        event_data={"test": "data"}
    )
    
    assert log.id is not None
    assert log.thread_id == thread.id
    assert log.agent_id == "test_agent"
    assert log.user_id == "test_user"
    assert log.role == "assistant"
    assert log.event_name == "test_event"
    assert log.event == {"test": "data"}
    assert isinstance(log.created_at, datetime)
    assert log.version == 1

def test_update_thread(db_manager):
    """Test updating a thread."""
    thread = db_manager.create_thread(
        agent_id="test_agent",
        user_id="test_user",
        initial_prompt="Test prompt"
    )
    
    updated_thread = db_manager.update_thread(
        thread_id=thread.id,
        description="Updated description",
        usage_data={"model": "test-model", "tokens": 100},
        thread_metadata={"key": "value"}
    )
    
    assert updated_thread is not None
    assert updated_thread.description == "Updated description"
    assert updated_thread.usage_data == {"model": "test-model", "tokens": 100}
    assert updated_thread.thread_metadata == {"key": "value"}
    assert updated_thread.updated_at > thread.updated_at

def test_get_thread(db_manager):
    """Test retrieving a thread."""
    created_thread = db_manager.create_thread(
        agent_id="test_agent",
        user_id="test_user",
        initial_prompt="Test prompt"
    )
    
    retrieved_thread = db_manager.get_thread(created_thread.id)
    assert retrieved_thread is not None
    assert retrieved_thread.id == created_thread.id
    assert retrieved_thread.agent_id == created_thread.agent_id

def test_get_thread_logs(db_manager):
    """Test retrieving logs for a thread."""
    thread = db_manager.create_thread(
        agent_id="test_agent",
        user_id="test_user",
        initial_prompt="Test prompt"
    )
    
    # Create multiple logs
    for i in range(3):
        db_manager.log_event(
            thread_id=thread.id,
            agent_id="test_agent",
            user_id="test_user",
            role="assistant",
            event_name=f"test_event_{i}",
            event_data={"test": f"data_{i}"}
        )
    
    logs = db_manager.get_thread_logs(thread.id)
    assert len(logs) == 3
    assert all(isinstance(log, ThreadLog) for log in logs)
    assert all(log.thread_id == thread.id for log in logs)

def test_get_threads_by_user(db_manager):
    """Test retrieving threads for a specific user."""
    # Create threads for different users
    user1_threads = [
        db_manager.create_thread(
            agent_id="test_agent",
            user_id="user1",
            initial_prompt=f"Test prompt {i}"
        )
        for i in range(2)
    ]
    
    user2_thread = db_manager.create_thread(
        agent_id="test_agent",
        user_id="user2",
        initial_prompt="Test prompt"
    )
    
    retrieved_threads = db_manager.get_threads_by_user("user1")
    assert len(retrieved_threads) == 2
    assert all(thread.user_id == "user1" for thread in retrieved_threads)

def test_get_threads_by_agent(db_manager):
    """Test retrieving threads for a specific agent."""
    # Create threads for different agents
    agent1_threads = [
        db_manager.create_thread(
            agent_id="agent1",
            user_id="test_user",
            initial_prompt=f"Test prompt {i}"
        )
        for i in range(2)
    ]
    
    agent2_thread = db_manager.create_thread(
        agent_id="agent2",
        user_id="test_user",
        initial_prompt="Test prompt"
    )
    
    retrieved_threads = db_manager.get_threads_by_agent("agent1", user_id=None)
    assert len(retrieved_threads) == 2
    assert all(thread.agent_id == "agent1" for thread in retrieved_threads)

def test_thread_manager_handle_events(db_manager, thread_manager, thread_context):
    """Test ThreadManager event handling."""
    # Test handling PromptStarted event
    prompt_event = PromptStarted(agent="test_agent", message="Test prompt")
    thread_manager.handle_event(prompt_event, thread_context)
    assert thread_manager.current_thread_id is not None
    
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
    thread_manager.handle_event(completion_event, thread_context)
    
    # Test handling tool events
    tool_call = ToolCall(agent="test_agent", name="test_tool", arguments={"arg": "value"})
    thread_manager.handle_event(tool_call, thread_context)
    
    tool_result = ToolResult(agent="test_agent", name="test_tool", result="success")
    thread_manager.handle_event(tool_result, thread_context)
    
    # Test handling TurnEnd event
    turn_end = TurnEnd(agent="test_agent", messages=[], thread_context=thread_context)
    thread_manager.handle_event(turn_end, thread_context)
    
    # Verify logs were created
    logs = db_manager.get_thread_logs(thread_manager.current_thread_id)
    assert len(logs) > 0
    
    # Verify usage data was tracked
    thread = db_manager.get_thread(thread_manager.current_thread_id)
    assert "test-model" in thread.usage_data
    assert thread.usage_data["test-model"]["input_tokens"] == 10
    assert thread.usage_data["test-model"]["output_tokens"] == 20
