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
When triggered, you need to assume the standups are every Tuesday. That being said, analyze my repository, open issues, comments, open pull requests as well as recently closed issues and pull requests to prepare an agenda for the standup. 
You do not need to provide a count. You need to provide a detailed desciption of which developer is working on which issue, what are the blockers, what are the potential blockers, what are the tasks that are in progress, what are the tasks that are completed and what are the tasks that are to be started.
You need to provide a detailed description of the pull requests that are open. Make sure to include the reviews and comments that were left in the discussion along with the pending tasks on each pull request. 
You need to provide a detailed description of the recently closed issues and pull requests. Make sure to look at the comments and more importantly the reviews on the pull requests to look for future actino items.
""" 

agent = Agent(
    name="Standup Agent",
    welcome="I am an AI agent that can prepare and assist with development standup meetings.",
    instructions=instructions,
    model=GPT_4O_MINI,
    tools=[GithubTool()], #Add more tools here like meetingbaas and update github according to the standup
    memories=[
        "Use the default repository name and owner when the user does not provide a repository name or owner.",
        "First check your context when answering questions to see if you have already found the information you need. Then use the tools to find the information that is not in your context.",
    ]
)

if __name__ == "__main__":
    AgentRunner(agent).repl_loop()
