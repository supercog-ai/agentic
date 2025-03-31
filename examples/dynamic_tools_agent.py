from agentic.tools import (
    AutomaticTools,
    BrowserUseTool,
    DatabaseTool,
    DuckDuckGoTool,
    GoogleNewsTool,
    ImageGeneratorTool,
    IMAPTool,
    LinkedinDataTool,
    TavilySearchTool,
    WeatherTool
)

from agentic.common import Agent, AgentRunner
from agentic.tools.utils.registry import tool_registry

# This is a demonstration of dynamic tool use. You can add a tool to an agent at any time. This
# demo uses a meta tool called "AutomaticTools" which will automatically load tools from the
# list of tools you configure it with. AutomaticTools exposes a "seach_for_tool" and 
# "enable_agent_tool" function which your agent can use to automatically enable a tool.
#
# Try running this agent and then requesting something that requires a tool to be enabled.
# Or for simple use just say "please enable <tool name>".
#
# In the REPL you can alway use the system command `.tools` to see which tools are currently active.

agent = Agent(
    name="Dynamic Tools Agent",
    welcome="I have a list of tools which I can enable and use on-demand. Query the list of tools to start.",
    instructions="You are a helpful assistant. You can list tools or enable a tool for different purposes.",
    model="openai/gpt-4o-mini",
    tools=[
        AutomaticTools(
            tool_classes=[
                GoogleNewsTool, 
                WeatherTool, 
                DatabaseTool, 
                LinkedinDataTool, 
                ImageGeneratorTool,
                TavilySearchTool,
                IMAPTool,
                DuckDuckGoTool,
            ],
        ),
        # The tool registry has some support for installing/loading LangChain tools.
        tool_registry.load_tool(
            "langchain_community.tools.shell.tool.ShellTool",
            requires=["langchain-community", "langchain-experimental"]
        ),
    ],
)

if __name__ == "__main__":
    AgentRunner(agent).repl_loop()
