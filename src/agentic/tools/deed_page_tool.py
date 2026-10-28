import json
import os
from datetime import timedelta
from typing import Callable, Optional

import anyio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import Dependency, tool_registry

DEED_PAGE_MCP_URL = "https://deed.page/mcp"
PUBLISH_FIELDS = ("url", "slug", "version", "expires_at")


@tool_registry.register(
    name="DeedPageTool",
    description="Publish HTML pages to public URLs with the deed.page MCP server.",
    dependencies=[Dependency(name="mcp", version="^1.9.4", type="pip")],
    config_requirements=[],
)
class DeedPageTool(BaseAgenticTool):
    """Opt-in page publishing over MCP Streamable HTTP, without an account."""

    def __init__(self, token: Optional[str] = None, timeout: float = 60):
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.timeout = timeout
        self.token = token or os.environ.get("DEEDPAGE_TOKEN") or None

    def get_tools(self) -> list[Callable]:
        return [self.deed_page_publish, self.deed_page_delete]

    async def deed_page_publish(
        self,
        html: str,
        slug: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
    ) -> str:
        """Publish an HTML document as a public web page and return its URL.

        slug is an optional lowercase subdomain (letters, digits, hyphens).
        ttl_seconds makes the page expire; omit it to keep the page.
        Publishing again to a slug you own replaces the page.
        """
        arguments = {"files": {"index.html": html}}
        if slug:
            arguments["slug"] = slug
        if ttl_seconds:
            arguments["ttl_seconds"] = ttl_seconds
        data = await self._call("publish_site", arguments)
        token = data.pop("token", None)
        if token and not self.token:
            # Keep the owner token for later updates and deletes; never return
            # it to the model.
            self.token = token
        return json.dumps({key: data[key] for key in PUBLISH_FIELDS if key in data})

    async def deed_page_delete(self, slug: str) -> str:
        """Permanently delete a page this tool published."""
        if not self.token:
            raise RuntimeError("deed.page delete needs the owner token")
        data = await self._call("delete_site", {"slug": slug})
        return json.dumps({"ok": data.get("ok", False), "deleted": slug})

    async def _call(self, name: str, arguments: dict) -> dict:
        headers = {"User-Agent": "agentic/DeedPageTool"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        with anyio.fail_after(self.timeout):
            async with streamablehttp_client(
                DEED_PAGE_MCP_URL,
                headers=headers,
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
            raise RuntimeError(f"deed.page {name} failed: {text}")
        data = json.loads(text)
        if not data.get("ok"):
            raise RuntimeError(f"deed.page {name} failed: {text}")
        return data
