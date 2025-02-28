import pytest
import ray
from typing import Dict, Any
from agentic.vendor_agents import LangGraphAgent
from agentic.events import Prompt, PromptStarted, ChatOutput, TurnEnd

class MockGraph:
    async def astream(self, input_data: Dict[str, Any]):
        # Simulate LangGraph stream response
        yield {"output": {"messages": [{"content": "Test response"}]}}

@pytest.mark.asyncio
async def test_langgraph_agent():
    # Initialize Ray if not already running
    if not ray.is_initialized():
        ray.init()
    
    # Create agent instance
    agent = LangGraphAgent.remote()
    
    # Configure with mock graph
    await agent.configure_agent.remote({"graph": MockGraph()})
    
    # Start agent
    await agent.start.remote()
    
    # Create test prompt
    prompt = Prompt("test", "Hello", depth=0)
    
    # Run agent and collect events
    events = []
    async for event in agent.handlePromptOrResume.remote(prompt):
        events.append(ray.get(event))
    
    # Verify events
    assert len(events) == 3
    assert isinstance(events[0], PromptStarted)
    assert isinstance(events[1], ChatOutput)
    assert isinstance(events[2], TurnEnd)
    assert events[1].content == {"content": "Test response"}
    
    # Stop agent
    await agent.stop.remote()

@pytest.mark.asyncio
async def test_langgraph_agent_errors():
    if not ray.is_initialized():
        ray.init()
        
    agent = LangGraphAgent.remote()
    
    # Test missing graph configuration
    with pytest.raises(ValueError):
        await agent.configure_agent.remote({})
    
    # Test running without starting
    prompt = Prompt("test", "Hello", depth=0)
    with pytest.raises(RuntimeError):
        async for _ in agent.run.remote({"messages": [{"role": "user", "content": "test"}]}):
            pass
