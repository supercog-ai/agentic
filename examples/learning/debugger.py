import os
from agentic.common import Agent, AgentRunner
from agentic.tools import DatabaseTool, PlaywrightTool

# This is the simplest possible Text-to-SQL agent. It uses a database tool to answer questions.


db_path = os.path.expanduser("~/.agentic/database.db")
database_agent = Agent(
    name="Database Agent",
    instructions="""
I can help you query the Runs database. """,
    tools=[
        DatabaseTool(connection_string=f"sqlite:///{db_path}"),
        PlaywrightTool(),
    ],
)

if __name__ == "__main__":
    AgentRunner(database_agent).repl_loop()
