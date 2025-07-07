# A simple agent to demonstrate the Geolocation tool.

from agentic.tools import GeolocationTool
from agentic.common import Agent, AgentRunner
from agentic.models import GPT_4O_MINI

MODEL=GPT_4O_MINI

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
        "isp": "What is my ISP?",
        "ip": "What is my IP address?",
        "gps": "What are my gps coordinates in (latitude, longitude) format?"
    }
)

if __name__ == "__main__":
    AgentRunner(agent).repl_loop()
