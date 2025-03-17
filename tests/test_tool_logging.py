import pytest
from agentic.common import Agent, AgentRunner
from agentic.tools.unit_test_tool import UnitTestingTool
from agentic.models import CLAUDE, GPT_4O_MINI
from agentic.events import ToolOutput, TurnEnd

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

def test_sync_logging(parent):
    tool_outputs = []
    turn_end = None
    for event in parent.next_turn("call sync_function_with_logging"):
        if isinstance(event, ToolOutput):
            tool_outputs.append(event)
        elif isinstance(event, TurnEnd):
            turn_end = event

    print("Turn end: ", turn_end)
    assert len(tool_outputs) > 0

def test_async_logging(parent):
    tool_outputs = []
    turn_end = None
    for event in parent.next_turn("call async_function_with_logging"):
        if isinstance(event, ToolOutput):
            tool_outputs.append(event)
        elif isinstance(event, TurnEnd):
            turn_end = event

    print("Turn end: ", turn_end)
    assert len(tool_outputs) > 0
    assert tool_outputs[0].payload == "async_function_with_logging"
    assert "ASYNC" in tool_outputs[0].result

def test_direct_logging(parent):
    tool_outputs = []
    turn_end = None
    for event in parent.next_turn("call sync_function_direct_logging"):
        if isinstance(event, ToolOutput):
            tool_outputs.append(event)
        elif isinstance(event, TurnEnd):
            turn_end = event

    print("Turn end: ", turn_end)
    assert len(tool_outputs) > 0
    assert tool_outputs[0].payload == "sync_function_direct_logging"
    assert "Something interesting happened" in tool_outputs[0].result
