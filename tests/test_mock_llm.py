import pytest
from agentic.common import Agent, AgentRunner
from agentic.models import set_mock_default_response


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