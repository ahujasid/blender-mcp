"""Headless entrypoint for blender-mcp-bma in benchmark mode.

Usage:
    blender --background --factory-startup --python headless/start_blender_mcp_headless.py

Environment variables (all optional):
    BMA_SOCKET_HOST       Bind host (default: localhost)
    BMA_SOCKET_PORT       Bind port (default: 9876)
    BMA_MCP_PROFILE       Tool-gating profile (default: minimal)
    BMA_ENABLE_EXTERNAL_ASSETS  Set to 'true' to enable asset integrations (default: false)
"""
from __future__ import annotations

import os
import signal
import sys
import time

# ---------------------------------------------------------------------------
# Ensure the addon directory is on sys.path so we can import addon.py directly
# ---------------------------------------------------------------------------
_ADDON_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ADDON_DIR not in sys.path:
    sys.path.insert(0, _ADDON_DIR)

import bpy  # noqa: E402  (only available inside Blender)

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------
_HOST = os.environ.get("BMA_SOCKET_HOST", "localhost")
_PORT = int(os.environ.get("BMA_SOCKET_PORT", "9876"))
_PROFILE = os.environ.get("BMA_MCP_PROFILE", "minimal")
_EXTERNAL_ASSETS = os.environ.get("BMA_ENABLE_EXTERNAL_ASSETS", "false").lower() in (
    "1", "true", "yes"
)

# ---------------------------------------------------------------------------
# Import and register the add-on
# ---------------------------------------------------------------------------
import addon as _addon  # noqa: E402

_addon.register()

# ---------------------------------------------------------------------------
# Configure scene properties written by register()
# ---------------------------------------------------------------------------
scene = bpy.context.scene

scene.blendermcp_port = _PORT

# Disable all external asset integrations unless explicitly opted in.
# BMA_PATCH: these flags are checked by addon handlers before making network calls.
scene.blendermcp_use_polyhaven = _EXTERNAL_ASSETS
scene.blendermcp_use_hyper3d = _EXTERNAL_ASSETS
scene.blendermcp_use_sketchfab = _EXTERNAL_ASSETS

if hasattr(scene, "blendermcp_use_hunyuan3d"):
    scene.blendermcp_use_hunyuan3d = _EXTERNAL_ASSETS

# ---------------------------------------------------------------------------
# Start the Blender-side socket server
# ---------------------------------------------------------------------------
bpy.types.blendermcp_server = _addon.BlenderMCPServer(host=_HOST, port=_PORT)
bpy.types.blendermcp_server.start()
scene.blendermcp_server_running = True

print(
    f"[BMA headless] Server listening on {_HOST}:{_PORT} "
    f"profile={_PROFILE} external_assets={_EXTERNAL_ASSETS}"
)

# ---------------------------------------------------------------------------
# Signal handlers: clean shutdown on SIGTERM / SIGINT
# ---------------------------------------------------------------------------
_shutdown_requested = False


def _shutdown(signum, frame):  # noqa: ARG001
    global _shutdown_requested
    print(f"[BMA headless] Received signal {signum}, shutting down…")
    _shutdown_requested = True


signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)

# ---------------------------------------------------------------------------
# Keep the Blender process alive via headless-safe persistent timer
# (modal operators require a window; --background has none)
# ---------------------------------------------------------------------------
from headless.headless_socket_mode import install_headless_keepalive  # BMA_PATCH

install_headless_keepalive(
    server=bpy.types.blendermcp_server,
    shutdown_flag_getter=lambda: _shutdown_requested,
)
