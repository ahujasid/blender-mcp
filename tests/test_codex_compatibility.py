"""Compatibility checks for approval-aware MCP clients such as Codex."""

import asyncio

from blender_mcp.server import mcp


def _tools_by_name():
    return {tool.name: tool for tool in asyncio.run(mcp.list_tools())}


def test_scene_info_has_no_required_telemetry_argument():
    tool = _tools_by_name()["get_scene_info"]

    assert "user_prompt" not in tool.inputSchema.get("required", [])


def test_every_tool_has_approval_metadata():
    tools = _tools_by_name()

    assert tools
    assert all(tool.annotations is not None for tool in tools.values())


def test_scene_inspection_is_local_and_read_only():
    tools = _tools_by_name()

    for name in ("get_scene_info", "get_object_info", "get_viewport_screenshot"):
        annotations = tools[name].annotations
        assert annotations.readOnlyHint is True
        assert annotations.destructiveHint is False
        assert annotations.idempotentHint is True
        assert annotations.openWorldHint is False


def test_external_search_is_read_only_but_open_world():
    annotations = _tools_by_name()["search_polyhaven_assets"].annotations

    assert annotations.readOnlyHint is True
    assert annotations.destructiveHint is False
    assert annotations.idempotentHint is True
    assert annotations.openWorldHint is True


def test_execute_code_remains_a_destructive_write():
    annotations = _tools_by_name()["execute_blender_code"].annotations

    assert annotations.readOnlyHint is False
    assert annotations.destructiveHint is True
    assert annotations.idempotentHint is False
    assert annotations.openWorldHint is False


def test_server_instructions_put_connection_and_safety_first():
    first_paragraph = mcp.instructions.split("\n\n", 1)[0]

    assert len(first_paragraph) <= 512
    assert "Blender add-on" in first_paragraph
    assert "execute_blender_code runs arbitrary Python" in first_paragraph
    assert "verify it again afterward" in first_paragraph
