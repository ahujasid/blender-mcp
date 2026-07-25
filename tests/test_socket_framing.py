#!/usr/bin/env python3
"""Unit tests for length-prefixed socket framing (Issue #219 cluster)."""

import io
import json
import socket
import struct
import unittest

from blender_mcp.socket_framing import (
    pack_json_message,
    receive_framed_bytes,
    receive_framed_json,
    send_json_message,
)


class MockSocket:
    """Feed preloaded bytes through socket-like recv()."""

    def __init__(self, data: bytes):
        self._buffer = io.BytesIO(data)
        self.timeout = None

    def recv(self, size: int) -> bytes:
        return self._buffer.read(size)

    def sendall(self, data: bytes) -> None:
        pass

    def settimeout(self, timeout: float) -> None:
        self.timeout = timeout


class TestSocketFraming(unittest.TestCase):
    def test_length_prefix_small_json(self):
        payload = {"status": "success", "result": {"object_count": 3}}
        framed = pack_json_message(payload)
        result = receive_framed_json(MockSocket(framed))
        self.assertEqual(result, payload)

    def test_length_prefix_large_json(self):
        payload = {"objects": [{"name": f"obj_{i}"} for i in range(10_000)]}
        framed = pack_json_message(payload)
        result = receive_framed_json(MockSocket(framed))
        self.assertEqual(len(result["objects"]), 10_000)

    def test_receive_partial_chunks(self):
        payload = {"status": "ok", "data": "x" * 20_000}
        framed = pack_json_message(payload)
        # Split after header and mid-body to simulate TCP chunking
        split_a = len(framed) // 3
        split_b = (2 * len(framed)) // 3
        chunks = [framed[:split_a], framed[split_a:split_b], framed[split_b:]]
        mock = MockSocket(b"".join(chunks))
        body = receive_framed_bytes(mock)
        self.assertEqual(json.loads(body.decode()), payload)

    def test_truncated_body_raises(self):
        payload = {"status": "success"}
        body = json.dumps(payload).encode()
        truncated = struct.pack(">I", len(body) + 50) + body
        with self.assertRaises(ConnectionError):
            receive_framed_bytes(MockSocket(truncated), timeout=1.0)

    def test_send_roundtrip_memory_socket(self):
        client, server = socket.socketpair()
        try:
            payload = {"status": "success", "result": {"name": "Scene"}}
            send_json_message(client, payload)
            client.shutdown(socket.SHUT_WR)
            received = receive_framed_json(server, timeout=5.0)
            self.assertEqual(received, payload)
        finally:
            client.close()
            server.close()


if __name__ == "__main__":
    unittest.main()
