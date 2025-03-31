from agentic.common import Agent, AgentRunner
from agentic.tools.utils.registry import tool_registry
import pytest

@pytest.mark.requires_llm
def test_langchain_tool():
    agent = Agent(
        name="Basic Agent",
        instructions="You are a helpful assistant.",
        model="openai/gpt-4o-mini",
        tools=[
            tool_registry.load_tool(
                "langchain_community.tools.DuckDuckGoSearchRun",
                requires=["duckduckgo-search", "langchain-community"],
                always_install=True,
            ),
        ],
    )

    agent_runner = AgentRunner(agent)
    response = agent_runner.turn("search for 'supercog ai'")
    assert "supercog" in response.lower(), response
