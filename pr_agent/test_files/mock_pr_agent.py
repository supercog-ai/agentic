# mock agent for testing github integration

from agentic.common import Agent, AgentRunner 
from agentic.models import GPT_4O_MINI # model
from agentic.tools import GithubTool

from dotenv import load_dotenv
import openai
import requests
import os


load_dotenv()  # This loads variables from .env into os.environ
openai.api_key = os.getenv("OPENAI_API_KEY") # api key
github_api = os.getenv("GITHUB_TOKEN")
pr_id = os.getenv("PR_ID")

# Define the agent
agent = Agent(
    name="Mock PR Summary Agent",

    # Agent instructions
    instructions="""
    You are a helpful mock PR sumary agent to test github integration.
    Output a helpful example of a PR summary.
    """,
    
    model=GPT_4O_MINI, # model
    tools=[],
    memories=[]

)

# basic main function that allows us to run our agent locally in terminal
if __name__ == "__main__":

    gh = GithubTool(api_key=github_api)

    output = AgentRunner(agent).grab_final_result(
        "You were triggered by a PR opening/reopening. Follow your instructions."
    )

    GithubTool.add_comment_to_issue(issue_numer = pr_id, body= output)
