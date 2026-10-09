from datetime import timedelta
from typing import Callable, Optional
from uuid import uuid4

import anyio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import Dependency, tool_registry


@tool_registry.register(
    name="ParallelSearchTool",
    description="Search and fetch web pages with the keyless Parallel Search MCP.",
    dependencies=[Dependency(name="mcp", version="^1.9.4", type="pip")],
    config_requirements=[],
)
class ParallelSearchTool(BaseAgenticTool):
    """Opt-in web search over MCP Streamable HTTP, without a Parallel API key."""

    def __init__(self, timeout: float = 60):
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.timeout = timeout
        self.session_id = uuid4().hex

    def get_tools(self) -> list[Callable]:
        return [self.parallel_web_search, self.parallel_web_fetch]

    async def parallel_web_search(self, objective: str, search_query: str) -> str:
        """Search the web for a focused objective, returning sources and excerpts.

        search_query is a concise keyword query to complement the objective.
        """
        arguments = {"objective": objective, "search_queries": [search_query]}
        return await self._call("web_search", arguments)

    async def parallel_web_fetch(
        self, url: str, objective: Optional[str] = None
    ) -> str:
        """Fetch excerpts from an HTTP(S) URL, optionally focused on an objective."""
        arguments = {"urls": [url]}
        if objective is not None:
            arguments["objective"] = objective
        return await self._call("web_fetch", arguments)

    async def _call(self, name: str, arguments: dict) -> str:
        arguments = {**arguments, "session_id": self.session_id}
        # Keep transport and session in the caller's task so cancellation closes
        # both, and no open connections need to be serialized by Ray.
        with anyio.fail_after(self.timeout):
            async with streamablehttp_client(
                "https://search.parallel.ai/mcp",
                headers={"User-Agent": "agentic/ParallelSearchTool"},
                timeout=self.timeout,
                sse_read_timeout=self.timeout,
            ) as (read, write, _):
                async with ClientSession(
                    read, write, read_timeout_seconds=timedelta(seconds=self.timeout)
                ) as session:
                    await session.initialize()
                    result = await session.call_tool(name, arguments)
        text = "\n".join(block.text for block in result.content if block.type == "text")
        if result.isError:
            raise RuntimeError(f"Parallel {name} failed: {text}")
        return text
