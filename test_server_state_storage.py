"""Regression checks for BlenderMCP server instance storage.

Runtime instances must not be attached to ``bpy.types`` because Blender treats
that namespace as a class registry and calls ``issubclass`` on its entries when
saving theme presets.
"""

import ast
import pathlib


ADDON = pathlib.Path(__file__).with_name("addon.py")


def _source():
    return ADDON.read_text()


def _load_server_state_helpers():
    tree = ast.parse(_source())
    selected_nodes = []

    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == "_server_instance" for target in node.targets):
                selected_nodes.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in {"_ensure_server", "_stop_server"}:
            selected_nodes.append(node)

    module = ast.Module(body=selected_nodes, type_ignores=[])
    ast.fix_missing_locations(module)

    class FakeServer:
        def __init__(self, port):
            self.port = port
            self.running = False
            self.stop_calls = 0

        def stop(self):
            self.stop_calls += 1
            self.running = False

    namespace = {"BlenderMCPServer": FakeServer}
    exec(compile(module, str(ADDON), "exec"), namespace)
    return namespace


def test_server_instance_is_not_stored_on_bpy_types():
    assert "bpy.types.blendermcp_server" not in _source()


def test_server_helpers_reuse_and_release_module_state():
    namespace = _load_server_state_helpers()

    first = namespace["_ensure_server"](9876)
    second = namespace["_ensure_server"](9001)

    assert second is first
    assert first.port == 9876

    namespace["_stop_server"]()
    assert first.stop_calls == 1
    assert namespace["_server_instance"] is None

    replacement = namespace["_ensure_server"](9001)
    assert replacement is not first
    assert replacement.port == 9001
