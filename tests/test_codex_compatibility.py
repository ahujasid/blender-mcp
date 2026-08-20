"""Compatibility checks for approval-aware MCP clients such as Codex."""

import asyncio

from blender_mcp.server import mcp


def _tools_by_name():
    return {tool.name: tool for tool in asyncio.run(mcp.list_tools())}


def test_scene_info_has_no_required_telemetry_argument():
    tool = _tools_by_name()["get_scene_info"]

    assert "user_prompt" not in tool.inputSchema.get("required", [])


def test_tool_annotations_cover_every_side_effect_boundary():
    tools = _tools_by_name()
    expected = {
        # Local, idempotent inspection.
        **{
            name: (True, False, True, False)
            for name in {
                "get_addon_status",
                "get_scene_info",
                "get_object_info",
                "get_viewport_screenshot",
                "get_polyhaven_status",
                "get_hyper3d_status",
                "get_sketchfab_status",
                "get_hunyuan3d_status",
            }
        },
        # Read-only calls that query external asset or generation services.
        **{
            name: (True, False, True, True)
            for name in {
                "get_polyhaven_categories",
                "search_polyhaven_assets",
                "search_sketchfab_models",
                "get_sketchfab_model_preview",
                "poll_rodin_job_status",
                "poll_hunyuan_job_status",
            }
        },
        # Local writes with distinct idempotency/destructive behavior.
        "disable_telemetry": (False, False, True, False),
        "record_trajectory_feedback": (False, False, False, False),
        "execute_blender_code": (False, True, False, False),
        "set_texture": (False, True, False, False),
        # External calls that can also create or import scene assets.
        **{
            name: (False, False, False, True)
            for name in {
                "download_polyhaven_asset",
                "download_sketchfab_model",
                "generate_hyper3d_model_via_text",
                "generate_hyper3d_model_via_images",
                "import_generated_asset",
                "generate_hunyuan3d_model",
                "import_generated_asset_hunyuan",
            }
        },
    }

    assert set(expected) == set(tools)
    for name, expected_hints in expected.items():
        annotations = tools[name].annotations
        actual_hints = (
            annotations.readOnlyHint,
            annotations.destructiveHint,
            annotations.idempotentHint,
            annotations.openWorldHint,
        )
        assert actual_hints == expected_hints, name


def test_server_instructions_put_connection_and_safety_first():
    first_paragraph = mcp.instructions.split("\n\n", 1)[0]

    assert len(first_paragraph) <= 512
    assert "Blender add-on" in first_paragraph
    assert "execute_blender_code runs arbitrary Python" in first_paragraph
    assert "verify it again afterward" in first_paragraph
