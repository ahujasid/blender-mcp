"""Blender headless entrypoint with blocking keep-alive loop.

In Blender 5.x --background mode, bpy.app.timers do not prevent Blender from
exiting after the script finishes. This script uses a blocking while-loop in
the main thread instead.

Commands are executed directly in the socket thread (BMA_HEADLESS=1 path in
addon.py), so blocking the main thread is safe.

Usage:
    BMA_HEADLESS=1 BMA_SOCKET_HOST=127.0.0.1 BMA_SOCKET_PORT=9876 \
        blender --background --factory-startup \
        --python blender-mcp-bma/headless/start_headless_blocking.py
"""
from __future__ import annotations

import os
import signal
import sys
import time

_ADDON_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ADDON_DIR not in sys.path:
    sys.path.insert(0, _ADDON_DIR)

import bpy  # noqa: E402

_HOST = os.environ.get("BMA_SOCKET_HOST", "127.0.0.1")
_PORT = int(os.environ.get("BMA_SOCKET_PORT", "9876"))
_EXTERNAL_ASSETS = os.environ.get("BMA_ENABLE_EXTERNAL_ASSETS", "false").lower() in (
    "1", "true", "yes"
)

import addon as _addon

_addon.register()

scene = bpy.context.scene
scene.blendermcp_port = _PORT
scene.blendermcp_use_polyhaven = _EXTERNAL_ASSETS
scene.blendermcp_use_hyper3d = _EXTERNAL_ASSETS
scene.blendermcp_use_sketchfab = _EXTERNAL_ASSETS
if hasattr(scene, "blendermcp_use_hunyuan3d"):
    scene.blendermcp_use_hunyuan3d = _EXTERNAL_ASSETS

server = _addon.BlenderMCPServer(host=_HOST, port=_PORT)
server.start()
scene.blendermcp_server_running = True
bpy.types.blendermcp_server = server

print(f"[BMA headless] Server listening on {_HOST}:{_PORT}  external_assets={_EXTERNAL_ASSETS}")

_shutdown = False


def _handle_signal(signum, frame):
    global _shutdown
    print(f"[BMA headless] Signal {signum}, shutting down...")
    _shutdown = True


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)

# Block main thread; commands run directly in socket thread (BMA_HEADLESS=1).
while not _shutdown and server.running:
    time.sleep(0.5)

server.stop()
scene.blendermcp_server_running = False
print("[BMA headless] Shutdown complete.")
