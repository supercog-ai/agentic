import pytest
from agentic.common import ThreadAgent, ThreadRunner


def test_agent():
    agent = ThreadAgent(
        name="Basic Agent",
        welcome="I am a simple agent here to help.",
        instructions="You are a helpful assistant.",
        tools=[],
    )
    assert agent.name == "Basic Agent"
    assert agent.welcome == "I am a simple agent here to help."
    assert agent.instructions == "You are a helpful assistant."

    agent_runnner = ThreadRunner(agent)
    response = agent_runnner.turn("please tell me hello")
    assert "hello" in response.lower(), response

def test_agent_as_tool():
    agent = ThreadAgent(
        name="Agent A",
        instructions="""
Print this 'I am agent 1'.
Then call agent B once with the request 'run'
""",
        tools=[
            ThreadAgent(
                name="Agent B",
                instructions="Only print 'I am agent B. My secret number is 99'.",
                enable_run_logs=False,
            )
        ],
        model="openai/gpt-4o",
    )

    agent_runnner = ThreadRunner(agent)
    response = agent_runnner.turn("run your instructions")
    assert "99" in response.lower(), response


def test_event_depth():
    agent = ThreadAgent(
        name="Agent A",
        instructions="""
Print this 'I am agent 1'.
Then call agent B once with the request 'run'
""",
        tools=[
            ThreadAgent(
                name="Agent B",
                instructions="Only print 'I am agent B. My secret number is 99'.",
                enable_run_logs=False,
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


def test_simple_tool_use():
    global read_file_was_called

    agent = ThreadAgent(
        name="Agent Simple Tool Use",
        instructions="You are helpful assistant.",
        tools=[read_file],
    )

    agent_runnner = ThreadRunner(agent)
    response = agent_runnner.turn("read the file")
    assert "world" in response.lower(), response
