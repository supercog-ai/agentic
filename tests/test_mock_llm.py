import pytest
from agentic.common import Agent, AgentRunner
from agentic.models import set_mock_default_response, register_mock_tool, mock_provider


def test_mock_llm_response():
    """Test that an agent using a mock model returns the expected response"""
    
    set_mock_default_response("That is a great question!")

    agent = Agent(
        name="MockAgent",
        instructions="You are a helpful assistant.",
        model="mock/default"
    )
    
    # Send a message to the agent
    agent_runner = AgentRunner(agent)
    response = agent_runner.turn("What time is it right now?")
    
    # Verify the response
    assert response == "That is a great question!"

def test_mock_llm_pattern_matching():
    """Test that pattern matching in mock responses works"""
    
    set_mock_default_response("my name is (\w+)", "Hello, $1!")

    agent = Agent(
        name="MockAgent",
        instructions="You are a helpful assistant.",
        model="mock/default"
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
    
    # Explicitly register the tool with the mock provider
    mock_provider.clear_tools()  # Clear any previous tools
    register_mock_tool(convert_to_pdf)
    
    # Create an agent with our test function as a tool
    agent = Agent(
        name="MockAgent",
        instructions="You are a helpful assistant.",
        model="mock/default",
        tools=[convert_to_pdf]
    )
    
    # Send a message requesting to call the function
    agent_runner = AgentRunner(agent)
    response = agent_runner.turn("call the function convert_to_pdf with filename=output.txt")
    
    # Verify the response contains the function output
    assert "output.txt is converted to PDF" in response