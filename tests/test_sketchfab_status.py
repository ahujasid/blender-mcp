"""Regression coverage for Sketchfab availability reporting."""
import importlib.util
import sys
import types

from conftest import ROOT_ADDON as ADDON


def _load_addon(monkeypatch, scene):
    bpy = types.ModuleType("bpy")
    bpy.context = types.SimpleNamespace(scene=scene)
    bpy.types = types.SimpleNamespace(
        AddonPreferences=object,
        Operator=object,
        Panel=object,
        Scene=type("Scene", (), {}),
    )

    props = types.ModuleType("bpy.props")
    for name in ("BoolProperty", "EnumProperty", "FloatProperty", "IntProperty", "StringProperty"):
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

    requests = types.ModuleType("requests")
    requests.utils = types.SimpleNamespace(default_headers=dict)
    requests.exceptions = types.SimpleNamespace(Timeout=TimeoutError)
    monkeypatch.setitem(sys.modules, "requests", requests)

    spec = importlib.util.spec_from_file_location("blender_mcp_addon_test", ADDON)
    addon = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(addon)
    return addon


def _scene(sketchfab_enabled):
    return types.SimpleNamespace(
        blendermcp_use_polyhaven=False,
        blendermcp_use_hyper3d=False,
        blendermcp_use_hunyuan3d=False,
        blendermcp_use_sketchfab=sketchfab_enabled,
    )


def test_disabled_sketchfab_does_not_report_a_saved_key_as_ready(monkeypatch):
    addon = _load_addon(monkeypatch, _scene(sketchfab_enabled=False))
    server = addon.BlenderMCPServer()
    monkeypatch.setattr(server, "_get_sketchfab_api_key", lambda: "saved-key")

    def request_should_not_run(*_args, **_kwargs):
        raise AssertionError("must not validate a disabled integration")

    monkeypatch.setattr(
        addon.requests,
        "get",
        request_should_not_run,
        raising=False,
    )

    status = server.get_sketchfab_status()
    command = server._execute_command_internal({"type": "search_sketchfab_models"})

    assert status["enabled"] is False
    assert "currently disabled" in status["message"]
    assert command == {"status": "error", "message": "Unknown command type: search_sketchfab_models"}


def test_enabled_sketchfab_reports_a_valid_key_as_ready(monkeypatch):
    addon = _load_addon(monkeypatch, _scene(sketchfab_enabled=True))
    server = addon.BlenderMCPServer()
    monkeypatch.setattr(server, "_get_sketchfab_api_key", lambda: "saved-key")

    class Response:
        status_code = 200

        @staticmethod
        def json():
            return {"username": "artist"}

    monkeypatch.setattr(addon.requests, "get", lambda *_args, **_kwargs: Response(), raising=False)

    assert server.get_sketchfab_status() == {
        "enabled": True,
        "message": "Sketchfab integration is enabled and ready to use. Logged in as: artist",
    }
