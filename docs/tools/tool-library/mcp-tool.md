# MCPTool

The `MCPTool` provides a universal wrapper for Model Control Protocol (MCP) servers. This tool allows agents to interact with any MCP-compatible service, enabling access to specialized capabilities through a standardized interface.

## Features

- Connect to any MCP server
- Dynamically discover available tools
- Execute MCP tool calls with proper formatting
- Handle asynchronous communication with MCP servers

## MCP Overview

The Model Control Protocol (MCP) is a standard for enabling LLMs to interact with external tools. It provides a consistent interface for tool discovery and execution, making it easier to integrate various capabilities into agent systems.

## Initialization

```python
def __init__(command: str, args: list[str], tool_name: Optional[str] = None, env: Optional[Dict[str, str]] = None)
```

**Parameters:**

- `command (str)`: The command to run the MCP server (e.g., "python3", "npx")
- `args (list[str])`: Arguments for the command
- `tool_name (Optional[str])`: Optional specific tool name to use from the MCP server
- `env (Optional[Dict[str, str]])`: Optional environment variables to pass to the MCP server

## Methods

### get_tools

```python
def get_tools(self) -> List[Callable]
```

Get the available MCP tools in a format compatible with Agentic.

**Returns:**
A list of callable functions representing the tools available from the MCP server.

### call_tool

```python
async def call_tool(openai_tool: dict) -> Any
```

Call an MCP tool with given arguments.

**Parameters:**

- `openai_tool (dict)`: Tool call in OpenAI format

**Returns:**
The result from the MCP tool execution.

### cleanup

```python
async def cleanup()
```

Cleanup MCP session and resources.

## Example Usage

```python
from agentic.common import Agent
from agentic.tools.mcp_tool import MCPTool

# Create an MCP tool for a Python-based MCP server
python_mcp = MCPTool(
    command="python3",
    args=["./mcp_servers/data_analysis_server.py"]
)

# Create an agent with MCP capabilities
mcp_agent = Agent(
    name="MCP-Enabled Assistant",
    instructions="You help users by leveraging specialized tools through MCP.",
    tools=[python_mcp]
)

# Use the agent - it will have access to all tools provided by the MCP server
response = mcp_agent << "Analyze the trends in this dataset"
print(response)

# Create an MCP tool for a JavaScript-based MCP server
js_mcp = MCPTool(
    command="npx",
    args=["./mcp-servers/web-scraper"],
    env={"API_KEY": "your-api-key"}
)

# Create an agent with the JavaScript MCP capabilities
web_agent = Agent(
    name="Web Scraping Assistant",
    instructions="You help users extract data from websites using specialized tools.",
    tools=[js_mcp]
)

# Use the agent with JavaScript MCP tools
response = web_agent << "Extract pricing data from this e-commerce site"
print(response)
```

## Creating an MCP Server

To create your own MCP server that works with this tool:

1. Implement the MCP protocol (input/output JSON format)
2. Expose your tools with proper schema definitions
3. Make your server executable with command-line arguments

Example Python MCP server:

```python
from mcp import StdioServer, Tool, schema

@schema.tool("calculator", description="Performs calculations")
def calculator(expression: str) -> float:
    """Calculate the result of a mathematical expression"""
    return eval(expression)

# Create and run MCP server
server = StdioServer(tools=[calculator])
server.run()
```

## Notes

- The MCPTool automatically handles session initialization and cleanup
- The tool handles conversion between OpenAI tool format and MCP format
- Each tool function will have proper documentation based on the MCP schema
- The tool works with both synchronous and asynchronous agent frameworks
