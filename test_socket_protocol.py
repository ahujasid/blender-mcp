"""Tests for the versioned TCP bridge between the MCP server and Blender."""

import ast
import json
import pathlib
import socket
import threading
import time

from blender_mcp.server import BlenderConnection


ROOT = pathlib.Path(__file__).parent
ADDON = ROOT / "addon.py"


def _load_addon_protocol_helpers():
    """Load pure protocol helpers without importing Blender's bpy module."""
    tree = ast.parse(ADDON.read_text(encoding="utf-8"))
    selected = [
        node
        for node in tree.body
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id
                in {
                    "SOCKET_PROTOCOL_VERSION",
                    "MAX_SOCKET_MESSAGE_BYTES",
                    "COMMAND_TIMEOUT_SECONDS",
                }
                for target in node.targets
            )
        )
        or (
            isinstance(node, ast.FunctionDef)
            and node.name
            in {"_encode_socket_message", "_decode_socket_messages"}
        )
    ]
    namespace = {"json": json}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(ADDON), "exec"), namespace)
    return namespace


def test_addon_protocol_handles_fragmented_framed_message():
    helpers = _load_addon_protocol_helpers()
    decode = helpers["_decode_socket_messages"]
    encoded = helpers["_encode_socket_message"](
        {"type": "get_scene_info", "params": {"label": "ทดสอบ"}}
    )

    messages, tail = decode(encoded[:13])
    assert messages == []
    messages, tail = decode(tail + encoded[13:])

    assert messages == [
        {"type": "get_scene_info", "params": {"label": "ทดสอบ"}}
    ]
    assert tail == b""


def test_addon_protocol_accepts_legacy_unframed_message():
    helpers = _load_addon_protocol_helpers()
    decode = helpers["_decode_socket_messages"]

    messages, tail = decode(b'{"type":"get_scene_info","params":{}}')

    assert messages == [{"type": "get_scene_info", "params": {}}]
    assert tail == b""


def test_server_receives_fragmented_framed_response():
    client, peer = socket.socketpair()
    connection = BlenderConnection("localhost", 9876, sock=client)
    payload = (
        b'{"status":"success","result":{"name":"Cube"},'
        b'"request_id":"abc","protocol_version":2}\n'
    )

    def sender():
        peer.sendall(payload[:17])
        time.sleep(0.01)
        peer.sendall(payload[17:])

    thread = threading.Thread(target=sender)
    thread.start()
    try:
        response = connection.receive_full_response(client)
    finally:
        thread.join()
        client.close()
        peer.close()

    assert json.loads(response) == {
        "status": "success",
        "result": {"name": "Cube"},
        "request_id": "abc",
        "protocol_version": 2,
    }


def test_server_serializes_concurrent_commands_and_matches_ids():
    client, peer = socket.socketpair()
    connection = BlenderConnection("localhost", 9876, sock=client)
    received = []

    def fake_addon():
        buffer = b""
        while len(received) < 2:
            buffer += peer.recv(8192)
            while b"\n" in buffer:
                raw, buffer = buffer.split(b"\n", 1)
                if not raw:
                    continue
                command = json.loads(raw)
                received.append(command)
                response = {
                    "status": "success",
                    "result": command["type"],
                    "request_id": command["request_id"],
                    "protocol_version": 2,
                }
                peer.sendall(json.dumps(response).encode() + b"\n")

    addon_thread = threading.Thread(target=fake_addon)
    addon_thread.start()
    results = {}

    def call(name):
        results[name] = connection.send_command(name)

    callers = [
        threading.Thread(target=call, args=("first",)),
        threading.Thread(target=call, args=("second",)),
    ]
    for caller in callers:
        caller.start()
    for caller in callers:
        caller.join()
    addon_thread.join()
    client.close()
    peer.close()

    assert results == {"first": "first", "second": "second"}
    assert len({command["request_id"] for command in received}) == 2
