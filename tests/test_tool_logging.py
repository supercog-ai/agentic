import pytest
from agentic.common import Agent
from agentic.tools import UnitTestingTool
from agentic.models import GPT_4O_MINI
from agentic.events import ToolResult

model = GPT_4O_MINI

# Test the various ways we logging from tools.


@pytest.fixture
def parent():
    story_log = "This is the log from the parent. The sun sets over the horizon."
    child_story_log = "I am just a child in this crazy, agentic world."

    return Agent(
        name="TheParent",
        model=model,
        tools=[
            UnitTestingTool(story_log),
            Agent(
                name="TheChild",
                model=model,
                tools=[UnitTestingTool(child_story_log)],
                db_path=None,
            )
        ]
    )

@pytest.mark.requires_llm
def test_sync_logging(parent):
    tool_outputs = []
    for event in parent.next_turn("call sync_function_with_logging"):
        if isinstance(event, ToolResult):
            tool_outputs.append(event)

    assert len(tool_outputs) > 0

@pytest.mark.requires_llm
def test_async_logging(parent):
    tool_outputs = []
    for event in parent.next_turn("call async_function_with_logging"):
        if isinstance(event, ToolResult):
            tool_outputs.append(event)

    assert len(tool_outputs) > 0
    assert tool_outputs[0].payload["name"] == "async_function_with_logging"
    assert "ASYNC" in tool_outputs[0].result

@pytest.mark.requires_llm
def test_direct_logging(parent):
    tool_outputs = []
    for event in parent.next_turn("call sync_function_direct_logging"):
        if isinstance(event, ToolResult):
            tool_outputs.append(event)

    assert len(tool_outputs) > 0
    assert tool_outputs[0].payload["name"] == "sync_function_direct_logging"
    assert "Something interesting happened" in tool_outputs[0].result
