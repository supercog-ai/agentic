from agentic import Agent, repl_loop, PauseAgentResult
from tools import GoogleNewsTool

gnt = GoogleNewsTool()

def query_news(topic: str):
    return gnt.query_news(topic)

def get_human_input(request_message: str):
    return PauseAgentResult(request_message)

if __name__ == "__main__":

    newsAgent = Agent(
        name="News Gatherer",
        instructions="""
    You do news research. If you dont know the topic, then
    stop for human input on the topic. Then query the news for that topic. 
    """,
        functions=[query_news, get_human_input],
    )

    repl_loop(newsAgent)
