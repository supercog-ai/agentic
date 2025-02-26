import pytest
from agentic.common import Agent, AgentRunner
from agentic.models import set_mock_default_response
import litellm
from src.agentic.custom_models.mock_provider import MockModelProvider
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