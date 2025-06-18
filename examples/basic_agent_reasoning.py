from agentic.tools import WeatherTool

from agentic.common import Agent, AgentRunner
from agentic.models import GEMINI_2_5_FLASH_PREVIEW

MODEL=GEMINI_2_5_FLASH_PREVIEW

agent = Agent(
    name="Basic Agent",
    welcome="I am a simple agent here to help answer your weather questions.",
    instructions="You are a helpful assistant that reports the weather.",
    model=MODEL,
    tools=[WeatherTool()],
    reasoning_effort="medium"
)

if __name__ == "__main__":
    AgentRunner(agent).repl_loop()
