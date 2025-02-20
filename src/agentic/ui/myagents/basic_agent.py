from agentic.common import Agent
from agentic.tools.weather_tool import WeatherTool

# This is the "hello world" agent example. A simple agent with a tool for getting weather reports.


weather_agent = Agent(
    name="Basic Agent",
    welcome="I am a simple agent here to help answer your weather questions.",
    instructions="You are a helpful assistant.",
    model="openai/gpt-4o-mini",
    tools=[WeatherTool()],
)
