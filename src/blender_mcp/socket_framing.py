"""Length-prefixed JSON framing for Blender MCP socket protocol."""

from __future__ import annotations

import json
import socket
import struct
from typing import Any

HEADER_SIZE = 4
HEADER_FORMAT = ">I"
MAX_MESSAGE_BYTES = 256 * 1024 * 1024


def pack_json_message(payload: dict[str, Any]) -> bytes:
    body = json.dumps(payload).encode("utf-8")
    return struct.pack(HEADER_FORMAT, len(body)) + body


def send_json_message(sock: socket.socket, payload: dict[str, Any]) -> None:
    sock.sendall(pack_json_message(payload))


def receive_framed_bytes(sock: socket.socket, timeout: float = 180.0) -> bytes:
    sock.settimeout(timeout)

    length_data = b""
    while len(length_data) < HEADER_SIZE:
        chunk = sock.recv(HEADER_SIZE - len(length_data))
        if not chunk:
            raise ConnectionError("Socket closed before length prefix")
        length_data += chunk

    (length,) = struct.unpack(HEADER_FORMAT, length_data)
    if length > MAX_MESSAGE_BYTES:
        raise ValueError(f"Framed message too large: {length} bytes")

    body = b""
    while len(body) < length:
        chunk = sock.recv(min(8192, length - len(body)))
        if not chunk:
            raise ConnectionError("Socket closed before full message body")
        body += chunk

    return body


def receive_framed_json(sock: socket.socket, timeout: float = 180.0) -> dict[str, Any]:
    return json.loads(receive_framed_bytes(sock, timeout).decode("utf-8"))
