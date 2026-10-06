# ParallelSearchTool

`ParallelSearchTool` adds opt-in web search and page fetching through
[Parallel Search MCP](https://docs.parallel.ai/integrations/mcp/search-mcp).
It connects to `https://search.parallel.ai/mcp` using Streamable HTTP and works
without a Parallel API key. It does not read saved credentials or environment
API keys. Existing search tools and agent defaults are unchanged.

Install the optional MCP dependencies:

```bash
pip install 'agentic-framework[mcp]'
```

Add the tool to an agent:

```python
from agentic.common import Agent, AgentRunner
from agentic.tools import ParallelSearchTool

agent = Agent(
    name="Web Research Assistant",
    instructions="Search for sources, fetch relevant pages, and cite their URLs.",
    model="openai/gpt-4o-mini",
    tools=[ParallelSearchTool()],
)

if __name__ == "__main__":
    AgentRunner(agent).repl_loop()
```

The agent exposes two async tools:

- `parallel_web_search(objective, search_query)` returns sources and
  excerpts for a focused objective. Supply a concise keyword query.
- `parallel_web_fetch(url, objective=None)` extracts excerpts from an
  HTTP(S) URL. An optional objective focuses the extraction.

Both return the server's text content, including source URLs. MCP tool errors
raise `RuntimeError`; transport errors propagate to the caller. Each call opens
and closes its own MCP connection. A stable session identifier is shared by
search and fetch on the same tool instance. `ParallelSearchTool(timeout=60)` sets
the total call deadline in seconds, including connection and initialization.
Cancellation closes the session and transport.

To try the tools directly without running a language model:

```python
import asyncio
from agentic.tools import ParallelSearchTool

async def main():
    tool = ParallelSearchTool()
    print(await tool.parallel_web_search(
        "Find the official Python asyncio documentation", "Python asyncio documentation"
    ))
    print(await tool.parallel_web_fetch("https://docs.python.org/3/library/asyncio.html"))

asyncio.run(main())
```

The anonymous service has lower rate limits and server-managed search settings.
Free access is intended for exploration and light use, and is not unlimited.
The agent example separately requires credentials for its configured language
model; direct tool calls do not.
