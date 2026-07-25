#!/usr/bin/env python3
"""
Stress-test Blender MCP socket (Issue #279 repro helper).

Requires Blender GUI + community addon listening on BLENDER_HOST:9876.

Usage:
  BLENDER_HOST=172.19.96.1 uv run --directory . python scripts/benchmark_mcp_socket.py --iterations 20
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import statistics
import time

from blender_mcp.socket_framing import pack_json_message, receive_framed_bytes

DEFAULT_HOST = os.getenv("BLENDER_HOST", "localhost")
DEFAULT_PORT = int(os.getenv("BLENDER_PORT", "9876"))


def run_command(host: str, port: int, command_type: str, timeout: float) -> tuple[float, int]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    start = time.perf_counter()
    try:
        sock.connect((host, port))
        command = {"type": command_type, "params": {}}
        sock.sendall(pack_json_message(command))
        data = receive_framed_bytes(sock, timeout=timeout)
        elapsed = time.perf_counter() - start
        return elapsed, len(data)
    finally:
        sock.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark MCP socket commands")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--command", default="get_scene_info")
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()

    timings: list[float] = []
    sizes: list[int] = []

    print(f"Target {args.host}:{args.port} command={args.command} n={args.iterations}")
    for i in range(args.iterations):
        try:
            elapsed, size = run_command(args.host, args.port, args.command, args.timeout)
            timings.append(elapsed)
            sizes.append(size)
            print(f"  {i + 1:3d}: {elapsed:6.2f}s  {size:6d} bytes")
        except Exception as exc:
            print(f"  {i + 1:3d}: FAIL {exc}")
            break

    if timings:
        print(
            f"Summary: n={len(timings)} "
            f"min={min(timings):.2f}s p50={statistics.median(timings):.2f}s "
            f"max={max(timings):.2f}s avg={statistics.mean(timings):.2f}s"
        )


if __name__ == "__main__":
    main()
