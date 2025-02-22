from agentic.common import Agent, AgentRunner, PauseForInputResult, RunContext
from agentic.tools.google_news import GoogleNewsTool
from agentic.tools.human_interrupt import HumanInterruptTool

gnt = GoogleNewsTool()


def query_news(topic: str):
    return gnt.query_news(topic)


def get_human_input(request_message: str, run_context: RunContext):
    if run_context.get("topic"):
        return run_context.get("topic")
    return PauseForInputResult({"topic": request_message})


newsAgent = Agent(
    name="News Gatherer",
    instructions="""
You do news research. If you dont know the topic, then
stop for human input on the topic. Then query the news for that topic. 
""",
    tools=[query_news, HumanInterruptTool()],
)

if __name__ == "__main__":
    AgentRunner(newsAgent).repl_loop()
