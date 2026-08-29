"""Regression coverage for ND (HugeMenace) availability reporting."""

import importlib.util
import sys
import types

from conftest import ROOT_ADDON as ADDON


def _load_addon(monkeypatch, scene, nd_installed=False):
    bpy = types.ModuleType("bpy")
    bpy.context = types.SimpleNamespace(scene=scene)
    bpy.types = types.SimpleNamespace(
        AddonPreferences=object,
        Operator=object,
        Panel=object,
        Scene=type("Scene", (), {}),
    )

    ops = types.SimpleNamespace()
    if nd_installed:
        ops.nd = types.SimpleNamespace(bool_vanilla=lambda *_a, **_k: {"FINISHED"})
    bpy.ops = ops

    props = types.ModuleType("bpy.props")
    for name in (
        "BoolProperty",
        "EnumProperty",
        "FloatProperty",
        "IntProperty",
        "StringProperty",
    ):
        setattr(props, name, lambda **_kwargs: None)
    bpy.props = props

    handlers = types.ModuleType("bpy.app.handlers")
    handlers.persistent = lambda fn: fn
    handlers.undo_post = []
    handlers.redo_post = []
    handlers.depsgraph_update_post = []

    app = types.ModuleType("bpy.app")
    app.version = (4, 2, 0)
    app.version_string = "4.2.0"
    app.background = False
    app.handlers = handlers
    app.timers = types.SimpleNamespace(
        is_registered=lambda *_a, **_k: False,
        register=lambda *_a, **_k: None,
        unregister=lambda *_a, **_k: None,
    )
    bpy.app = app

    monkeypatch.setitem(sys.modules, "bpy", bpy)
    monkeypatch.setitem(sys.modules, "bpy.props", props)
    monkeypatch.setitem(sys.modules, "bpy.app", app)
    monkeypatch.setitem(sys.modules, "bpy.app.handlers", handlers)
    monkeypatch.setitem(sys.modules, "mathutils", types.ModuleType("mathutils"))
    monkeypatch.setitem(sys.modules, "bmesh", types.ModuleType("bmesh"))

    requests = types.ModuleType("requests")
    requests.utils = types.SimpleNamespace(default_headers=dict)
    requests.exceptions = types.SimpleNamespace(Timeout=TimeoutError)
    monkeypatch.setitem(sys.modules, "requests", requests)

    spec = importlib.util.spec_from_file_location("blender_mcp_addon_test", ADDON)
    addon = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(addon)
    return addon


def _scene(nd_enabled):
    return types.SimpleNamespace(
        blendermcp_use_polyhaven=False,
        blendermcp_use_hyper3d=False,
        blendermcp_use_hunyuan3d=False,
        blendermcp_use_sketchfab=False,
        blendermcp_use_nd=nd_enabled,
    )


def test_disabled_nd_is_absent_from_dispatch(monkeypatch):
    addon = _load_addon(monkeypatch, _scene(nd_enabled=False), nd_installed=True)
    server = addon.BlenderMCPServer()

    status = server.get_nd_status()
    command = server._execute_command_internal({"type": "nd_boolean"})

    assert status["enabled"] is False
    assert "currently disabled" in status["message"]
    assert command == {
        "status": "error",
        "message": "Unknown command type: nd_boolean",
    }


def test_enabled_nd_without_addon_installed_is_reported_as_not_ready(monkeypatch):
    addon = _load_addon(monkeypatch, _scene(nd_enabled=True), nd_installed=False)
    server = addon.BlenderMCPServer()

    status = server.get_nd_status()

    assert status["enabled"] is False
    assert "does not appear to be" in status["message"]


def test_enabled_nd_with_addon_installed_is_ready(monkeypatch):
    addon = _load_addon(monkeypatch, _scene(nd_enabled=True), nd_installed=True)
    server = addon.BlenderMCPServer()

    status = server.get_nd_status()

    assert status == {
        "enabled": True,
        "message": "ND integration is enabled and the ND addon is installed and ready to use.",
    }
