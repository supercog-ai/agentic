import pytest
from unittest.mock import Mock

from agentic.tools import AutomaticTools, DatabaseTool, GoogleNewsTool, WeatherTool
from agentic.common import ThreadContext, Agent

def a_dummy_tool_function(name: str):
    """ This turns the parameter into a dummy. """
    return name + " is a dummy"

@pytest.fixture
def toolset():
    return [WeatherTool, GoogleNewsTool, DatabaseTool]

@pytest.fixture
def mock_thread_context():
    context = Mock(spec=ThreadContext)
    context.agent = Mock(spec=Agent)
    context.agent.add_tool = Mock()
    return context

@pytest.mark.asyncio
@pytest.mark.requires_llm
async def test_search_for_tool(toolset):
    autos = AutomaticTools(tool_classes=toolset, tool_functions=[a_dummy_tool_function])

    all_tools = await autos.get_tool_listing()
    print(all_tools)

    # Basic functionality tests
    result = await autos.search_for_tool("weather")
    assert "WeatherTool" in result

    result = await autos.search_for_tool("latest finance news")
    assert "GoogleNewsTool" in result

    result = await autos.search_for_tool("make a dummy")
    assert "a_dummy_tool_function" in result

    result = await autos.search_for_tool("post a Slack message")
    assert not result

    # Edge case: Ambiguous queries that could match multiple tools
    result = await autos.search_for_tool("get current conditions")
    assert "WeatherTool" in result

    result = await autos.search_for_tool("find information about")
    assert "GoogleNewsTool" in result

    # Edge case: Queries with mixed purposes
    result = await autos.search_for_tool("weather news and database")
    assert len(result) > 1  # Should return multiple tools

    # Edge case: Very specific but potentially matching queries
    result = await autos.search_for_tool("check if it's raining in New York")
    assert "WeatherTool" in result

    result = await autos.search_for_tool("search for financial market updates")
    assert "GoogleNewsTool" in result

    # Edge case: Queries that might need database but aren't explicit
    result = await autos.search_for_tool("store and retrieve data")
    assert "DatabaseTool" in result

    # Edge case: Queries with technical terms
    result = await autos.search_for_tool("query the database")
    assert "DatabaseTool" in result

    # Edge case: Queries with multiple possible interpretations
    result = await autos.search_for_tool("get updates")
    assert len(result) > 0  # Should return at least one tool

    # Edge case: Queries that are too specific but don't match any tool
    result = await autos.search_for_tool("generate a PDF report")
    assert not result  # Should return no tools for non-matching specific queries

    # Edge case: Queries with mixed case and special characters
    result = await autos.search_for_tool("WEATHER!!!")
    assert "WeatherTool" in result

    result = await autos.search_for_tool("database?")
    assert "DatabaseTool" in result

@pytest.mark.asyncio
@pytest.mark.requires_llm
async def test_enable_agent_tool(toolset, mock_thread_context):
    autos = AutomaticTools(tool_classes=toolset, tool_functions=[a_dummy_tool_function])

    # Test enabling a class-based tool
    result = await autos.enable_agent_tool("WeatherTool", mock_thread_context)
    assert "The tool WeatherTool has been enabled" in result
    mock_thread_context.agent.add_tool.assert_called_once()
    mock_thread_context.agent.add_tool.reset_mock()

    # Test enabling a function-based tool
    result = await autos.enable_agent_tool("a_dummy_tool_function", mock_thread_context)
    assert "The tool a_dummy_tool_function has been enabled" in result
    mock_thread_context.agent.add_tool.assert_called_once()
    mock_thread_context.agent.add_tool.reset_mock()

    # Test enabling with different case
    result = await autos.enable_agent_tool("weathertool", mock_thread_context)
    assert "The tool WeatherTool has been enabled" in result
    mock_thread_context.agent.add_tool.assert_called_once()
    mock_thread_context.agent.add_tool.reset_mock()

    # Test enabling non-existent tool
    result = await autos.enable_agent_tool("NonExistentTool", mock_thread_context)
    assert "Error: Tool not found" in result
    mock_thread_context.agent.add_tool.assert_not_called()

@pytest.mark.asyncio
async def test_get_tool_listing(toolset):
    autos = AutomaticTools(tool_classes=toolset, tool_functions=[a_dummy_tool_function])

    # Test getting all tools
    tools = await autos.get_tool_listing()
    assert len(tools) == len(toolset) + 1  # +1 for the dummy function
    tool_names = [tool["name"] for tool in tools]
    assert "WeatherTool" in tool_names
    assert "GoogleNewsTool" in tool_names
    assert "DatabaseTool" in tool_names
    assert "a_dummy_tool_function" in tool_names
