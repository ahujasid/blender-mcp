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
# Keep the Blender process alive via a modal timer operator
# ---------------------------------------------------------------------------

class BMA_OT_HeadlessKeepAlive(bpy.types.Operator):
    """Modal operator that keeps the headless Blender process running."""

    bl_idname = "bma.headless_keep_alive"
    bl_label = "BMA Headless Keep-Alive"

    _timer = None

    def modal(self, context, event):
        if event.type == "TIMER":
            if _shutdown_requested or not bpy.types.blendermcp_server.running:
                self.cancel(context)
                # Quit Blender cleanly
                bpy.ops.wm.quit_blender()
                return {"CANCELLED"}
        return {"PASS_THROUGH"}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        if hasattr(bpy.types, "blendermcp_server"):
            bpy.types.blendermcp_server.stop()
            del bpy.types.blendermcp_server
        scene.blendermcp_server_running = False
        print("[BMA headless] Shutdown complete.")


bpy.utils.register_class(BMA_OT_HeadlessKeepAlive)


def _start_keepalive():
    bpy.ops.bma.headless_keep_alive("INVOKE_DEFAULT")


# Schedule the operator to run after Blender finishes its startup sequence.
bpy.app.timers.register(_start_keepalive, first_interval=0.1)
