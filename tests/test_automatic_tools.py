import pytest

from agentic.tools import AutomaticTools, DatabaseTool, GoogleNewsTool, WeatherTool

def a_dummy_tool_function(name: str):
    """ This turns the parameter into a dummy. """
    return name + " is a dummy"

@pytest.fixture
def toolset():
    return [WeatherTool, GoogleNewsTool, DatabaseTool]
    
@pytest.mark.asyncio
@pytest.mark.requires_llm
async def test_search_for_tool(toolset):
    autos = AutomaticTools(tool_classes=toolset, tool_functions=[a_dummy_tool_function])

    all_tools = await autos.get_tool_listing()
    print(all_tools)

    result = await autos.search_for_tool("weather")
    assert "WeatherTool" in result

    result = await autos.search_for_tool("latest finance news")
    assert "GoogleNewsTool" in result

    result = await autos.search_for_tool("make a dummy")
    assert "a_dummy_tool_function" in result

    result = await autos.search_for_tool("post a Slack message")
    assert not result
