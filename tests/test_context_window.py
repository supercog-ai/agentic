import pytest
from agentic.common import Agent, AgentRunner

def generate_large_text(base_text="This is a test message. ", repetitions=10):
    """Generate text with a predictable token count"""
    return base_text * repetitions

@pytest.mark.requires_llm
def test_context_compression():
    """Test that context window compression allows agent to continue functioning with very large inputs"""
    # Create agent with smaller context window model
    agent = Agent(
        name="Context Test Agent",
        instructions="You are a helpful assistant that gives very brief responses. Your name is Context Test Agent.",
        model="gpt-3.5-turbo",  # Smaller context window than gpt-4
        tools=[]
    )
    
    # First message - normal size
    agent_runner = AgentRunner(agent)
    response = agent_runner.run("Hello, who are you?")
    assert response, "Agent should respond to initial message"
    
    for i in range(10):
        # Send extremely large message that should exceed context window
        # This will be around 10,000 tokens, large enough to trigger compression for gpt-3.5-turbo
        large_text = generate_large_text(repetitions=2500)
        prompt = f"Here's a lot of text: {large_text}. Ignore all that and just tell me your name."
        
        # This should trigger context compression internally
        response = agent_runner.run(prompt)
        
        # Check if we got a coherent response
        assert response, "Agent should respond despite large input"
        assert "Context Test Agent" in response, "Agent should remember its identity after handling large context"
    
    # Final check - agent should still be functional after handling large input
    response = agent_runner.run("What's your name again?")
    assert "Context Test Agent" in response, "Agent should maintain identity after processing large context" 