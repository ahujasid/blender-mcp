"""Regression tests for the add-on's deferred socket auto-start lifecycle.

The add-on cannot be imported without Blender, so the small auto-start helper
functions are lifted out with AST and executed against a minimal bpy stub.
"""

from __future__ import annotations

import ast
import socket
import types
from typing import ClassVar

from conftest import ROOT_ADDON

_AUTOSTART_FUNCTIONS = {
    "_blendermcp_port_has_listener",
    "_blendermcp_ensure_server_running",
    "_blendermcp_schedule_auto_start",
    "_blendermcp_load_post",
    "_blendermcp_register_auto_start",
    "_blendermcp_unregister_auto_start",
}


class _Timers:
    def __init__(self):
        self.registrations = {}

    def register(self, fn, first_interval=0.0, persistent=False):
        self.registrations[fn] = {
            "first_interval": first_interval,
            "persistent": persistent,
        }

    def unregister(self, fn):
        self.registrations.pop(fn)

    def is_registered(self, fn):
        return fn in self.registrations


class _Server:
    instances: ClassVar[list[_Server]] = []
    failures_before_start = 0

    def __init__(self, port):
        self.port = port
        self.running = False
        self.start_attempts = 0
        self.__class__.instances.append(self)

    def start(self):
        self.start_attempts += 1
        if self.start_attempts > self.__class__.failures_before_start:
            self.running = True


def _load_autostart_helpers():
    source = ROOT_ADDON.read_text(encoding="utf-8")
    tree = ast.parse(source)
    body = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in _AUTOSTART_FUNCTIONS
    ]
    assert {node.name for node in body} == _AUTOSTART_FUNCTIONS

    timers = _Timers()
    scene = types.SimpleNamespace(
        blendermcp_auto_start_server=True,
        blendermcp_port=9876,
        blendermcp_server_running=False,
    )
    bpy = types.SimpleNamespace(
        app=types.SimpleNamespace(
            background=False,
            timers=timers,
            handlers=types.SimpleNamespace(load_post=[]),
        ),
        context=types.SimpleNamespace(scene=scene),
        types=types.SimpleNamespace(),
    )
    namespace = {
        "bpy": bpy,
        "socket": socket,
        "persistent": lambda fn: fn,
        "BlenderMCPServer": _Server,
        "_user_stopped_server": False,
    }
    exec(  # noqa: S102 - execute only the selected functions from our own source.
        compile(ast.Module(body=body, type_ignores=[]), "<addon>", "exec"), namespace
    )
    namespace["_blendermcp_port_has_listener"] = lambda host, port: False
    return namespace, bpy, timers, scene


def setup_function():
    _Server.instances = []
    _Server.failures_before_start = 0


def test_registration_defers_start_and_is_idempotent():
    namespace, bpy, timers, _scene = _load_autostart_helpers()
    register_auto_start = namespace["_blendermcp_register_auto_start"]
    ensure_running = namespace["_blendermcp_ensure_server_running"]
    load_post = namespace["_blendermcp_load_post"]

    register_auto_start()
    register_auto_start()

    assert _Server.instances == []
    assert bpy.app.handlers.load_post == [load_post]
    assert timers.registrations == {
        ensure_running: {"first_interval": 0.5, "persistent": True}
    }


def test_timer_retries_a_failed_start_then_marks_scene_running():
    namespace, bpy, _timers, scene = _load_autostart_helpers()
    ensure_running = namespace["_blendermcp_ensure_server_running"]
    _Server.failures_before_start = 1

    assert ensure_running() == 1.0
    server = bpy.types.blendermcp_server
    assert server.start_attempts == 1
    assert scene.blendermcp_server_running is False

    assert ensure_running() is None
    assert server.start_attempts == 2
    assert scene.blendermcp_server_running is True


def test_load_post_restores_a_missing_timer():
    namespace, _bpy, timers, _scene = _load_autostart_helpers()
    ensure_running = namespace["_blendermcp_ensure_server_running"]

    namespace["_blendermcp_load_post"](None)

    assert timers.is_registered(ensure_running)
    assert timers.registrations[ensure_running]["persistent"] is True


def test_disabled_auto_start_does_not_create_a_server():
    namespace, _bpy, _timers, scene = _load_autostart_helpers()
    scene.blendermcp_auto_start_server = False

    assert namespace["_blendermcp_ensure_server_running"]() is None
    assert _Server.instances == []


def test_occupied_port_does_not_create_a_competing_server():
    namespace, _bpy, _timers, scene = _load_autostart_helpers()
    namespace["_blendermcp_port_has_listener"] = lambda host, port: True

    assert namespace["_blendermcp_ensure_server_running"]() is None
    assert _Server.instances == []
    assert scene.blendermcp_server_running is False


def test_background_mode_does_not_schedule_retries():
    namespace, bpy, _timers, _scene = _load_autostart_helpers()
    bpy.app.background = True

    assert namespace["_blendermcp_ensure_server_running"]() is None
    assert _Server.instances == []


def test_missing_scene_retries_without_binding_the_default_port():
    namespace, bpy, _timers, _scene = _load_autostart_helpers()
    bpy.context.scene = None

    assert namespace["_blendermcp_ensure_server_running"]() == 0.5
    assert _Server.instances == []


def test_stopped_server_retargets_to_the_loaded_scene_port():
    namespace, bpy, _timers, scene = _load_autostart_helpers()
    server = _Server(port=9876)
    bpy.types.blendermcp_server = server
    scene.blendermcp_port = 9999

    assert namespace["_blendermcp_ensure_server_running"]() is None
    assert server.port == 9999
    assert server.running is True


def test_manual_disconnect_survives_loading_another_file():
    namespace, _bpy, _timers, scene = _load_autostart_helpers()
    namespace["_user_stopped_server"] = True

    assert namespace["_blendermcp_ensure_server_running"]() is None
    assert _Server.instances == []
    assert scene.blendermcp_server_running is False


def test_registration_clears_manual_disconnect_for_an_addon_reload():
    namespace, _bpy, _timers, _scene = _load_autostart_helpers()
    namespace["_user_stopped_server"] = True

    namespace["_blendermcp_register_auto_start"]()

    assert namespace["_user_stopped_server"] is False


def test_unregistration_removes_handler_and_pending_timer():
    namespace, bpy, timers, _scene = _load_autostart_helpers()
    register_auto_start = namespace["_blendermcp_register_auto_start"]
    unregister_auto_start = namespace["_blendermcp_unregister_auto_start"]

    register_auto_start()
    unregister_auto_start()

    assert bpy.app.handlers.load_post == []
    assert timers.registrations == {}
