from agentic.tools import GeolocationTool

from agentic.common import Agent, AgentRunner
from agentic.models import GPT_4O_MINI, LMSTUDIO_QWEN
# This is the "hello world" agent example. A simple agent with a tool for getting weather reports.

MODEL=GPT_4O_MINI # try locally with LMSTUDIO_QWEN

agent = Agent(
    name="Geolocation Agent",
    welcome="I am a simple agent here to help answer your geolocation questions.",
    instructions="You are a helpful assistant that reports the weather.",
    model=MODEL,
    tools=[GeolocationTool()],
    prompts = {
        "location": "What is the location of the user?",
        "time": "What is the time in the user's location?",
        "timezone": "What is the timezone of the user?",
    }
)

if __name__ == "__main__":
    AgentRunner(agent).repl_loop()
