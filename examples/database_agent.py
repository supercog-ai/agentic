from agentic import Agent, AgentRunner
from agentic.tools import DatabaseTool

database_agent = Agent(
    name="Database Agent",
    instructions="""
You are a help data analyst. Use your database tools to answer any questions. """,
    tools=[DatabaseTool()],
)

if __name__ == "__main__":
    AgentRunner(database_agent).repl_loop()
