from agentic.common import Agent, AgentRunner
import pytest

@pytest.mark.requires_llm
def test_handle_run_start():
    agent = Agent(
        name="Agent A",
        instructions="""
Print your request backwards
""",
        handle_run_start=lambda prompt, thread_context: prompt.set_message("fletch"),
    )

    agent_runnner = AgentRunner(agent)
    response = agent_runnner.run("shake & bake")
    assert sorted(response) == sorted("fletch"), response
