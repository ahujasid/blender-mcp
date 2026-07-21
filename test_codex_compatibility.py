"""Compatibility checks for MCP clients with approval-aware tool calling."""

import asyncio

from blender_mcp.server import mcp


def _tools_by_name():
    return {tool.name: tool for tool in asyncio.run(mcp.list_tools())}


def test_scene_info_has_no_required_telemetry_argument():
    tool = _tools_by_name()["get_scene_info"]
    assert "user_prompt" not in tool.inputSchema.get("required", [])


def test_scene_info_is_annotated_read_only():
    tool = _tools_by_name()["get_scene_info"]
    assert tool.annotations.readOnlyHint is True
    assert tool.annotations.destructiveHint is False
    assert tool.annotations.idempotentHint is True
    assert tool.annotations.openWorldHint is False


def test_execute_code_requires_write_approval():
    tool = _tools_by_name()["execute_blender_code"]
    assert tool.annotations.readOnlyHint is False
    assert tool.annotations.destructiveHint is True
    assert tool.annotations.idempotentHint is False


def test_external_search_is_read_only_but_open_world():
    tool = _tools_by_name()["search_polyhaven_assets"]
    assert tool.annotations.readOnlyHint is True
    assert tool.annotations.openWorldHint is True


def test_server_instructions_put_safety_first():
    assert mcp.instructions.startswith("Inspect the active Blender scene")
    assert "only be used when the user requested" in mcp.instructions
