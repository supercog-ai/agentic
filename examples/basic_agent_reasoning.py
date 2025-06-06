from agentic.tools import WeatherTool

from agentic.common import Agent, AgentRunner
from agentic.models import CLAUDE_4_SONNET

MODEL=CLAUDE_4_SONNET

agent = Agent(
    name="Basic Agent",
    welcome="I am a simple agent here to help answer your weather questions.",
    instructions="You are a helpful assistant that reports the weather.",
    model=MODEL,
    tools=[],
    reasoning_effort="low"
)

if __name__ == "__main__":
    AgentRunner(agent).repl_loop()
