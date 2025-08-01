# PR_agent.py
# Coordinates between a PR Summary Agent and a RAG Sub Agent to generate a summary for a pull request.

from agentic.common import Agent, AgentRunner 
from agentic.models import GPT_4O_MINI # model (using GPT for testing)
from agentic.tools import GithubTool, A2ATool
import rag_sub_agent
import summary_agent

from dotenv import load_dotenv
import openai
import requests
import os

MODEL = GPT_4O_MINI

load_dotenv()  # This loads variables from .env into os.environ
openai.api_key = os.getenv("OPENAI_API_KEY") # api key
github_api = os.getenv("GITHUB_TOKEN")
pr_id = os.getenv("PR_ID")



# Create the A2A tool instance
a2a_tool = A2ATool()



# Register "PR Summary Agent" from summary_agent.py with the A2A tool
a2a_tool.register_agent(
    "pr_summary_agent",
    summary_agent.agent,  # Access the agent from the module
    "Expert in generating a comment for the pull request based on analysis of the provided patch file and relevant context files from the repository."
)

# Register RAG Sub Agent from rag_sub_agent.py with the A2A tool
a2a_tool.register_agent(
    "rag_sub_agent",
    rag_sub_agent.agent,  # Access the agent from the module
    "Expert in using RAG (Retrieval-Augmented Generation) for information retrieval and generation tasks."
)



# Create the coordinator agent that manages the team
coordinator = Agent(
    name="Team Coordinator",
    
    # Agent instructions
    instructions="""
    You are a helpful assistant that can summarize a pull request.
    
    Your responsibilities include:
    - Coordinating between the PR Summary Agent and RAG Sub Agent
    - Ensuring the PR summary is comprehensive and accurate
    - Managing the flow of information between different agents
    - Providing a final, well-structured PR summary
    
    Use the available tools to gather information and generate a high-quality PR summary.
    """,
    
    model=GPT_4O_MINI, # model
    tools=[a2a_tool],
    memories=[]

)



# basic main function that allows us to run our agent locally in terminal
if __name__ == "__main__":

    gh = GithubTool(api_key=github_api)

    output = AgentRunner(coordinator).grab_final_result(
        "You were triggered by a PR opening/reopening. Follow your instructions."
    )

    GithubTool.add_comment_to_issue(issue_number = pr_id, body= output)