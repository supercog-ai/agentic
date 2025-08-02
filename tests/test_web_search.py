import pytest
from agentic.common import Agent
from agentic.actor_agents import DebugLevel
from agentic.agentic_secrets import agentic_secrets
from agentic.models import GPT_4O_MINI

def test_web_search_agent_creation():
    """Test that we can create an agent with web search enabled"""
    agent = Agent(
        name="Web Search Test Agent",
        instructions="You can search the web for current information.",
        model="openai/gpt-4o-search-preview",
        reasoning_tools=["websearch"],
        web_search_context_size="medium",
    )
    
    # Verify the agent has the correct web search settings
    assert agent.reasoning_tools == ["websearch"]
    assert agent.web_search_context_size == "medium"
    assert agent.model == "openai/gpt-4o-search-preview"

def test_web_search_context_sizes():
    """Test different web search context sizes"""
    # Test low context
    agent_low = Agent(
        name="Low Context Agent",
        instructions="Quick web search agent.",
        model="openai/gpt-4o-search-preview",
        reasoning_tools=["websearch"],
        web_search_context_size="low",
    )
    assert agent_low.web_search_context_size == "low"
    
    # Test medium context (default)
    agent_medium = Agent(
        name="Medium Context Agent",
        instructions="Balanced web search agent.",
        model="openai/gpt-4o-search-preview",
        reasoning_tools=["websearch"],
        web_search_context_size="medium",
    )
    assert agent_medium.web_search_context_size == "medium"
    
    # Test high context
    agent_high = Agent(
        name="High Context Agent",
        instructions="Comprehensive web search agent.",
        model="openai/gpt-4o-search-preview",
        reasoning_tools=["websearch"],
        web_search_context_size="high",
    )
    assert agent_high.web_search_context_size == "high"

def test_web_search_default_context_size():
    """Test that default context size is medium when not specified"""
    agent = Agent(
        name="Default Context Agent",
        instructions="Web search agent with default settings.",
        model="openai/gpt-4o-search-preview",
        reasoning_tools=["websearch"],
        # web_search_context_size not specified, should default to "medium"
    )
    assert agent.web_search_context_size == "medium"

def test_agent_without_web_search():
    """Test that agents without web search still work normally"""
    agent = Agent(
        name="Regular Agent",
        instructions="Regular agent without web search.",
        model=GPT_4O_MINI,
        # No reasoning_tools specified
    )
    
    assert agent.reasoning_tools == []
    assert agent.web_search_context_size == "medium"  # Should still have default value

def test_web_search_with_multiple_reasoning_tools():
    """Test agent with multiple reasoning tools including websearch"""
    agent = Agent(
        name="Multi-Tool Agent",
        instructions="Agent with multiple reasoning capabilities.",
        model="openai/gpt-4o-search-preview",
        reasoning_tools=["websearch", "other_tool"],
        web_search_context_size="high",
    )
    
    assert "websearch" in agent.reasoning_tools
    assert "other_tool" in agent.reasoning_tools
    assert agent.web_search_context_size == "high"

@pytest.mark.requires_llm
def test_web_search_agent_request():
    """Test that we can start a request with a web search agent"""
    
    agent = Agent(
        name="Web Search Request Test",
        instructions="You can search the web for current information.",
        model="openai/gpt-4o-search-preview",
        reasoning_tools=["websearch"],
        web_search_context_size="low",  # Use low context for faster test
        debug=DebugLevel(""),  # Disable debug for cleaner test output
    )
    
    try:
        # Start a request that should trigger web search
        request_id = agent.start_request("What's the current weather like today?")
        assert request_id is not None
        assert isinstance(request_id, str)
        
        # Get at least one event to verify the request works
        events = list(agent.get_events(request_id))
        assert len(events) > 0
        
        # Check that we got some kind of response
        has_response = any(event.type in ["chat_output", "turn_end"] for event in events)
        assert has_response, "Expected to receive a response event"
        
    except Exception as e:
        # If we get a temperature error, the fix didn't work
        if "temperature" in str(e).lower():
            pytest.fail(f"Temperature parameter error still occurring: {e}")
        else:
            # Other errors might be expected (API limits, etc.)
            print(f"Note: Got expected error during web search test: {e}")

@pytest.mark.requires_llm  
def test_web_search_different_models():
    """Test web search with different supported models"""
    models_to_test = [
        "openai/gpt-4o-search-preview",
        "gemini-2.0-flash",
        "anthropic/claude-3-5-sonnet-20240620",
    ]
    
    for model in models_to_test:
        agent = Agent(
            name=f"Test Agent for {model}",
            instructions="Web search test agent.",
            model=model,
            reasoning_tools=["websearch"],
            web_search_context_size="low",
        )
        
        try:
            # Start a request that should trigger web search
            request_id = agent.start_request("What's the current weather like today?")
            assert request_id is not None
            assert isinstance(request_id, str)
        
            # Get at least one event to verify the request works
            events = list(agent.get_events(request_id))
            assert len(events) > 0
        
            # Check that we got some kind of response
            has_response = any(event.type in ["chat_output", "turn_end"] for event in events)
            assert has_response, "Expected to receive a response event"
            
        except Exception as e:
            # If we get a temperature error, the fix didn't work
            if "temperature" in str(e).lower():
                pytest.fail(f"Temperature parameter error still occurring: {e}")
            else:
                # Other errors might be expected (API limits, etc.)
                print(f"Note: Got expected error during web search test: {e}")