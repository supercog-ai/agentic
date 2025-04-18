from typing import Any, Optional, Dict, List, Callable
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from litellm import experimental_mcp_client
from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry, Dependency

@tool_registry.register(
    name="MCPTool",
    description="Universal wrapper for MCP tools that can work with any MCP server.",
    dependencies=[
        Dependency(
            name="mcp",
            version="1.5.0",
            type="pip",
        ),
    ],
    config_requirements=[]
)


class MCPTool(BaseAgenticTool):
    """Universal wrapper for MCP tools that can work with any MCP server."""
    
    def __init__(self, 
                 command: str,
                 args: list[str],
                 tool_name: Optional[str] = None,
                 env: Optional[Dict[str, str]] = None):
        """
        Initialize an MCP tool wrapper.
        
        Args:
            command: The command to run the MCP server (e.g. "python3", "npx")
            args: Arguments for the command (e.g. ["./mcp_server.py"])
            tool_name: Optional specific tool name to use from the MCP server
            env: Optional environment variables to pass to the MCP server
        """
        super().__init__()
        self.server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env or {}
        )
        self.tool_name = tool_name
        self._session = None
        self._tools = None
        self._stdio = None
        
        # Initialize in a new event loop
        self._loop = asyncio.new_event_loop()
        self._loop.run_until_complete(self._init_session())

    async def _init_session(self):
        """Initialize the MCP session if not already initialized."""
        if self._session is None:
            self._stdio = stdio_client(self.server_params)
            read, write = await self._stdio.__aenter__()
            self._session = ClientSession(read, write)
            await self._session.__aenter__()
            await self._session.initialize()
            
            # Load available tools
            self._tools = await experimental_mcp_client.load_mcp_tools(
                session=self._session,
                format="openai"
            )

    def get_tools(self) -> List[Callable]:
        """Get the available MCP tools in OpenAI format."""
        if self._tools is None:
            raise RuntimeError("MCP session not initialized")
            
        # Convert MCP tools to callable functions
        tool_functions = []
        for tool in self._tools:
            if self.tool_name and tool["function"]["name"] != self.tool_name:
                continue
                
            # Get the tool's parameter schema
            tool_schema = tool["function"].get("parameters", {})
            required_params = tool_schema.get("required", [])
            properties = tool_schema.get("properties", {})

            # Create a synchronous wrapper function for each tool
            def tool_wrapper(**kwargs):
                # Extract nested kwargs if needed
                if "kwargs" in kwargs:
                    if isinstance(kwargs["kwargs"], str):
                        try:
                            kwargs = json.loads(kwargs["kwargs"])
                        except:
                            pass
                    elif isinstance(kwargs["kwargs"], dict):
                        kwargs = kwargs["kwargs"]

                # Validate required parameters
                for param in required_params:
                    if param not in kwargs:
                        return f"Error: Missing required parameter '{param}'"

                # Create OpenAI tool format
                openai_tool = {
                    "id": "tool_call_id",  # ID doesn't matter for MCP
                    "type": "function",
                    "function": {
                        "name": tool["function"]["name"],
                        "arguments": json.dumps(kwargs)
                    }
                }
                
                return self._loop.run_until_complete(
                    self.call_tool(openai_tool)
                )
                
            # Format parameter documentation
            param_docs = []
            for param_name, param_info in properties.items():
                required = "required" if param_name in required_params else "optional"
                desc = param_info.get("description", "No description")
                param_type = param_info.get("type", "any")
                enum_values = param_info.get("enum", [])
                
                param_doc = f"  {param_name} ({param_type}, {required}): {desc}"
                if enum_values:
                    param_doc += f"\n    Allowed values: {', '.join(map(str, enum_values))}"
                param_docs.append(param_doc)

            # Set function metadata for OpenAI format
            tool_wrapper.__name__ = tool["function"]["name"]
            tool_wrapper.__doc__ = (
                f"{tool['function'].get('description', '')}\n\n"
                f"Parameters:\n"
                f"{chr(10).join(param_docs)}\n"
            )
            tool_functions.append(tool_wrapper)
        
        return tool_functions

    async def call_tool(self, openai_tool: dict) -> Any:
        """Call an MCP tool with given arguments."""
        if self._session is None:
            await self._init_session()
            
        result = await experimental_mcp_client.call_openai_tool(
            session=self._session,
            openai_tool=openai_tool
        )
        return result

    async def cleanup(self):
        """Cleanup MCP session."""
        if self._session:
            await self._session.__aexit__(None, None, None)
            self._session = None
        if self._stdio:
            await self._stdio.__aexit__(None, None, None)
            self._stdio = None

    def __del__(self):
        """Ensure cleanup on deletion."""
        if self._session or self._stdio:
            try:
                self._loop.run_until_complete(self.cleanup())
            except:
                pass  # Ignore cleanup errors during deletion
            finally:
                self._loop.close() 