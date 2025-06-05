import asyncio
from typing import Callable, Any

from agentic.common import Agent, AgentRunner, PauseForInputResult, ThreadContext
from agentic.tools import GoogleNewsTool, LinkedinDataTool


def invoke_async(async_func: Callable, *args, **kwargs) -> Any:
    return asyncio.run(async_func(*args, **kwargs))


gnt = GoogleNewsTool()


def query_news(topic: str):
    return gnt.query_news(topic)


def get_human_input(thread_context: ThreadContext):
    if thread_context.get("topic"):
        return thread_context.get("topic")
    return PauseForInputResult({"topic": "What is the news topic?"})


model = "openai/gpt-4o-mini"
#model="lm_studio/qwen2.5-7b-instruct-1m"
#model="lm_studio/deepseek-r1-distill-qwen-7B"

reporter = Agent(
    name="News Reporter",
    instructions=f"""
Call Google News to get headlines on the indicated news topic.
""",
    model=model,
    tools=[query_news],
)

producer = Agent(
    name="Producer",
    welcome="I am the news producer. Tell me the topic, and I'll get the news from my reporter.",
    instructions="""
You are a news producer. Call the human to get the topic, then call the reporter with the indicated topic. 
Print one sentence summary of the report.
""",
    model=model,
    tools=[get_human_input],
)

producer.add_tool(reporter)

if __name__ == "__main__":
    AgentRunner(producer).repl_loop()
