from agentic.common import Agent, AgentRunner
from agentic.tools import GoogleNewsTool, HumanInterruptTool

gnt = GoogleNewsTool()


def query_news(topic: str):
    return gnt.query_news(topic)

newsAgent = Agent(
    name="News Gatherer",
    instructions="""
You do news research. If you dont know the topic, then
stop and ask the user for input on the topic.
Then query the news for that topic. 
""",
    tools=[query_news, HumanInterruptTool()],
)

if __name__ == "__main__":
    AgentRunner(newsAgent).repl_loop()
