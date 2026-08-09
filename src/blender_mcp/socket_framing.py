"""Length-prefixed JSON framing for the Blender MCP TCP protocol."""
from __future__ import annotations

import json
import socket
import struct
from typing import Any

HEADER_SIZE = 4
HEADER_FORMAT = ">I"
MAX_MESSAGE_BYTES = 64 * 1024 * 1024  # 64 MiB


def pack_json_message(payload: dict[str, Any]) -> bytes:
    body = json.dumps(payload).encode("utf-8")
    if len(body) > MAX_MESSAGE_BYTES:
        raise ValueError(f"Message too large: {len(body)} bytes")
    return struct.pack(HEADER_FORMAT, len(body)) + body


def send_json_message(sock: socket.socket, payload: dict[str, Any]) -> None:
    sock.sendall(pack_json_message(payload))


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Socket closed before full frame")
        buf += chunk
    return buf


def receive_framed_bytes(sock: socket.socket, timeout: float = 180.0) -> bytes:
    sock.settimeout(timeout)
    length_data = _recv_exact(sock, HEADER_SIZE)
    (length,) = struct.unpack(HEADER_FORMAT, length_data)
    if length <= 0 or length > MAX_MESSAGE_BYTES:
        raise ValueError(f"Invalid framed length: {length}")
    return _recv_exact(sock, length)


def receive_framed_json(sock: socket.socket, timeout: float = 180.0) -> dict[str, Any]:
    return json.loads(receive_framed_bytes(sock, timeout).decode("utf-8"))
