# DeedPageTool

`DeedPageTool` lets an agent publish HTML to a public `https://<slug>.deed.page/`
URL through the [deed.page](https://deed.page/docs) MCP server. It connects to
`https://deed.page/mcp` using Streamable HTTP and needs no account or API key.
Published pages are public. Existing tools and agent defaults are unchanged.

Install the optional MCP dependencies:

```bash
pip install 'agentic-framework[mcp]'
```

Add the tool to an agent:

```python
from agentic.common import Agent, AgentRunner
from agentic.tools import DeedPageTool

agent = Agent(
    name="Page Publisher",
    instructions="Write the requested page as one HTML document, publish it, and reply with its URL.",
    model="openai/gpt-4o-mini",
    tools=[DeedPageTool()],
)

if __name__ == "__main__":
    AgentRunner(agent).repl_loop()
```

The agent exposes two async tools:

- `deed_page_publish(html, slug=None, ttl_seconds=None)` publishes `html` as
  `index.html` and returns JSON with `url`, `slug`, `version` and, for expiring
  pages, `expires_at`. Omit `slug` for a random one; omit `ttl_seconds` to keep
  the page. Publishing again to a slug you own replaces the page.
- `deed_page_delete(slug)` permanently deletes a page you own.

The first publish without a token returns an owner token. The tool keeps it on
the instance (`tool.token`) for later updates and deletes and never returns it to
the model. To keep pages under one owner across runs, store that token privately
and pass it as `DeedPageTool(token=...)` or set `DEEDPAGE_TOKEN`; it is sent as an
`Authorization: Bearer` header. MCP tool errors raise `RuntimeError`.
`DeedPageTool(timeout=60)` sets the total call deadline in seconds.

To try the tools directly without running a language model:

```python
import asyncio
from agentic.tools import DeedPageTool

async def main():
    tool = DeedPageTool()
    page = await tool.deed_page_publish("<h1>Hello from Agentic</h1>", ttl_seconds=3600)
    print(page)

asyncio.run(main())
```

The agent example separately requires credentials for its configured language
model; direct tool calls do not.
