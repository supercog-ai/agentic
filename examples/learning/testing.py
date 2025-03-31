from agentic.tools import UnitTestingTool

from agentic.common import Agent, AgentRunner

agent = Agent(
    name="Agentic Testing",
    welcome="This is a unit testing agent",
    instructions="""
    You have some functions to work with. Print verbose output about your steps and actions.
    Print a message before and after each function call.
""",
    model="openai/gpt-4o",
    tools=[UnitTestingTool()]
)

if __name__ == "__main__":
    AgentRunner(agent).repl_loop()
