import pytest

from blender_mcp.trajectory import SEMANTIC_ACTIONS, semantic_action_for_tool

NEW_MESH_MODEL_TOOLS = [
    "mesh_create_primitive",
    "mesh_extrude",
    "mesh_inset",
    "mesh_bevel",
    "mesh_bridge",
    "mesh_boolean",
    "mesh_subdivide",
    "mesh_remesh",
    "mesh_solidify",
    "model_from_reference",
    "model_generate_from_description",
    "model_match_reference",
    "model_blockout",
    "model_refine",
    "model_detail",
    "model_symmetrize",
    "model_mirror",
    "model_array",
    "model_radial_array",
]


@pytest.mark.parametrize("tool_name", NEW_MESH_MODEL_TOOLS)
def test_new_mesh_model_tools_have_a_known_semantic_action(tool_name):
    assert tool_name in SEMANTIC_ACTIONS
    assert semantic_action_for_tool(tool_name) != "UNKNOWN"
