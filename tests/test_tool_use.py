import pytest
from agentic.common import Agent, AgentRunner
from agentic.tools.unit_test_tool import UnitTestingTool
from agentic.models import CLAUDE, GPT_4O_MINI

model = GPT_4O_MINI

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
                model=CLAUDE,
                tools=[UnitTestingTool(child_story_log)],
                enable_run_logs=False,
            )
        ]
    )

def test_tool_use(parent):
    res = AgentRunner(parent).turn("Please read the story log")
    print(res)
    assert "the parent" in res

    res = AgentRunner(parent).turn("Call the child and ask for its story log")
    print(res)
    assert "crazy" in res
