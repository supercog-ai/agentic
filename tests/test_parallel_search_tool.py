import asyncio
from contextlib import asynccontextmanager
from functools import partial
import json

import httpx
import pytest

from agentic.tools import ParallelSearchTool
from agentic.tools import parallel_search_tool as module
from agentic.tools.utils.registry import tool_registry


@pytest.fixture
def server(monkeypatch):
    """Run the real MCP client against a deterministic HTTP protocol fixture."""
    state = {"requests": [], "closed": 0, "error": False, "delay": False}

    async def handle(request):
        message = json.loads(request.content)
        state["requests"].append((request, message))
        if message["method"].startswith("notifications/"):
            return httpx.Response(202)
        if message["method"] == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "parallel-fixture", "version": "1"},
            }
        else:
            assert message["method"] == "tools/call"
            if state["delay"]:
                state["started"].set()
                await asyncio.sleep(30)
            result = {
                "content": [
                    {
                        "type": "text",
                        "text": "https://docs.python.org/3/library/asyncio.html",
                    },
                    {
                        "type": "text",
                        "text": "asyncio supports concurrent code with async/await",
                    },
                ],
                "isError": state["error"],
            }
        return httpx.Response(
            200, json={"jsonrpc": "2.0", "id": message["id"], "result": result}
        )

    @asynccontextmanager
    async def factory(headers=None, timeout=None, auth=None):
        assert auth is None
        async with httpx.AsyncClient(
            headers=headers, timeout=timeout, transport=httpx.MockTransport(handle)
        ) as client:
            try:
                yield client
            finally:
                state["closed"] += 1

    monkeypatch.setattr(
        module,
        "streamablehttp_client",
        partial(module.streamablehttp_client, httpx_client_factory=factory),
    )
    return state


@pytest.mark.asyncio
async def test_public_loader_search_and_fetch(server, monkeypatch):
    monkeypatch.setenv("PARALLEL_API_KEY", "must-not-be-used")
    tool = tool_registry.load_tool("agentic.tools.ParallelSearchTool")
    assert isinstance(tool, ParallelSearchTool)
    assert tool_registry.get_tool(ParallelSearchTool).config_requirements == []
    search, fetch = tool.get_tools()
    result = await search("Find asyncio docs", "Python asyncio documentation")
    assert "https://docs.python.org" in result and "async/await" in result
    assert (
        await fetch("https://docs.python.org/3/library/asyncio.html", "concurrency")
        == result
    )
    calls = [m["params"] for _, m in server["requests"] if m["method"] == "tools/call"]
    assert calls == [
        {
            "name": "web_search",
            "arguments": {
                "objective": "Find asyncio docs",
                "search_queries": ["Python asyncio documentation"],
                "session_id": tool.session_id,
            },
        },
        {
            "name": "web_fetch",
            "arguments": {
                "urls": ["https://docs.python.org/3/library/asyncio.html"],
                "objective": "concurrency",
                "session_id": tool.session_id,
            },
        },
    ]
    for request, _ in server["requests"]:
        assert str(request.url) == "https://search.parallel.ai/mcp"
        assert request.headers["user-agent"] == "agentic/ParallelSearchTool"
        assert "authorization" not in request.headers
    assert server["closed"] == 2
    assert tool.__getstate__() == {"timeout": 60, "session_id": tool.session_id}


@pytest.mark.asyncio
async def test_fetch_omits_optional_objective(server):
    await ParallelSearchTool().get_tools()[1]("https://example.com")
    call = next(m for _, m in server["requests"] if m["method"] == "tools/call")
    assert "objective" not in call["params"]["arguments"]


@pytest.mark.asyncio
async def test_mcp_error_is_not_success(server):
    server["error"] = True
    with pytest.raises(RuntimeError, match="Parallel web_search failed"):
        await ParallelSearchTool().parallel_web_search("docs", "Python docs")
    assert server["closed"] == 1


@pytest.mark.asyncio
async def test_deadline_closes_transport(server):
    server["delay"] = True
    server["started"] = asyncio.Event()
    with pytest.raises(TimeoutError):
        await ParallelSearchTool(timeout=0.1).parallel_web_fetch("https://example.com")
    assert server["started"].is_set()
    assert server["closed"] == 1


@pytest.mark.asyncio
async def test_cancellation_closes_transport(server):
    server["delay"] = True
    server["started"] = asyncio.Event()
    task = asyncio.create_task(
        ParallelSearchTool().parallel_web_fetch("https://example.com")
    )
    await asyncio.wait_for(server["started"].wait(), timeout=2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert server["closed"] == 1


def test_invalid_timeout():
    with pytest.raises(ValueError, match="positive"):
        ParallelSearchTool(timeout=0)


def test_agent_schema_and_execution(server):
    from agentic.actor_agents import ActorBaseAgent
    from agentic.swarm.types import ThreadContext
    from agentic.swarm.util import function_to_json
    from openai.types.chat.chat_completion_message_tool_call import (
        ChatCompletionMessageToolCall,
        Function,
    )

    agent = ActorBaseAgent("Parallel fixture")
    agent.functions, agent.tools = [], []
    agent.add_tool(ParallelSearchTool())
    schema = function_to_json(agent.functions[0])["function"]["parameters"]
    assert schema["required"] == ["objective", "search_query"]
    assert schema["properties"]["search_query"] == {"type": "string"}
    call = ChatCompletionMessageToolCall(
        id="fixture-search",
        type="function",
        function=Function(
            name="parallel_web_search",
            arguments=json.dumps(
                {
                    "objective": "Find asyncio docs",
                    "search_query": "Python asyncio documentation",
                }
            ),
        ),
    )
    response, events = agent._execute_tool_calls(
        [call],
        agent.functions,
        ThreadContext(agent, context={}),
    )
    assert "https://docs.python.org" in response.messages[0]["content"]
    assert "Tool error" not in response.messages[0]["content"]
    assert server["closed"] == 1
