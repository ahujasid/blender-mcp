"""MCP Python SDK v2 compatibility tests."""

import pytest
from mcp import Client
from mcp.types.version import LATEST_PROTOCOL_VERSION

import blender_mcp.server as server
from blender_mcp.server import mcp


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_server_supports_2026_07_28_and_lists_tools():
    assert LATEST_PROTOCOL_VERSION == "2026-07-28"

    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.list_tools()
        tools = result.tools

    names = {tool.name for tool in tools}
    assert {
        "get_scene_info",
        "get_viewport_screenshot",
        "execute_blender_code",
        "get_polyhaven_status",
    } <= names
    assert result.ttl_ms == 300_000
    assert result.cache_scope == "public"


@pytest.mark.anyio
async def test_tool_catalog_order_is_deterministic():
    async with Client(mcp, raise_exceptions=True) as client:
        first = [tool.name for tool in (await client.list_tools()).tools]
        second = [tool.name for tool in (await client.list_tools()).tools]

    assert first == second


def test_main_defaults_to_stdio(monkeypatch):
    calls = []
    monkeypatch.delenv("BLENDER_MCP_TRANSPORT", raising=False)
    monkeypatch.setattr(server.mcp, "run", lambda *args, **kwargs: calls.append((args, kwargs)))

    server.main()

    assert calls == [((), {})]


def test_main_configures_stateless_streamable_http(monkeypatch):
    calls = []
    monkeypatch.setenv("BLENDER_MCP_TRANSPORT", "streamable-http")
    monkeypatch.setenv("BLENDER_MCP_HTTP_HOST", "127.0.0.1")
    monkeypatch.setenv("BLENDER_MCP_HTTP_PORT", "8765")
    monkeypatch.setenv("BLENDER_MCP_HTTP_PATH", "custom-mcp")
    monkeypatch.setattr(server.mcp, "run", lambda *args, **kwargs: calls.append((args, kwargs)))

    server.main()

    assert calls == [
        (
            (),
            {
                "transport": "streamable-http",
                "host": "127.0.0.1",
                "port": 8765,
                "streamable_http_path": "/custom-mcp",
                "stateless_http": True,
                "json_response": True,
            },
        )
    ]


def test_main_refuses_unprotected_remote_http(monkeypatch):
    monkeypatch.setenv("BLENDER_MCP_TRANSPORT", "streamable-http")
    monkeypatch.setenv("BLENDER_MCP_HTTP_HOST", "0.0.0.0")
    monkeypatch.delenv("BLENDER_MCP_ALLOW_REMOTE_HTTP", raising=False)

    with pytest.raises(ValueError, match="Refusing to expose Blender MCP"):
        server.main()
