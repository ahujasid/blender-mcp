"""The model-facing surface: a handful of tools, guides on demand, and
observation scripts that run through execute_code."""

import ast
import asyncio

from blender_mcp import blender_scripts, guides, server
from blender_mcp.openai_apps import is_app_only

MODEL_TOOLS = {
    "get_addon_status", "disable_telemetry", "get_scene_info", "execute_blender_code",
    "record_trajectory_feedback", "look", "generate_3d", "search_assets", "import_asset", "get_guide",
}


def test_model_sees_only_the_consolidated_tools():
    tools = asyncio.run(server.mcp.list_tools())
    assert {t.name for t in tools if not is_app_only(t)} == MODEL_TOOLS


def test_every_guide_has_a_title_summary_and_body():
    found = guides.all_guides()
    assert {"bpy", "scene", "level-design", "animation", "rigging", "retopology", "materials"} <= set(found)
    for guide in found.values():
        assert guide.title and guide.summary and guide.body.startswith("# ")


def test_get_guide_lists_topics_and_handles_unknown_ones():
    tools = {t.name: t for t in asyncio.run(server.mcp.list_tools())}
    assert "retopology:" in tools["get_guide"].description
    assert guides.get("RIGGING").startswith("# Rigging")
    assert "Available guides" in guides.get("nope")


def test_guides_are_published_as_resources():
    uris = {str(r.uri) for r in asyncio.run(server.mcp.list_resources())}
    assert "guide://rigging" in uris


def test_scripts_compile_and_never_raise_systemexit():
    # The addon catches Exception around execute_code but not SystemExit.
    for script in (blender_scripts.SCENE_SUMMARY, blender_scripts.LOOK, blender_scripts.BOUNDS):
        code = blender_scripts.build(script, {"mode": "angles", "target": None, "flag": True, "none": None})
        ast.parse(code)
        assert "SystemExit" not in code and "sys.exit" not in code


def test_script_arguments_round_trip_json_only_values():
    code = blender_scripts.build("return ARGS", {"a": True, "b": None, "c": ["x'y\"z"]})
    namespace = {}
    import contextlib, io
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        exec(code, namespace)
    assert blender_scripts.parse_result("noise\n" + out.getvalue()) == {"a": True, "b": None, "c": ["x'y\"z"]}


def test_look_caption_reports_mesh_and_rig_problems():
    caption = server._look_caption({
        "mode": "topology", "views": ["three_quarter"], "targets": 1, "center": [0, 0, 1], "size": [1, 1, 2],
        "mesh_stats": [{"object": "Body", "verts": 8, "faces": 6, "tris": 0, "quads": 6, "ngons": 0,
                        "non_manifold_edges": 2, "boundary_edges": 0, "loose_verts": 1, "poles": 8,
                        "modifiers": []}],
        "rig_stats": [{"mesh": "Body", "armature": "Rig", "vertices": 8, "unweighted_vertices": 3,
                       "deform_bones_without_group": ["hand.L"]}],
    })
    assert "2 non-manifold edges" in caption
    assert "3 of 8 vertices unweighted" in caption and "hand.L" in caption


def test_scene_summary_formatting():
    text = server._format_scene_summary({
        "header": {"scene": "Scene", "file": "(unsaved)", "blender": "4.2.0", "engine": "CYCLES",
                   "frames": [1, 250, 1], "fps": 24, "resolution": [1920, 1080], "camera": "Camera",
                   "world_hdri": None, "unit_scale": 1.0, "object_counts": {"mesh": 60},
                   "selected": [], "active": None, "mode": "OBJECT"},
        "lines": ["Cube | mesh | at (0, 0, 1)"], "total": 60, "shown": 1,
    })
    assert "Cube | mesh" in text
    assert "59 more" in text


class _Blender:
    def __init__(self, replies):
        self.replies = replies
        self.sent = []

    def send_command(self, command, params=None, read_only=False):
        self.sent.append((command, params))
        reply = self.replies.get(command)
        if isinstance(reply, Exception):
            raise reply
        return reply


def test_texture_import_applies_the_material(monkeypatch):
    blender = _Blender({
        "download_polyhaven_asset": {"success": True, "message": "Downloaded", "material": "Rock",
                                     "maps": ["diffuse"]},
        "set_texture": {"success": True, "material": "Rock", "maps": ["diffuse"]},
    })
    monkeypatch.setattr(server, "get_blender_connection", lambda: blender)
    reply = asyncio.run(server.import_asset(None, source="polyhaven", id="rock", asset_type="textures",
                                            apply_to=["Ground"]))
    assert ("set_texture", {"object_name": "Ground", "texture_id": "rock"}) in blender.sent
    assert "Applied" in reply and server.POLYHAVEN_UNUSED_NOTE not in reply


def test_sketchfab_import_needs_a_size():
    reply = asyncio.run(server.import_asset(None, source="sketchfab", id="abc"))
    assert reply.startswith("Error") and "target_size" in reply


def test_a_missing_library_command_means_switched_off_or_outdated(monkeypatch):
    from blender_mcp.addon_manager import EXPECTED_ADDON_PROTOCOL_VERSION, AddonHandshake

    blender = _Blender({"search_sketchfab_models": Exception("Unknown command type: search_sketchfab_models")})
    monkeypatch.setattr(server, "get_blender_connection", lambda: blender)

    current = AddonHandshake(True, EXPECTED_ADDON_PROTOCOL_VERSION, [2, 1], [], "4.2", "native")
    monkeypatch.setattr(server, "_addon_handshake", current)
    reply = asyncio.run(server.search_assets(None, source="sketchfab", query="car"))
    assert "switched off" in reply and "install-addon" not in reply

    behind = AddonHandshake(False, 9, [2, 0], [], "4.2", "native")
    monkeypatch.setattr(server, "_addon_handshake", behind)
    reply = asyncio.run(server.search_assets(None, source="sketchfab", query="car"))
    assert "install-addon" in reply
