import pytest
from unittest.mock import patch, MagicMock
import io
import sys
from agentic.common import Agent
from agentic.runner import RayAgentRunner

@pytest.fixture(autouse=True)
def mock_secrets():
    """Mock the secrets manager to avoid database issues"""
    with patch('agentic.agentic_secrets.agentic_secrets') as mock:
        mock.list_secrets.return_value = []
        mock.get_secret.return_value = None
        yield mock

@pytest.fixture
def test_agent():
    return Agent(
        name="Test Agent",
        welcome="Welcome to test agent",
        instructions="You are a test assistant.",
        tools=[],
        model="test-model"
    )

@pytest.fixture
def agent_runner(test_agent):
    return RayAgentRunner(test_agent)

def capture_output(func, *args, **kwargs):
    # Redirect stdout to capture output
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        func(*args, **kwargs)
    finally:
        sys.stdout = sys.__stdout__
    return captured_output.getvalue()

def test_dot_agent_command(agent_runner):
    output = capture_output(agent_runner.run_dot_commands, ".agent")
    assert "Test Agent" in output
    assert "You are a test assistant" in output
    assert "test-model" in output

def test_dot_debug_command(agent_runner):
    # Test setting debug level
    output = capture_output(agent_runner.run_dot_commands, ".debug llm")
    assert "Debug level set to: llm" in output
    
    # Test showing current debug level
    output = capture_output(agent_runner.run_dot_commands, ".debug")
    assert "Debug level set to: llm" in output

def test_dot_help_command(agent_runner):
    output = capture_output(agent_runner.run_dot_commands, ".help")
    assert ".agent" in output
    assert ".debug" in output
    assert ".help" in output
    assert "Current:" in output
    assert "Test Agent" in output

def test_dot_model_command(agent_runner):
    output = capture_output(agent_runner.run_dot_commands, ".model gpt-4")
    assert "Model set to gpt-4" in output

def test_dot_tools_command(agent_runner):
    output = capture_output(agent_runner.run_dot_commands, ".tools")
    assert "Test Agent" in output
    assert "tools:" in output

def test_dot_functions_command(agent_runner):
    output = capture_output(agent_runner.run_dot_commands, ".functions")
    assert "Test Agent" in output
    assert "functions:" in output

def test_dot_reset_command(agent_runner):
    # Mock the reset_history method
    agent_runner.facade.reset_history = MagicMock()
    output = capture_output(agent_runner.run_dot_commands, ".reset")
    assert "Session cleared" in output
    agent_runner.facade.reset_history.assert_called_once()

@pytest.fixture
def multi_agent_runner(test_agent):
    other_agent = Agent(
        name="Other Agent",
        welcome="Welcome to other agent",
        instructions="You are another test assistant.",
        tools=[]
    )
    # Add agents to registry
    from agentic.runner import _AGENT_REGISTRY
    _AGENT_REGISTRY.clear()
    _AGENT_REGISTRY.extend([test_agent, other_agent])
    return RayAgentRunner(test_agent)

def test_dot_run_command(multi_agent_runner):
    output = capture_output(multi_agent_runner.run_dot_commands, ".run other")
    assert "Switched to other" in output
    assert "Welcome to other agent" in output

def test_dot_history_command(agent_runner):
    # Mock the get_history method
    agent_runner.facade.get_history = MagicMock(return_value="Test history")
    output = capture_output(agent_runner.run_dot_commands, ".history")
    assert "Test history" in output

def test_unknown_dot_command(agent_runner):
    output = capture_output(agent_runner.run_dot_commands, ".unknown")
    assert "Unknown command" in output

def test_repl_loop_basic(agent_runner):
    with patch('agentic.runner.console.input') as mock_input:
        mock_input.side_effect = [".help", "quit"]
        with patch('readline.write_history_file'):  # Mock history file writing
            agent_runner.repl_loop()
            # Verify help was called
            mock_input.assert_called()
