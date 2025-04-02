import pytest
from agentic.common import Agent, AgentRunner
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_secrets():
    """Mock the secrets manager to avoid database issues"""
    with patch('agentic.agentic_secrets.agentic_secrets') as mock:
        mock.list_secrets.return_value = []
        mock.get_secret.return_value = None
        yield mock

def test_mock_llm_response():
    """Test that an agent using a mock model returns the expected response"""
    
    agent = Agent(
        name="MockAgent",
        instructions="You are a helpful assistant.",
        model="mock/default",
        mock_settings={
            "response": "That is a great question!"
        }
    )
    
    # Send a message to the agent
    agent_runner = AgentRunner(agent)
    response = agent_runner.turn("What time is it right now?")
    
    # Verify the response
    assert response == "That is a great question!"

def test_mock_llm_pattern_matching():
    """Test that pattern matching in mock responses works"""
    
    agent = Agent(
        name="MockAgent",
        instructions="You are a helpful assistant.",
        model="mock/default",
        mock_settings={
            "pattern": "my name is (\w+)",
            "response": "Hello, $1!"
        }
    )
    
    # Send a message to the agent
    agent_runner = AgentRunner(agent)
    response = agent_runner.turn("my name is Richard")
    
    # Verify the response
    assert response == "Hello, Richard!"

def test_mock_llm_tool_calling():
    """Test that the mock provider can detect and execute function calls"""
    
    # Define a simple test function
    def convert_to_pdf(filename):
        """Convert a file to PDF format"""
        return f"{filename} is converted to PDF."
    
    # Pass the tool directly in mock_settings
    agent = Agent(
        name="MockAgent",
        instructions="You are a helpful assistant.",
        model="mock/default",
        tools=[convert_to_pdf],
        mock_settings={
            "tools": {"convert_to_pdf": convert_to_pdf}
        }
    )
    
    # Send a message requesting to call the function
    agent_runner = AgentRunner(agent)
    response = agent_runner.turn("call the function convert_to_pdf with filename=output.txt")
    
    # Verify the response contains the function output
    assert "output.txt is converted to PDF" in response