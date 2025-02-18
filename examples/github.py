from typing import Any

from agentic.tools.github_tool import GithubTool
from agentic.common import Agent, AgentRunner
from agentic.models import CLAUDE

instructions = """
You are an AI agent that can interact with GitHub repositories.
"""

agent = Agent(
    name="Github Agent",
    welcome="I am an AI agent that can interact with GitHub repositories. I can search repositories, create issues, create pull requests, and more.",
    instructions=instructions,
    model=CLAUDE,
    tools=[GithubTool()],
    memories=[
        "Use the default repository name and owner when the user does not provide a repository name or owner.",
        "First check your context when answering questions to see if you have already found the information you need. Then use the tools to find the information that is not in your context.",
    ]
)

if __name__ == "__main__":
    AgentRunner(agent).repl_loop()