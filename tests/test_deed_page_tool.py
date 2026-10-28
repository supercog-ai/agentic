from contextlib import asynccontextmanager
from functools import partial
import json

import httpx
import pytest

from agentic.tools import DeedPageTool
from agentic.tools import deed_page_tool as module
from agentic.tools.utils.registry import tool_registry


@pytest.fixture
def server(monkeypatch):
    """Run the real MCP client against a deterministic deed.page fixture."""
    state = {"requests": [], "closed": 0, "error": False}

    async def handle(request):
        message = json.loads(request.content)
        state["requests"].append((request, message))
        if message["method"].startswith("notifications/"):
            return httpx.Response(202)
        if message["method"] == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "deed-page-fixture", "version": "1"},
            }
        else:
            assert message["method"] == "tools/call"
            name = message["params"]["name"]
            if name == "publish_site":
                payload = {
                    "ok": True,
                    "url": "https://fixture-page.deed.page/",
                    "slug": "fixture-page",
                    "version": "v1",
                    "expires_at": "2030-01-01T00:00:00.000Z",
                }
                if "authorization" not in request.headers:
                    payload["token"] = "deed_tok_fixture"
            else:
                payload = {
                    "ok": True,
                    "deleted": message["params"]["arguments"]["slug"],
                }
            if state["error"]:
                payload = {"code": "slug_reserved", "message": "Reserved."}
            result = {
                "content": [{"type": "text", "text": json.dumps(payload)}],
                "isError": state["error"],
            }
        return httpx.Response(
            200, json={"jsonrpc": "2.0", "id": message["id"], "result": result}
        )

    @asynccontextmanager
    async def factory(headers=None, timeout=None, auth=None):
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


def calls(server):
    return [m["params"] for _, m in server["requests"] if m["method"] == "tools/call"]


@pytest.mark.asyncio
async def test_publish_keeps_token_from_model_and_reuses_it(server, monkeypatch):
    monkeypatch.delenv("DEEDPAGE_TOKEN", raising=False)
    tool = tool_registry.load_tool("agentic.tools.DeedPageTool")
    assert isinstance(tool, DeedPageTool)
    assert tool_registry.get_tool(DeedPageTool).config_requirements == []
    publish, delete = tool.get_tools()

    result = json.loads(
        await publish("<h1>Hi</h1>", slug="fixture-page", ttl_seconds=600)
    )
    assert result == {
        "url": "https://fixture-page.deed.page/",
        "slug": "fixture-page",
        "version": "v1",
        "expires_at": "2030-01-01T00:00:00.000Z",
    }
    assert tool.token == "deed_tok_fixture"
    assert json.loads(await delete("fixture-page")) == {
        "ok": True,
        "deleted": "fixture-page",
    }

    assert calls(server) == [
        {
            "name": "publish_site",
            "arguments": {
                "files": {"index.html": "<h1>Hi</h1>"},
                "slug": "fixture-page",
                "ttl_seconds": 600,
            },
        },
        {"name": "delete_site", "arguments": {"slug": "fixture-page"}},
    ]
    first, last = server["requests"][0][0], server["requests"][-1][0]
    assert str(first.url) == "https://deed.page/mcp"
    assert first.headers["user-agent"] == "agentic/DeedPageTool"
    assert "authorization" not in first.headers
    assert last.headers["authorization"] == "Bearer deed_tok_fixture"
    assert server["closed"] == 2


@pytest.mark.asyncio
async def test_optional_arguments_are_omitted(server, monkeypatch):
    monkeypatch.delenv("DEEDPAGE_TOKEN", raising=False)
    await DeedPageTool().deed_page_publish("<p>x</p>")
    assert calls(server)[0]["arguments"] == {"files": {"index.html": "<p>x</p>"}}


@pytest.mark.asyncio
async def test_configured_token_is_sent_and_kept(server, monkeypatch):
    monkeypatch.setenv("DEEDPAGE_TOKEN", "deed_tok_env")
    tool = DeedPageTool()
    await tool.deed_page_publish("<p>x</p>")
    assert server["requests"][0][0].headers["authorization"] == "Bearer deed_tok_env"
    assert tool.token == "deed_tok_env"
    assert DeedPageTool(token="deed_tok_arg").token == "deed_tok_arg"


@pytest.mark.asyncio
async def test_delete_without_token_does_not_connect(server, monkeypatch):
    monkeypatch.delenv("DEEDPAGE_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="owner token"):
        await DeedPageTool().deed_page_delete("fixture-page")
    assert server["requests"] == []


@pytest.mark.asyncio
async def test_mcp_error_is_not_success(server, monkeypatch):
    monkeypatch.delenv("DEEDPAGE_TOKEN", raising=False)
    server["error"] = True
    with pytest.raises(RuntimeError, match="deed.page publish_site failed"):
        await DeedPageTool().deed_page_publish("<p>x</p>", slug="hello")
    assert server["closed"] == 1


def test_invalid_timeout():
    with pytest.raises(ValueError, match="positive"):
        DeedPageTool(timeout=0)


def test_agent_schema(monkeypatch):
    from agentic.actor_agents import ActorBaseAgent
    from agentic.swarm.util import function_to_json

    agent = ActorBaseAgent("deed.page fixture")
    agent.functions, agent.tools = [], []
    agent.add_tool(DeedPageTool())
    publish = function_to_json(agent.functions[0])["function"]
    assert publish["name"] == "deed_page_publish"
    assert publish["parameters"]["required"] == ["html"]
    assert (
        function_to_json(agent.functions[1])["function"]["name"] == "deed_page_delete"
    )
