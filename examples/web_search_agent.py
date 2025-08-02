from agentic.common import Agent, AgentRunner
from agentic.actor_agents import DebugLevel

# Create an agent with web search support enabled
agent = Agent(
    name="Web Search Agent",
    welcome="I can search the web for current information to help answer your questions.",
    instructions="""You are a helpful assistant that can access current information through web search.
    When you need up-to-date information to answer a question, use web search to find relevant data.
    Always provide accurate, well-sourced information based on your search results.""",
    model="openai/gpt-4o-search-preview",  # Use a web search-enabled model
    reasoning_tools=["websearch"],  # Enable web search support
    web_search_context_size="medium",  # Use medium context
    debug=DebugLevel("all"),  # Enable debug logging to see web search activity
)

if __name__ == "__main__":
    AgentRunner(agent).repl_loop()