from agentic.tools import WeatherTool

from agentic.common import Agent, AgentRunner
from agentic.models import GPT_4O_MINI, LMSTUDIO_QWEN
# This is the "hello world" agent example. A simple agent with a tool for getting weather reports.

MODEL=GPT_4O_MINI # try locally with LMSTUDIO_QWEN

agent = Agent(
    name="Basic Agent",
    welcome="I am a simple agent here to help answer your weather questions.",
    instructions="You are a helpful assistant that reports the weather.",
    model=MODEL,
    tools=[WeatherTool()],
    prompts = {
        "NYC": "What is the weather in New York City?",
        "LA": "What is the weather in Los Angeles?",
        "DC": "What is the weather in Washington DC?",
    }
)

if __name__ == "__main__":
    AgentRunner(agent).repl_loop()
