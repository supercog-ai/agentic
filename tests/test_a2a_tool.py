import pytest
from unittest.mock import patch, MagicMock
from agentic.common import Agent, AgentRunner
from agentic.tools.a2a_tool import A2ATool
from agentic.events import SubAgentCall, SubAgentResult
from agentic.models import GPT_4O_MINI



@pytest.fixture(autouse=True) 
def mock_database():
    """Mock only the thread/agent database components to prevent database access in tests"""
    with patch('agentic.thread_manager.DatabaseManager') as mock_db1, \
         patch('agentic.actor_agents.DatabaseManager') as mock_db2, \
         patch('agentic.db.db_manager.DatabaseManager') as mock_db3:
        
        # Configure all database manager mocks to avoid file system access
        mock_db1.return_value.get_threads_by_agent.return_value = []
        mock_db1.return_value.get_thread_logs.return_value = []
        mock_db1.return_value.create_thread.return_value = None
        mock_db1.return_value.log_event.return_value = None
        
        mock_db2.return_value.get_threads_by_agent.return_value = []
        mock_db2.return_value.get_thread_logs.return_value = []
        mock_db2.return_value.create_thread.return_value = None
        mock_db2.return_value.log_event.return_value = None
        
        mock_db3.return_value.get_threads_by_agent.return_value = []
        mock_db3.return_value.get_thread_logs.return_value = []
        mock_db3.return_value.create_thread.return_value = None
        mock_db3.return_value.log_event.return_value = None
        
        with patch('agentic.thread_manager.init_thread_tracking') as mock_thread:
            mock_thread.return_value = ("test_thread_id", lambda x, y: None)
            yield mock_db1


@pytest.fixture
def weather_agent():
    """Creates a simple weather agent for testing"""
    return Agent(
        name="Weather Expert",
        instructions="You are a weather expert. When asked about weather, respond with 'The weather is sunny and 75°F'.",
        tools=[],
        db_path=None,
    )


@pytest.fixture
def news_agent():
    """Creates a simple news agent for testing"""
    return Agent(
        name="News Expert", 
        instructions="You are a news expert. When asked about news, respond with 'The top news today is about AI advances'.",
        tools=[],
        db_path=None,
    )


@pytest.fixture
def coordinator_agent(weather_agent, news_agent):
    """Creates a coordinator agent with A2A tool and registered sub-agents"""
    a2a_tool = A2ATool()
    
    # Register the specialist agents
    a2a_tool.register_agent(
        "weather_specialist",
        weather_agent,
        "Expert in weather conditions and forecasts"
    )
    
    a2a_tool.register_agent(
        "news_specialist", 
        news_agent,
        "Expert in current events and news"
    )
    
    coordinator = Agent(
        name="Team Coordinator",
        instructions="""You are a team coordinator. When asked about weather, call the weather_specialist. 
        When asked about news, call the news_specialist. Use the call_agent function.""",
        tools=[a2a_tool],
        model=GPT_4O_MINI,
        db_path=None,
    )
    
    return coordinator


def test_a2a_tool_initialization():
    """Test basic A2A tool initialization"""
    a2a_tool = A2ATool()
    assert len(a2a_tool.registered_agents) == 0
    assert len(a2a_tool.active_conversations) == 0


def test_agent_registration():
    """Test agent registration functionality"""
    a2a_tool = A2ATool()
    
    test_agent = Agent(
        name="Test Agent",
        instructions="Test instructions",
        tools=[],
        db_path=None,
    )
    
    # Test successful registration
    result = a2a_tool.register_agent(
        "test_agent",
        test_agent,
        "A test agent for testing"
    )
    
    assert "successfully registered" in result
    assert "test_agent" in a2a_tool.registered_agents
    assert a2a_tool.registered_agents["test_agent"].name == "test_agent"
    assert a2a_tool.registered_agents["test_agent"].description == "A test agent for testing"


def test_list_available_agents():
    """Test listing available agents"""
    a2a_tool = A2ATool()
    
    # Test empty list
    result = a2a_tool.list_available_agents()
    assert "No agents currently registered" in result
    
    # Add some agents
    agent1 = Agent(name="Agent 1", instructions="Test", tools=[], db_path=None)
    agent2 = Agent(name="Agent 2", instructions="Test", tools=[], db_path=None)
    
    a2a_tool.register_agent("agent1", agent1, "First test agent")
    a2a_tool.register_agent("agent2", agent2, "Second test agent") 
    
    result = a2a_tool.list_available_agents()
    assert "agent1: First test agent" in result
    assert "agent2: Second test agent" in result


def test_get_agent_info():
    """Test getting agent information"""
    a2a_tool = A2ATool()
    
    # Test non-existent agent
    result = a2a_tool.get_agent_info("nonexistent")
    assert "not found" in result
    
    # Test existing agent
    test_agent = Agent(name="Test Agent", instructions="Test", tools=[], db_path=None)
    a2a_tool.register_agent("test_agent", test_agent, "A test agent")
    
    result = a2a_tool.get_agent_info("test_agent")
    assert "Name: test_agent" in result
    assert "Description: A test agent" in result
    assert "Type: Sub-Agent" in result


@pytest.mark.requires_llm
def test_basic_agent_call(coordinator_agent):
    """Test basic agent-to-agent communication"""
    runner = AgentRunner(coordinator_agent)
    
    # Test weather call
    response = runner.turn("What's the weather like?")
    
    # Should contain weather information from the weather agent
    assert "weather" in response.lower() or "sunny" in response.lower() or "75" in response


@pytest.mark.requires_llm
def test_subagent_events(coordinator_agent):
    """Test that SubAgent events are properly generated"""
    request_start = coordinator_agent.start_request("What's the weather like?")
    
    subagent_call_found = False
    subagent_result_found = False
    
    for event in coordinator_agent.get_events(request_start.request_id):
        if isinstance(event, SubAgentCall):
            subagent_call_found = True
            assert event.type == "subagent_call"
            assert event.target_agent is not None
            assert event.payload["message"] is not None
            
        elif isinstance(event, SubAgentResult):
            subagent_result_found = True
            assert event.type == "subagent_result"
            assert event.source_agent is not None
            assert event.payload["result"] is not None
    
    # At least one subagent call should have occurred for weather question
    assert subagent_call_found, "No SubAgentCall event was found"


def test_call_nonexistent_agent():
    """Test error handling when calling non-existent agent"""
    a2a_tool = A2ATool()
    
    result = a2a_tool.call_agent(
        "nonexistent_agent",
        "test message"
    )
    
    assert "not found" in result
    assert "Available agents:" in result


def test_handoff_functionality():
    """Test handoff to agent functionality"""
    a2a_tool = A2ATool()
    
    test_agent = Agent(name="Test Agent", instructions="Test", tools=[], db_path=None)
    a2a_tool.register_agent("test_agent", test_agent, "Test agent")
    
    result = a2a_tool.handoff_to_agent(
        "test_agent",
        "test handoff message"
    )
    
    assert "Handoff to test_agent initiated" in result


def test_handoff_nonexistent_agent():
    """Test handoff error handling"""
    a2a_tool = A2ATool()
    
    result = a2a_tool.handoff_to_agent(
        "nonexistent_agent", 
        "test message"
    )
    
    assert "not found" in result
    assert "Available agents:" in result


def test_a2a_tool_get_tools():
    """Test that A2A tool returns correct function list"""
    a2a_tool = A2ATool()
    tools = a2a_tool.get_tools()
    
    expected_tools = [
        "register_agent",
        "call_agent", 
        "handoff_to_agent",
        "list_available_agents",
        "get_agent_info"
    ]
    
    tool_names = [tool.__name__ for tool in tools]
    
    for expected_tool in expected_tools:
        assert expected_tool in tool_names, f"Expected tool {expected_tool} not found in {tool_names}"


def test_agent_reference_model():
    """Test AgentReference model functionality"""
    from agentic.tools.a2a_tool import AgentReference
    
    test_agent = Agent(name="Test", instructions="Test", tools=[], db_path=None)
    
    agent_ref = AgentReference(
        name="test_agent",
        agent_instance=test_agent,
        description="Test description",
        handoff=False
    )
    
    assert agent_ref.name == "test_agent"
    assert agent_ref.agent_instance == test_agent
    assert agent_ref.description == "Test description"
    assert agent_ref.handoff is False


def test_a2a_request_model():
    """Test A2ARequest model functionality"""
    from agentic.tools.a2a_tool import A2ARequest
    
    request = A2ARequest(
        target_agent="test_agent",
        message="test message",
        context={"key": "value"}
    )
    
    assert request.target_agent == "test_agent"
    assert request.message == "test message"
    assert request.context == {"key": "value"}
    assert len(request.request_id) > 0  # Should have generated UUID


def test_a2a_response_model():
    """Test A2AResponse model functionality"""
    from agentic.tools.a2a_tool import A2AResponse
    
    response = A2AResponse(
        source_agent="agent1",
        target_agent="agent2", 
        result="test result",
        success=True
    )
    
    assert response.source_agent == "agent1"
    assert response.target_agent == "agent2"
    assert response.result == "test result"
    assert response.success is True
    assert response.error_message is None


def test_subagent_event_creation():
    """Test SubAgent event creation and properties"""
    # Test SubAgentCall event
    call_event = SubAgentCall("Team Coordinator", "Weather Expert", "What's the weather?", 0)
    
    assert call_event.type == "subagent_call"
    assert call_event.agent == "Team Coordinator"
    assert call_event.target_agent == "Weather Expert"
    assert call_event.payload["target_agent"] == "Weather Expert"
    assert call_event.payload["message"] == "What's the weather?"
    assert call_event.depth == 0
    
    # Test SubAgentResult event
    result_event = SubAgentResult("Team Coordinator", "Weather Expert", "It's sunny!", 0)
    
    assert result_event.type == "subagent_result"
    assert result_event.agent == "Team Coordinator"
    assert result_event.source_agent == "Weather Expert"
    assert result_event.payload["source_agent"] == "Weather Expert"
    assert result_event.payload["result"] == "It's sunny!"
    assert result_event.depth == 0 