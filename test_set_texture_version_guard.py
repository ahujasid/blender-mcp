"""Static structural check for the set_texture ARM version guard.

Blender 4.0 removed ShaderNodeSeparateRGB (renamed to ShaderNodeSeparateColor,
added in 3.3). This test asserts addon.py branches on bpy.app.version and wires
the correct socket names on each branch, without running Blender.
"""
import ast
import pathlib

ADDON = pathlib.Path(__file__).with_name("addon.py")


def _source():
    return ADDON.read_text()


def test_addon_parses():
    # The file must remain syntactically valid Python after the edit.
    ast.parse(_source())


def test_has_version_guard():
    src = _source()
    assert "bpy.app.version >= (4, 0)" in src, \
        "expected a runtime guard `bpy.app.version >= (4, 0)`"


def test_uses_separate_color_on_4x():
    src = _source()
    assert "ShaderNodeSeparateColor" in src, \
        "expected ShaderNodeSeparateColor node for Blender 4.0+"


def test_keeps_separate_rgb_for_legacy():
    src = _source()
    assert "ShaderNodeSeparateRGB" in src, \
        "pre-4.0 path must keep the original ShaderNodeSeparateRGB node"


def test_socket_name_locals_present():
    # Both branches must bind the channel-name locals used downstream.
    src = _source()
    for token in ("in_socket", "ch_r", "ch_g", "ch_b"):
        assert token in src, f"expected downstream channel local `{token}`"
    # 4.0+ socket names
    for token in ("'Color'", "'Red'", "'Green'", "'Blue'"):
        assert token in src, f"expected 4.0+ socket name {token}"
    # legacy socket names
    for token in ("'Image'", "'R'", "'G'", "'B'"):
        assert token in src, f"expected legacy socket name {token}"


def test_no_literal_separate_rgb_output_indexing():
    # After the fix, downstream wiring must go through ch_* locals,
    # not `separate_rgb.outputs['G'|'B'|'R']` literals.
    src = _source()
    for bad in ("separate_rgb.outputs['G']",
                "separate_rgb.outputs['B']",
                "separate_rgb.outputs['R']"):
        assert bad not in src, \
            f"downstream wiring still uses literal {bad}; convert to ch_* local"
