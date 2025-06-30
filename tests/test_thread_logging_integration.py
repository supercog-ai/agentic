import pytest
from datetime import datetime

from agentic.common import Agent, AgentRunner
from agentic.db.db_manager import DatabaseManager
from agentic.thread_manager import init_thread_tracking, disable_thread_tracking, reconstruct_chat_history_from_thread_logs


class SimpleCalculator:
    def get_tools(self):
        return [
            self.add,
            self.subtract
        ]

    def add(self, a: float, b: float) -> str:
        """Add two numbers"""
        return str(float(a) + float(b))
        
    def subtract(self, a: float, b: float) -> str:
        """Subtract b from a"""
        return str(float(a) - float(b))

@pytest.fixture
def temp_db_path(tmp_path):
    """Create a temporary database path for testing."""
    return str(tmp_path / "test_threads.db")

@pytest.fixture
def db_manager(temp_db_path):
    """Create a database manager instance with test configuration."""
    return DatabaseManager(db_path=temp_db_path)

@pytest.fixture
def test_agent(temp_db_path):
    """Create a simple test agent with basic math capabilities."""
    agent = Agent(
        name="Calculator",
        instructions="""You are a helpful calculator assistant. Use the provided tools to perform calculations.
        Always explain your work before using a tool.""",
        tools=[SimpleCalculator()],
        model="gpt-4o",
        db_path=temp_db_path
    )
    return agent

@pytest.mark.requires_llm
def test_thread_logging_enabled(test_agent, db_manager):
    """Test that thread logging works correctly when enabled."""
    runner = AgentRunner(test_agent)
    
    # Run a simple calculation
    runner.turn("What is 5 plus 3? Use your functions")
    
    # Verify the thread was created
    threads = db_manager.get_threads_by_user("default")
    assert len(threads) == 1
    thread = threads[0]
    initial_thread_logs_count = len(db_manager.get_thread_logs(thread.id))
    
    # Verify thread metadata
    assert thread.agent_id == "Calculator"
    assert thread.user_id == "default"
    assert thread.initial_prompt == "What is 5 plus 3? Use your functions"
    assert isinstance(thread.created_at, datetime)
    assert isinstance(thread.updated_at, datetime)
    
    # Get all logs for this thread
    logs = db_manager.get_thread_logs(thread.id)
    
    # Verify essential events were logged
    event_names = [log.event_name for log in logs]
    assert 'prompt_started' in event_names
    assert 'completion_end' in event_names
    assert 'tool_call' in event_names
    assert 'tool_result' in event_names
    assert 'turn_end' in event_names
    
    # Verify tool usage was logged correctly
    tool_calls = [log for log in logs if log.event_name == 'tool_call']
    assert len(tool_calls) > 0
    assert tool_calls[0].event['name'] == 'add'
    
    # Verify token usage was tracked
    assert any('input_tokens' in log.event.get('usage', {})
                for log in logs if log.event_name == 'completion_end')
    
    # Run another calculation to verify multiple runs are tracked
    runner.turn("What is 10 minus 4?")
    
    threads = db_manager.get_threads_by_user("default")
    new_thread_logs_count = len(db_manager.get_thread_logs(thread.id))
    # Make sure the length of threads is one but that the number of thread logs increased
    assert len(threads) == 1
    assert new_thread_logs_count > initial_thread_logs_count

@pytest.mark.requires_llm
def test_thread_logging_disabled(db_manager):
    """Test that no logging occurs when thread logging is disabled."""
    # Disable thread tracking
    no_logging_agent = Agent(
        name="Calculator",
        instructions="""You are a helpful calculator assistant. Use the provided tools to perform calculations.
        Always explain your work before using a tool.""",
        tools=[SimpleCalculator()],
        model="gpt-4o-mini",
        db_path=None
    )
    runner = AgentRunner(no_logging_agent)
    
    # Run a calculation
    runner.turn("What is 7 plus 2?")
    
    # Verify no threads were created
    threads = db_manager.get_threads_by_agent("Calculator", user_id=None)
    assert len(threads) == 0
    
    # Run another calculation
    runner.turn("What is 15 minus 5?")
    
    # Verify still no threads
    threads = db_manager.get_threads_by_agent("Calculator", user_id=None)
    assert len(threads) == 0

@pytest.mark.skip("Disabling isn't supported since the Threaded agent refactor")
def test_run_logging_toggle(test_agent, db_manager, temp_db_path):
    """Test that logging can be toggled on and off."""    
    runner = AgentRunner(test_agent)
    
    # Start with logging disabled
    disable_thread_tracking(test_agent)
    runner.turn("What is 3 plus 4?")
    
    threads = db_manager.get_threads_by_agent("Calculator", user_id=None)
    assert len(threads) == 0
    
    # Enable logging
    init_thread_tracking(test_agent, db_path=temp_db_path)
    runner.turn("What is 8 minus 5?")
    
    threads = db_manager.get_threads_by_agent("Calculator", user_id=None)
    assert len(threads) == 1
    
    # Disable logging again
    disable_thread_tracking(test_agent)
    runner.turn("What is 6 plus 7?")
    
    threads = db_manager.get_threads_by_agent("Calculator")
    assert len(threads) == 1  # Count should not have increased

def agent_turn(agent: Agent, request: str, thread_id: str=None) -> tuple[str, str]:
    """Run a turn with the agent and return the response and the thread_id."""
    results = []
    request_id = agent.start_request(
        request, 
        thread_id=thread_id,
    ).request_id
    for event in agent.get_events(request_id):
        if event.type == "chat_output":
            results.append(str(event))
    return "".join(results), agent.thread_id

@pytest.mark.requires_llm
def test_reload_history_from_thread_log(test_agent, db_manager):
    """Test that Agent will reload its history if we pass the same thread_id into a new request."""
    def get_weather() -> str:
        """Get the current weather report."""
        return "It's sunny and 75 degrees."
    
    test_agent.add_tool(get_weather)

    # Run a simple calculation
    res, thread_id = agent_turn(test_agent, "my name is Scott. Can you get the weather report?")
    agent_turn(test_agent, "Remember my favorite color is cyan.")
       
    # Verify the thread was created
    threads = db_manager.get_threads_by_user("default")
    assert len(threads) == 1

    # Make a new instance of the agent, without the history
    new_agent = test_agent.__class__(**test_agent.agent_config)

    result = agent_turn(new_agent, "What is my name and my favorite color?")[0]
    assert "Scott" not in result
    assert "cyan" not in result

    # Now pass in the thread_id to reload the history
    agent3 = test_agent.__class__(**test_agent.agent_config)
    
    result = agent_turn(agent3, "What is my name and my favorite color?", thread_id=thread_id)[0]

    assert "Scott" in result
    assert "cyan" in result
