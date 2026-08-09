import json
import socket
import threading

from blender_mcp.socket_framing import (
    pack_json_message,
    receive_framed_json,
    send_json_message,
)


def test_pack_roundtrip_length():
    payload = {"status": "success", "result": {"ok": True}}
    raw = pack_json_message(payload)
    assert len(raw) == 4 + len(json.dumps(payload).encode("utf-8"))


def test_send_receive_over_socket():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    host, port = server.getsockname()
    payload = {"type": "ping", "params": {"n": 1}}
    result = {}

    def client():
        c = socket.create_connection((host, port), timeout=5)
        send_json_message(c, payload)
        result["echo"] = receive_framed_json(c, timeout=5)
        c.close()

    t = threading.Thread(target=client)
    t.start()
    conn, _ = server.accept()
    msg = receive_framed_json(conn, timeout=5)
    assert msg == payload
    send_json_message(conn, {"status": "success", "result": msg})
    conn.close()
    t.join(timeout=5)
    server.close()
    assert result["echo"]["status"] == "success"
