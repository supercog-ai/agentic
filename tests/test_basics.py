import pytest
from agentic.common import Agent, AgentRunner


@pytest.mark.requires_llm
def test_agent():
    agent = Agent(
        name="Basic Agent",
        welcome="I am a simple agent here to help.",
        instructions="You are a helpful assistant.",
        tools=[],
    )
    assert agent.name == "Basic Agent"
    assert agent.welcome == "I am a simple agent here to help."
    assert agent.instructions == "You are a helpful assistant."

    agent_runnner = AgentRunner(agent)
    response = agent_runnner.turn("please tell me hello")
    assert "hello" in response.lower(), response

@pytest.mark.requires_llm
def test_agent_as_tool():
    agent = Agent(
        name="Agent A",
        instructions="""
Print this 'I am agent 1'.
Then call agent B once with the request 'run'
""",
        tools=[
            Agent(
                name="Agent B",
                instructions="Only print 'I am agent B. My secret number is 99'.",
                db_path=None,
            )
        ],
        model="openai/gpt-4o",
    )

    agent_runnner = AgentRunner(agent)
    response = agent_runnner.turn("run your instructions")
    assert "99" in response.lower(), response

@pytest.mark.requires_llm
def test_event_depth():
    agent = Agent(
        name="Agent A",
        instructions="""
Print this 'I am agent 1'.
Then call agent B once with the request 'run'
""",
        tools=[
            Agent(
                name="Agent B",
                instructions="Only print 'I am agent B. My secret number is 99'.",
                db_path=None,
            )
        ],
        model="openai/gpt-4o",
    )

    request_start = agent.start_request("run your instructions")
    for event in agent.get_events(request_start.request_id):
        if event.agent == 'Agent A':
            assert event.depth == 0
        elif event.agent == 'Agent B':
            assert event.depth == 1


def read_file() -> str:
    """Reads the current file"""
    return "Hello world, i am in a file."

@pytest.mark.requires_llm
def test_simple_tool_use():
    global read_file_was_called

    agent = Agent(
        name="Agent Simple Tool Use",
        instructions="You are helpful assistant.",
        tools=[read_file],
    )

    agent_runnner = AgentRunner(agent)
    response = agent_runnner.turn("read the file")
    assert "world" in response.lower(), response
