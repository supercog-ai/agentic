'''
Pre Standup: 
    - Pull data from the Jira/Github Issues/Commits
    - Analyze the week commits/in progress issues'
    - Potential Blockers and Merge Conflicts
    - Prepare the standup notes and agenda
During Standup:
    - Meeting note taker app
    - Flag missed items and track blockers and tasks
Post Standup:
    - send follow ups (e.g. if a meeting was to be scheduled)'
    - Generate a Summary to be sent
    - Update the Jira board/Github issues
'''
from typing import Any

from agentic.tools.github_tool import GithubTool
from agentic.common import Agent, AgentRunner, RunContext
from agentic.models import GPT_4O_MINI, GPT_4O
import tempfile

instructions = """
You are an AI agent that can prepare and assist with development standup meetings.
When triggered, you need to do the following:
You need to provide a detailed description of the pull requests that are open. Make sure to include the reviews and comments that were left in the discussion along with the pending tasks on each pull request.
You need to provide a summary of the commits made in the last week.
""" 

agent = Agent(
    name="Standup Agent",
    welcome="I am an AI agent that can prepare and assist with development standup meetings.",
    instructions=instructions,
    model=GPT_4O_MINI,
    tools=[GithubTool()], #Add more tools here like meetingbaas and update github according to the standup
    memories=[
        "Use the default repository name and owner when the user does not provide a repository name or owner.",
        "Use the tools to find the information that is not in your context.",
    ]
)

if __name__ == "__main__":
    AgentRunner(agent).repl_loop()
