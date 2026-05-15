"""Headless-safe socket mode for blender-mcp-bma.

In Blender's --background mode there is no window and no event loop, so modal
operators cannot be used.  This module provides a persistent bpy.app.timers-based
keep-alive that:

  - Keeps Blender alive by returning a non-None delay from the timer callback.
  - Executes commands in the main thread via bpy.app.timers (the existing addon
    mechanism), which works correctly in --background.
  - Shuts Blender down cleanly when a SIGTERM/SIGINT arrives or when the socket
    server thread has already stopped.

Usage (from start_blender_mcp_headless.py):

    from headless.headless_socket_mode import install_headless_keepalive
    install_headless_keepalive(server, shutdown_flag_getter, interval=0.5)
"""
from __future__ import annotations

import sys
from typing import Callable

import bpy  # type: ignore[import]

_KEEPALIVE_INTERVAL = 0.5  # seconds between timer ticks


def install_headless_keepalive(
    server: object,
    shutdown_flag_getter: Callable[[], bool],
    interval: float = _KEEPALIVE_INTERVAL,
) -> None:
    """Register a persistent timer that keeps Blender alive in --background mode.

    Args:
        server:               The BlenderMCPServer instance (has .running attribute
                              and .stop() method).
        shutdown_flag_getter: Callable returning True when shutdown is requested.
        interval:             Timer tick interval in seconds.
    """

    def _tick() -> float | None:
        """Called by bpy.app.timers on every tick.

        Returning a float reschedules the timer; returning None cancels it and
        allows Blender to exit normally.
        """
        want_shutdown = shutdown_flag_getter()
        server_dead = not getattr(server, "running", False)

        if want_shutdown or server_dead:
            _shutdown_blender(server)
            return None  # cancel timer → Blender exits

        return interval  # reschedule

    # persistent=True keeps the timer alive across file loads / scene changes.
    bpy.app.timers.register(_tick, first_interval=interval, persistent=True)
    print(f"[BMA headless] Headless keep-alive timer installed (interval={interval}s).")


def _shutdown_blender(server: object) -> None:
    """Stop the socket server and quit Blender."""
    try:
        if hasattr(server, "running") and server.running:
            server.stop()
    except Exception as exc:
        print(f"[BMA headless] Error stopping server: {exc}")

    if hasattr(bpy.types, "blendermcp_server"):
        try:
            del bpy.types.blendermcp_server
        except Exception:
            pass

    try:
        scene = bpy.context.scene
        if hasattr(scene, "blendermcp_server_running"):
            scene.blendermcp_server_running = False
    except Exception:
        pass

    print("[BMA headless] Shutdown complete.  Quitting Blender.")
    # sys.exit is cleaner than wm.quit_blender() when there is no window.
    sys.exit(0)
