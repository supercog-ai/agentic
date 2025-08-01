# mock agent for testing github integration

from agentic.common import Agent, AgentRunner 
from agentic.models import GPT_4O_MINI # model
from agentic.tools import GithubTool
import json
from agentic.common import Agent, AgentRunner 
from agentic.models import GPT_4O_MINI # model

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
pr_id = os.getenv("PR_ID")
repo_owner = os.getenv("REPO_OWNER")
repo_name = os.getenv("REPO_NAME")
gh_api = os.getenv("GITHUB_API_KEY")

# Define the agent
agent = Agent(
    name="PR Summary Agent",

    # Agent instructions
    instructions="""
    You are a helpful PR sumary agent to test github integration.
    Input: A git diff output, showing all changes in the branch.
    Create a short PR summary.

    If the input does not exist, always output an error message instead.
    """,
    
    model=GPT_4O_MINI, # model

)

# basic main function that allows us to run our agent locally in terminal
if __name__ == "__main__":

    gh = GithubTool(api_key=github_api)

    output = AgentRunner(agent).grab_final_result(
        "You were triggered by a PR opening/reopening. Follow your instructions."
    )

    GithubTool.add_comment_to_issue(issue_numer = pr_id, body= output)
    patch = open("PRChanges.patch")

    output = agent.grab_final_result(
        f"You were triggered by a PR. The git diff is as follows: {patch.read()}"
    )

    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{pr_id}/comments"

    headers = {
        "Authorization": f"token {gh_api}",
    }

    data = {
        "body": output
    }
    
    print("Request")
    print(requests.post(url=url,headers=headers,data=json.dumps(data)))
