from typing import Callable, Any, Optional, Type
import re
from pydantic import BaseModel
import pandas as pd

from agentic.llm import llm_generate_with_format
from agentic.common import RunContext
from agentic.tools.base  import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry
from agentic.tools.file_download import FileDownloadTool
from agentic.tools.rag_tool import RAGTool

def get_docstring(obj: Any) -> str:
    return obj.__doc__ or ""

@tool_registry.register(
    name="AutomaticTools",
    description="Automatically detects which tool to use and applies it to the agent",
    dependencies=[],
    config_requirements=[],
)

class AutomaticTools(BaseAgenticTool):
    file_download_tool: Optional[FileDownloadTool] = None
    tool_classes: list[Type] = []
    tool_functions: list[Callable] = []

    def __init__(
        self, tool_classes: list[Type] = [], tool_functions: list[Callable] = []
    ):
        super().__init__()
        self.file_download_tool = FileDownloadTool()
        self.tool_classes = tool_classes
        self.tool_functions = tool_functions

    def get_tools(self) -> list[Callable]:
        return [
            self.get_tool_listing,
            self.search_for_tool,
            self.enable_agent_tool,
            self.universal_read_file,
        ]

    async def get_tool_listing(
        self, show_connections_only: Optional[bool] = False
    ) -> list[dict]:
        """ " Returns the list of all available tools."""

        records = []
        for tool_class in self.tool_classes:
            records.append(
                {"name": tool_class.__name__, "description": get_docstring(tool_class)}
            )
        for tool_function in self.tool_functions:
            records.append(
                {
                    "name": tool_function.__name__,
                    "description": get_docstring(tool_function),
                }
            )

        return records

    async def search_for_tool(self, purpose: str) -> list[str]:
        """Searches for one or more tools related to the indicated purpose."""

        class ToolSuggestion(BaseModel):
            tool_choices: list[str]

        SEARCH_PROMPT = """
Given the list of tools below, return one or two suggestions for the tool that best fits: {{purpose}}.
Return no results if no tool fits the purpose.
----------
{% for tool in tools %}
{{tool.name}} - {{tool.description}}
{% endfor %}
"""

        tools = await self.get_tool_listing()

        result: ToolSuggestion = llm_generate_with_format(
            SEARCH_PROMPT,
            ToolSuggestion,
            purpose=purpose,
            tools=tools,
        )
        if len(result.tool_choices) == 0:
            # simple keyword search
            purpose2 = purpose.replace("tool", "").lower().strip()
            candidates = [
                t["name"]
                for t in tools
                if (purpose in t["name"].lower() or purpose2 in t["name"].lower())
            ]
            if len(candidates) > 0:
                # sort candidates by longest name first
                candidates.sort(key=lambda x: len(x), reverse=True)
                return candidates
        else:
            return result.tool_choices

    async def enable_agent_tool(self, tool_name: str, run_context: RunContext) -> str:
        """Enables the AI agent to use the tool with the indicated name."""

        # Remove use of 'tool' word in the tool name. Use regexp
        # to match. And lowercase.
        tool_name1 = tool_name.lower()
        tool_name2 = re.sub(r"\s+tool\s*", "", tool_name.lower())

        for tool_cls in self.tool_classes:
            if tool_cls.__name__.lower() in [tool_name1, tool_name2]:
                run_context.agent.add_tool(tool_cls())
                return f"The tool {tool_cls.__name__} has been enabled."

        for tool_func in self.tool_functions:
            if tool_func.__name__.lower() in [tool_name1, tool_name2]:
                run_context.agent.add_tool(tool_func)
                return f"The tool {tool_func.__name__} has been enabled."

        # In case the agent requested a tool that doesn't exist, see if we can suggest one
        suggestions = await self.search_for_tool(tool_name)
        return f"Error: Tool not found: {tool_name}. Perhaps you want one of: {', '.join(suggestions)}"

    async def universal_read_file(self, file_name: str) -> Any:
        """Reads the contents for any file type. Also supports reading from URLs."""
        try:
            value, mime_type = await RAGTool._universal_read_file(
                file_name, self.run_context
            )
            if isinstance(value, str):
                return value
            elif isinstance(value, pd.DataFrame):
                return self.get_dataframe_preview(value)
        except ValueError as e:
            return f"Error reading file: {e}"
