from agentic.common import Agent, AgentRunner
from agentic.models import CLAUDE
from agentic.tools import example_tool

instructions = """
You are a helpful assistant, helping the user to construct new "AI agent" tools.
A tool is a class with a set of functions intended to give an AI agent some new capability.
Follow these steps:
1. Start by asking the user what they want to do with the new tool.
Ask clarifying questions about exactly how they tool should operate.
2. Determine what kind of authentication the tool may need. Common types of API keys via
an environment variable or authentication token via Oauth2 flow.
3. Now explain your intended design for the tool.
4. Now generate the code for the tool, based on the example of how tools are defined.
5. Ask the user if they would like to make any changes.
"""
tool_builder = Agent(
    name="Tool Builder",
    welcome="I can help you code new tools for your AI agent. Tell me about the tool you want to build.",
    instructions=instructions,
    model=CLAUDE,
    memories=["Example tool definition: \n" + open(example_tool.__file__).read()],
    tools=[]
)

if __name__ == "__main__":
    AgentRunner(tool_builder).repl_loop()
