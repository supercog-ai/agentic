import pytest
from agentic.common import Agent, AgentRunner


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
                enable_run_logs=False,
            )
        ],
        model="openai/gpt-4o",
    )

    agent_runnner = AgentRunner(agent)
    response = agent_runnner.turn("run your instructions")
    assert "99" in response.lower(), response



def read_file() -> str:
    """Reads the current file"""
    return "Hello world, i am in a file."


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
