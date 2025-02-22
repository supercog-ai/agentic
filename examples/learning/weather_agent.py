from agentic.common import Agent, AgentRunner

# This is the "hello world" agent example. With a fake weather function.

def weather_tool():
    return "The weather is nice today."


agent = Agent(
    name="Basic Agent",
    welcome="I am a simple agent here to help answer your weather questions.",
    instructions="You are a helpful assistant.",
    model="openai/gpt-4o-mini",
    tools=[weather_tool],
)

if __name__ == "__main__":
    AgentRunner(agent).repl_loop()
