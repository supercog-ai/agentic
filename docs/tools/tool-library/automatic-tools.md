# AutomaticTools

The `AutomaticTools` is a meta-tool that provides dynamic tool discovery and management capabilities. It allows agents to automatically detect, search for, and enable appropriate tools based on user needs.

## Features

- Automatically discover available tools from a configured list
- Search for tools based on purpose or functionality
- Dynamically enable tools for the agent
- Support for both tool classes and tool functions

## Methods

### get_tool_listing

```python
async def get_tool_listing() -> list[dict]
```

Returns a list of all available tools with their names and descriptions.

**Returns:**
A list of dictionaries containing tool names and descriptions.

### search_for_tool

```python
async def search_for_tool(purpose: str) -> list[str]
```

Searches for one or more tools related to the indicated purpose using both semantic search and keyword matching.

**Parameters:**
- `purpose (str)`: The intended purpose or functionality needed

**Returns:**
A list of tool names that match the purpose.

### enable_agent_tool

```python
async def enable_agent_tool(tool_name: str, thread_context: RunContext) -> str
```

Enables a specific tool for the agent to use.

**Parameters:**
- `tool_name (str)`: The name of the tool to enable
- `thread_context (RunContext)`: The agent's running context

**Returns:**
A status message indicating whether the tool was successfully enabled or suggestions for similar tools.

## Example Usage

```python
from agentic.common import Agent
from agentic.tools import AutomaticTools, WeatherTool, GoogleNewsTool, DatabaseTool

# Create an agent with dynamic tool capabilities
dynamic_agent = Agent(
    name="Dynamic Assistant",
    instructions="You are a helpful assistant that can dynamically enable tools as needed.",
    tools=[
        AutomaticTools(
            tool_classes=[
                WeatherTool,
                GoogleNewsTool,
                DatabaseTool
            ]
        )
    ]
)

# The agent can now dynamically enable tools based on user needs
response = dynamic_agent << "What's the weather like in New York?"
# The agent will automatically enable the WeatherTool and use it

response = dynamic_agent << "Show me the latest tech news"
# The agent will automatically enable the GoogleNewsTool and use it
```

## Implementation Details

The AutomaticTools uses several key features:

1. **Tool Registry**: Integrates with Agentic's tool registry system for tool discovery
2. **Semantic Search**: Uses LLM-based semantic search to find relevant tools
3. **Keyword Matching**: Falls back to keyword matching when semantic search doesn't find matches
4. **Dynamic Loading**: Can load both tool classes and individual tool functions

## Helper Method

The tool includes a helper method:

- `get_docstring`: Extracts documentation from tools

## Notes

- The tool automatically handles tool discovery and loading
- It provides intelligent suggestions when requested tools aren't found
- Supports both class-based tools and function-based tools
- Integrates with Agentic's tool registry system
- Can be used to create highly dynamic agents that adapt their capabilities based on user needs 