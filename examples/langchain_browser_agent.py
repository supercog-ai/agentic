# Example demonstrating the use of LangChainWrapperAgent and BrowserUseAgent
# This example shows how to:
# 1. Create a LangChain agent and wrap it with LangChainWrapperAgent
# 2. Use BrowserUseAgent as a tool in another agent
# 3. Combine them in an operator agent

from agentic.common import Agent, AgentRunner
from agentic.langchain_wrapper import LangChainWrapperAgent
from agentic.tools.browser_use import BrowserUseAgent
from agentic.models import GPT_4O_MINI

# Import LangChain components
from langchain.agents import AgentType, initialize_agent
from langchain_openai import ChatOpenAI
from langchain.tools import DuckDuckGoSearchRun

def main():
    # Create a LangChain agent with DuckDuckGo search tool
    llm = ChatOpenAI(temperature=0)
    search_tool = DuckDuckGoSearchRun()
    langchain_agent = initialize_agent(
        [search_tool], 
        llm, 
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )
    
    # Wrap the LangChain agent with our LangChainWrapperAgent
    langchain_wrapper = LangChainWrapperAgent(
        name="Research Agent",
        model=GPT_4O_MINI,
        langchain_agent=langchain_agent
    )
    
    # Create a BrowserUseAgent
    browser_agent = BrowserUseAgent(
        name="Browser Assistant",
        model=GPT_4O_MINI
    )
    
    # Create an operator agent that can use both agents
    operator = Agent(
        name="Operator", 
        tools=[langchain_wrapper, browser_agent],
        instructions="""
        You are an operator agent that can use both research and browser automation to help users.
        
        You have access to two specialized agents:
        1. Research Agent: Use this for general information gathering and research tasks.
        2. Browser Assistant: Use this for tasks that require browser automation.
        
        Choose the appropriate agent based on the user's request.
        """,
        model=GPT_4O_MINI
    )
    
    # Run the operator agent in an interactive loop
    AgentRunner(operator).repl_loop()

if __name__ == "__main__":
    main()
