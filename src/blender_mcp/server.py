# blender_mcp_server.py
import asyncio
import base64
import json
import logging
import os
import socket
import sys
import tempfile
import threading
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from mcp.server.fastmcp import Context, FastMCP, Image

from .addon_manager import (
    EXPECTED_ADDON_PROTOCOL_VERSION,
    check_addon_status_on_startup,
    format_handshake_log,
    handshake_addon,
)
from .addon_manager import (
    run_cli as run_addon_cli,
)
from .consent_prompt import maybe_prompt_for_consent

# Import telemetry
from .telemetry import EventType, get_telemetry, record_startup
from .telemetry_decorator import telemetry_tool, trajectory_tool

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("BlenderMCPServer")

# Default configuration
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876

_addon_handshake = None
_addon_handshake_checked = False
_addon_handshake_lock = threading.Lock()


@dataclass
class BlenderConnection:
    host: str
    port: int
    sock: socket.socket = (
        None  # Changed from 'socket' to 'sock' to avoid naming conflict
    )
    # Serializes send+receive so two commands can never interleave on one socket.
    # Without this, a second command's response can be read as the first's, and
    # the stream stays desynced until the 180s timeout fires.
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def connect(self) -> bool:
        """Connect to the Blender addon socket server"""
        if self.sock:
            return True

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info(f"Connected to Blender at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Blender: {str(e)}")
            self.sock = None
            return False

    def disconnect(self):
        """Disconnect from the Blender addon"""
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error disconnecting from Blender: {str(e)}")
            finally:
                self.sock = None

    def receive_full_response(self, sock, buffer_size=8192):
        """Receive the complete response, potentially in multiple chunks"""
        chunks = []
        # Use a consistent timeout value that matches the addon's timeout
        sock.settimeout(180.0)  # Match the addon's timeout

        try:
            while True:
                try:
                    chunk = sock.recv(buffer_size)
                    if not chunk:
                        # If we get an empty chunk, the connection might be closed
                        if (
                            not chunks
                        ):  # If we haven't received anything yet, this is an error
                            raise Exception(
                                "Connection closed before receiving any data"
                            )
                        break

                    chunks.append(chunk)

                    # Check if we've received a complete JSON object
                    try:
                        data = b"".join(chunks)
                        json.loads(data.decode("utf-8"))
                        # If we get here, it parsed successfully
                        logger.info(f"Received complete response ({len(data)} bytes)")
                        return data
                    except json.JSONDecodeError:
                        # Incomplete JSON, continue receiving
                        continue
                except TimeoutError:
                    # If we hit a timeout during receiving, break the loop and try to use what we have
                    logger.warning("Socket timeout during chunked receive")
                    break
                except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                    logger.error(f"Socket connection error during receive: {str(e)}")
                    raise  # Re-raise to be handled by the caller
        except TimeoutError:
            logger.warning("Socket timeout during chunked receive")
        except Exception as e:
            logger.error(f"Error during receive: {str(e)}")
            raise

        # If we get here, we either timed out or broke out of the loop
        # Try to use what we have
        if chunks:
            data = b"".join(chunks)
            logger.info(f"Returning data after receive completion ({len(data)} bytes)")
            try:
                # Try to parse what we have
                json.loads(data.decode("utf-8"))
                return data
            except json.JSONDecodeError as exc:
                # If we can't parse it, it's incomplete
                raise Exception("Incomplete JSON response received") from exc
        else:
            raise Exception("No data received")

    def send_command(
        self, command_type: str, params: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Send a command to Blender and return the response"""
        # Hold the lock across send+receive: the response is matched to the
        # command purely by ordering on the stream, so overlapping calls would
        # hand each other's responses back.
        with self._lock:
            return self._send_command_locked(command_type, params)

    def _send_command_locked(
        self, command_type: str, params: dict[str, Any] = None
    ) -> dict[str, Any]:
        if not self.sock and not self.connect():
            raise ConnectionError("Not connected to Blender")

        command = {"type": command_type, "params": params or {}}

        try:
            # Log the command being sent
            logger.info(f"Sending command: {command_type} with params: {params}")

            # Send the command
            self.sock.sendall(json.dumps(command).encode("utf-8"))
            logger.info("Command sent, waiting for response...")

            # Set a timeout for receiving - use the same timeout as in receive_full_response
            self.sock.settimeout(180.0)  # Match the addon's timeout

            # Receive the response using the improved receive_full_response method
            response_data = self.receive_full_response(self.sock)
            logger.info(f"Received {len(response_data)} bytes of data")

            response = json.loads(response_data.decode("utf-8"))
            logger.info(f"Response parsed, status: {response.get('status', 'unknown')}")

            if response.get("status") == "error":
                logger.error(f"Blender error: {response.get('message')}")
                raise Exception(response.get("message", "Unknown error from Blender"))

            return response.get("result", {})
        except TimeoutError as exc:
            logger.error("Socket timeout while waiting for response from Blender")
            # Don't try to reconnect here - let the get_blender_connection handle reconnection
            # Just invalidate the current socket so it will be recreated next time
            self.sock = None
            raise Exception(
                "Timeout waiting for Blender response - try simplifying your request. If Blender is running headless (blender -b), commands never execute; run Blender with a GUI or via 'xvfb-run -a blender' instead"
            ) from exc
        except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
            logger.error(f"Socket connection error: {str(e)}")
            self.sock = None
            raise Exception(f"Connection to Blender lost: {str(e)}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Blender: {str(e)}")
            # Try to log what was received
            if "response_data" in locals() and response_data:
                logger.error(f"Raw response (first 200 bytes): {response_data[:200]}")
            raise Exception(f"Invalid response from Blender: {str(e)}") from e
        except Exception as e:
            logger.error(f"Error communicating with Blender: {str(e)}")
            # Don't try to reconnect here - let the get_blender_connection handle reconnection
            self.sock = None
            raise Exception(f"Communication error with Blender: {str(e)}") from e


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """Manage server startup and shutdown lifecycle"""
    # We don't need to create a connection here since we're using the global connection
    # for resources and tools

    try:
        # Just log that we're starting up
        logger.info("BlenderMCP server starting up")

        try:
            status = check_addon_status_on_startup()
            if status.needs_action:
                logger.warning(status.message)
            elif status.message:
                logger.info(status.message)
        except Exception as e:
            logger.debug(f"Addon status check skipped: {e}")

        # Record startup event for telemetry
        try:
            record_startup()
        except Exception as e:
            logger.debug(f"Failed to record startup telemetry: {e}")

        # Try to connect to Blender on startup to verify it's available
        try:
            # This will initialize the global connection if needed
            get_blender_connection()
            logger.info("Successfully connected to Blender on startup")
            if _addon_handshake and not _addon_handshake.up_to_date:
                logger.warning(format_handshake_log(_addon_handshake))
        except Exception as e:
            logger.warning(f"Could not connect to Blender on startup: {str(e)}")
            logger.warning(
                "Make sure the Blender addon is running before using Blender resources or tools"
            )

        # Return an empty context - we're using the global connection
        yield {}
    finally:
        try:
            from .trajectory import get_trajectory_recorder

            recorder = get_trajectory_recorder()
            recorder.close_episode("session_end")
            recorder.flush(2.0)
        except Exception as e:
            logger.debug(f"Episode close on shutdown skipped: {e}")
        # Clean up the global connection on shutdown
        global _blender_connection
        if _blender_connection:
            logger.info("Disconnecting from Blender on shutdown")
            _blender_connection.disconnect()
            _blender_connection = None
        logger.info("BlenderMCP server shut down")


# Create the MCP server with lifespan support
mcp = FastMCP("BlenderMCP", lifespan=server_lifespan)

# Resource endpoints

# Global connection for resources (since resources can't access context)
_blender_connection = None


def _maybe_handshake_addon(blender: BlenderConnection) -> None:
    """Run addon version handshake once per process after a live connection."""
    global _addon_handshake, _addon_handshake_checked
    with _addon_handshake_lock:
        if _addon_handshake_checked:
            return
        _addon_handshake_checked = True
    try:
        _addon_handshake = handshake_addon(blender)
        log_line = format_handshake_log(_addon_handshake)
        if _addon_handshake.up_to_date:
            logger.info(log_line)
        else:
            logger.warning(log_line)
    except Exception as e:
        logger.debug(f"Addon handshake skipped: {e}")


def get_blender_connection():
    """Get or create a persistent Blender connection"""
    global _blender_connection

    # Reuse the existing connection. We deliberately do NOT probe it with a
    # command here: that put two commands on the wire for every tool call, and
    # any overlap desynced the response stream until the socket timeout fired.
    # A dead socket is detected by the next real command and reconnected then.
    if _blender_connection is not None and _blender_connection.sock is not None:
        return _blender_connection

    # Create a new connection if needed
    if _blender_connection is None:
        host = os.getenv("BLENDER_HOST", DEFAULT_HOST)
        port = int(os.getenv("BLENDER_PORT", DEFAULT_PORT))
        _blender_connection = BlenderConnection(host=host, port=port)
        if not _blender_connection.connect():
            logger.error("Failed to connect to Blender")
            _blender_connection = None
            raise Exception(
                "Could not connect to Blender. Make sure the Blender addon is running."
            )
        logger.info("Created new persistent connection to Blender")
        _maybe_handshake_addon(_blender_connection)

    return _blender_connection


@mcp.tool()
async def get_addon_status(ctx: Context, user_prompt: str = "") -> str:
    """
    Check whether the connected Blender addon matches this MCP server version.

    If outdated, tells the user how to update via `uvx blender-mcp install-addon`
    (then restart or re-enable the addon in Blender).

    `telemetry_consent` reports whether data collection is on, off, or null if
    Blender could not be reached. Use it to answer telemetry status questions.
    """
    try:
        blender = get_blender_connection()
        global _addon_handshake, _addon_handshake_checked
        with _addon_handshake_lock:
            _addon_handshake_checked = False
        _maybe_handshake_addon(blender)
        result = _addon_handshake
        if result is None:
            return "Could not determine addon status." + await maybe_prompt_for_consent(
                ctx
            )
        payload = {
            "up_to_date": result.up_to_date,
            "protocol_version": result.protocol_version,
            "expected_protocol_version": EXPECTED_ADDON_PROTOCOL_VERSION,
            "addon_version": result.addon_version,
            "capabilities": result.capabilities,
            "blender_version": result.blender_version,
            "source": result.source,
            "warning": result.warning,
            "telemetry_consent": get_telemetry().check_user_consent(),
            "update_command": "uvx blender-mcp install-addon",
            "after_install": (
                "If the addon file was updated: in Blender, Preferences → Add-ons → "
                "disable/enable 'Interface: Blender MCP', or restart Blender, then Start MCP Server."
            ),
        }
        return json.dumps(payload, indent=2) + await maybe_prompt_for_consent(ctx)
    except Exception as e:
        return f"Error checking addon status: {e}"


@mcp.tool()
def disable_telemetry(ctx: Context, user_prompt: str = "") -> str:
    """
    Turn OFF collection of prompts, code, screenshots and scene data.

    Use this whenever the user asks to stop data collection, opt out of
    telemetry, or stop sharing their data. Takes effect immediately.

    This tool can only turn collection OFF. Turning it back on is done by the
    user in Blender under Preferences > Add-ons > Blender MCP.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("set_telemetry_consent", {"consent": False})
        if "error" in result:
            return f"Could not turn off data collection: {result['error']}"
        get_telemetry().invalidate_consent_cache()
        return (
            "Data collection is now OFF. Prompts, code, screenshots and scene "
            "data are no longer collected. Minimal anonymous usage counts "
            "(tool name, success, duration) still apply -- see the terms for "
            "details. To turn collection back on, tick 'Allow Telemetry' in "
            "Blender under Preferences > Add-ons > Blender MCP."
        )
    except Exception as e:
        return f"Error turning off data collection: {e}"


@mcp.tool()
@telemetry_tool("get_scene_info")
async def get_scene_info(ctx: Context, user_prompt: str) -> str:
    """Get detailed information about the current Blender scene

    Parameters:
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged. Required.
    """
    start_time = time.time()
    success = False
    error_msg = None
    result = None
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_scene_info")
        if isinstance(result, dict) and "error" in result:
            error_msg = str(result["error"])
        else:
            success = True
        # Just return the JSON representation of what Blender sent us
        return json.dumps(result, indent=2)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error getting scene info from Blender: {str(e)}")
        return f"Error getting scene info: {str(e)}"
    finally:
        try:
            from .telemetry_decorator import _record_observe_step

            _record_observe_step(
                "get_scene_info",
                modality="scene_info",
                goal_text=user_prompt,
                summary=result if isinstance(result, dict) else None,
                success=success,
                error=error_msg,
                duration_ms=(time.time() - start_time) * 1000,
            )
        except Exception:
            pass


@mcp.tool()
@telemetry_tool("get_object_info")
async def get_object_info(ctx: Context, object_name: str, user_prompt: str = "") -> str:
    """
    Get detailed information about a specific object in the Blender scene.

    Parameters:
    - object_name: The name of the object to get information about
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.
    """
    start_time = time.time()
    success = False
    error_msg = None
    result = None
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_object_info", {"name": object_name})
        if isinstance(result, dict) and "error" in result:
            error_msg = str(result["error"])
        else:
            success = True
        # Just return the JSON representation of what Blender sent us
        return json.dumps(result, indent=2)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error getting object info from Blender: {str(e)}")
        return f"Error getting object info: {str(e)}"
    finally:
        try:
            from .telemetry_decorator import _record_observe_step

            summary = (
                result if isinstance(result, dict) else {"object_name": object_name}
            )
            _record_observe_step(
                "get_object_info",
                modality="object_info",
                goal_text=user_prompt,
                summary=summary,
                success=success,
                error=error_msg,
                duration_ms=(time.time() - start_time) * 1000,
            )
        except Exception:
            pass


@mcp.tool()
def get_viewport_screenshot(
    ctx: Context, max_size: int = 1000, user_prompt: str = ""
) -> Image:
    """
    Capture a screenshot of the current Blender 3D viewport.

    Parameters:
    - max_size: Maximum size in pixels for the largest dimension (default: 800)
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the screenshot as an Image.
    """
    start_time = __import__("time").time()
    screenshot_url = None
    success = False
    error_msg = None

    try:
        blender = get_blender_connection()

        # Create temp file path
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"blender_screenshot_{os.getpid()}.png")

        result = blender.send_command(
            "get_viewport_screenshot",
            {"max_size": max_size, "filepath": temp_path, "format": "png"},
        )

        if "error" in result:
            raise Exception(result["error"])

        if not os.path.exists(temp_path):
            raise Exception("Screenshot file was not created")

        # Read the file
        with open(temp_path, "rb") as f:
            image_bytes = f.read()

        # Delete the temp file
        os.remove(temp_path)

        # Upload to storage for telemetry
        try:
            telemetry = get_telemetry()
            if telemetry._check_user_consent():
                screenshot_url = telemetry.upload_screenshot(image_bytes, "screenshot")
        except Exception:
            pass  # Silently fail - don't break screenshot for telemetry issues

        success = True
        return Image(data=image_bytes, format="png")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error capturing screenshot: {str(e)}")
        raise Exception(f"Screenshot failed: {str(e)}") from e
    finally:
        duration_ms = (__import__("time").time() - start_time) * 1000
        # Record telemetry with screenshot URL in metadata
        try:
            telemetry = get_telemetry()

            metadata = None
            if screenshot_url:
                metadata = {"screenshot_url": screenshot_url}

            telemetry.record_event(
                event_type=EventType.TOOL_EXECUTION,
                tool_name="get_viewport_screenshot",
                prompt_text=user_prompt,
                success=success,
                duration_ms=duration_ms,
                error_message=error_msg,
                metadata=metadata,
            )
        except Exception:
            pass

        try:
            from .telemetry_decorator import _record_observe_step

            _record_observe_step(
                "get_viewport_screenshot",
                modality="screenshot",
                goal_text=user_prompt,
                summary={"max_size": max_size},
                screenshot_ref=screenshot_url,
                success=success,
                error=error_msg,
                duration_ms=duration_ms,
            )
        except Exception:
            pass


@mcp.tool()
@trajectory_tool("mesh_create_primitive")
async def mesh_create_primitive(
    ctx: Context,
    primitive_type: str,
    name: str = None,
    location: list[float] = (0, 0, 0),
    rotation: list[float] = (0, 0, 0),
    size: float = 1.0,
    user_prompt: str = "",
) -> str:
    """
    Create a primitive mesh or curve object in the scene.

    Parameters:
    - primitive_type: One of CUBE, SPHERE, CYLINDER, CONE, TORUS, PLANE, CURVE (case-insensitive).
    - name: Optional name for the created object. Defaults to Blender's auto-generated name.
    - location: [x, y, z] location for the new object.
    - rotation: [x, y, z] rotation in radians for the new object.
    - size: Overall size (interpreted per primitive type, e.g. cube edge length, sphere radius).
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the created object's name, type, location, and mesh counts.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "create_primitive",
            {
                "primitive_type": primitive_type,
                "name": name,
                "location": list(location),
                "rotation": list(rotation),
                "size": size,
            },
        )
        return result
    except Exception as e:
        logger.error(f"Error creating primitive: {str(e)}")
        return f"Error creating primitive: {str(e)}"


@mcp.tool()
@trajectory_tool("mesh_extrude")
async def mesh_extrude(
    ctx: Context,
    object_name: str,
    offset: list[float] = (0, 0, 1),
    face_indices: list[int] = None,
    user_prompt: str = "",
) -> str:
    """
    Extrude the selected faces of a mesh object along an offset vector.

    Parameters:
    - object_name: Name of the mesh object to edit.
    - offset: [x, y, z] translation applied to the extruded geometry.
    - face_indices: Optional list of face indices to extrude. If omitted, all faces are extruded.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the object's name and updated vertex/edge/polygon counts.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "mesh_extrude",
            {
                "object_name": object_name,
                "offset": list(offset),
                "face_indices": face_indices,
            },
        )
        return result
    except Exception as e:
        logger.error(f"Error extruding mesh: {str(e)}")
        return f"Error extruding mesh: {str(e)}"


@mcp.tool()
@trajectory_tool("mesh_inset")
async def mesh_inset(
    ctx: Context,
    object_name: str,
    thickness: float = 0.05,
    depth: float = 0.0,
    face_indices: list[int] = None,
    user_prompt: str = "",
) -> str:
    """
    Inset the selected faces of a mesh object, creating a smaller face surrounded by new faces.

    Parameters:
    - object_name: Name of the mesh object to edit.
    - thickness: Inset thickness.
    - depth: Inset depth (pushes the inset faces along their normal).
    - face_indices: Optional list of face indices to inset. If omitted, all faces are inset.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the object's name and updated vertex/edge/polygon counts.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "mesh_inset",
            {
                "object_name": object_name,
                "thickness": thickness,
                "depth": depth,
                "face_indices": face_indices,
            },
        )
        return result
    except Exception as e:
        logger.error(f"Error insetting mesh faces: {str(e)}")
        return f"Error insetting mesh faces: {str(e)}"


@mcp.tool()
@trajectory_tool("mesh_bevel")
async def mesh_bevel(
    ctx: Context,
    object_name: str,
    offset: float = 0.05,
    segments: int = 1,
    affect: str = "EDGES",
    edge_indices: list[int] = None,
    vertex_indices: list[int] = None,
    user_prompt: str = "",
) -> str:
    """
    Bevel the selected edges or vertices of a mesh object.

    Parameters:
    - object_name: Name of the mesh object to edit.
    - offset: Bevel width.
    - segments: Number of bevel segments.
    - affect: "EDGES" or "VERTICES".
    - edge_indices: Optional list of edge indices to bevel.
    - vertex_indices: Optional list of vertex indices to bevel.
    - If neither edge_indices nor vertex_indices is given, the whole mesh is selected.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the object's name and updated vertex/edge/polygon counts.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "mesh_bevel",
            {
                "object_name": object_name,
                "offset": offset,
                "segments": segments,
                "affect": affect,
                "edge_indices": edge_indices,
                "vertex_indices": vertex_indices,
            },
        )
        return result
    except Exception as e:
        logger.error(f"Error beveling mesh: {str(e)}")
        return f"Error beveling mesh: {str(e)}"


@mcp.tool()
@trajectory_tool("mesh_bridge")
async def mesh_bridge(
    ctx: Context, object_name: str, edge_indices: list[int], user_prompt: str = ""
) -> str:
    """
    Bridge two open edge loops of a mesh object with new faces.

    Parameters:
    - object_name: Name of the mesh object to edit.
    - edge_indices: Required list of edge indices forming the two loops to bridge.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the object's name and updated vertex/edge/polygon counts.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "mesh_bridge",
            {
                "object_name": object_name,
                "edge_indices": edge_indices,
            },
        )
        return result
    except Exception as e:
        logger.error(f"Error bridging mesh edge loops: {str(e)}")
        return f"Error bridging mesh edge loops: {str(e)}"


@mcp.tool()
@trajectory_tool("mesh_boolean")
async def mesh_boolean(
    ctx: Context,
    object_name: str,
    cutter_object_name: str,
    operation: str = "DIFFERENCE",
    keep_target: bool = False,
    user_prompt: str = "",
) -> str:
    """
    Apply a boolean operation between two mesh objects.

    Parameters:
    - object_name: Name of the mesh object the boolean is applied to (the result).
    - cutter_object_name: Name of the other mesh object used as the cutter/operand.
    - operation: One of UNION, DIFFERENCE, INTERSECT.
    - keep_target: If False (default), the cutter object is deleted after the operation is applied. Set True to keep it.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the object's name and updated vertex/edge/polygon counts.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "mesh_boolean",
            {
                "object_name": object_name,
                "cutter_object_name": cutter_object_name,
                "operation": operation,
                "keep_target": keep_target,
            },
        )
        return result
    except Exception as e:
        logger.error(f"Error applying mesh boolean: {str(e)}")
        return f"Error applying mesh boolean: {str(e)}"


@mcp.tool()
@trajectory_tool("mesh_subdivide")
async def mesh_subdivide(
    ctx: Context,
    object_name: str,
    cuts: int = 1,
    face_indices: list[int] = None,
    user_prompt: str = "",
) -> str:
    """
    Subdivide the selected faces of a mesh object, adding more geometry.

    Parameters:
    - object_name: Name of the mesh object to edit.
    - cuts: Number of cuts per edge.
    - face_indices: Optional list of face indices to subdivide. If omitted, all faces are subdivided.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the object's name and updated vertex/edge/polygon counts.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "mesh_subdivide",
            {
                "object_name": object_name,
                "cuts": cuts,
                "face_indices": face_indices,
            },
        )
        return result
    except Exception as e:
        logger.error(f"Error subdividing mesh: {str(e)}")
        return f"Error subdividing mesh: {str(e)}"


@mcp.tool()
@trajectory_tool("mesh_remesh")
async def mesh_remesh(
    ctx: Context, object_name: str, voxel_size: float = 0.1, user_prompt: str = ""
) -> str:
    """
    Voxel-remesh a mesh object, rebuilding its topology at a uniform resolution.

    Parameters:
    - object_name: Name of the mesh object to remesh.
    - voxel_size: Size of the voxels used to rebuild the mesh; smaller values produce more detail.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the object's name and updated vertex/edge/polygon counts.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "mesh_remesh",
            {
                "object_name": object_name,
                "voxel_size": voxel_size,
            },
        )
        return result
    except Exception as e:
        logger.error(f"Error remeshing mesh: {str(e)}")
        return f"Error remeshing mesh: {str(e)}"


@mcp.tool()
@trajectory_tool("mesh_solidify")
async def mesh_solidify(
    ctx: Context,
    object_name: str,
    thickness: float = 0.01,
    apply: bool = True,
    user_prompt: str = "",
) -> str:
    """
    Give a mesh's surface thickness via a Solidify modifier.

    Parameters:
    - object_name: Name of the mesh object to solidify.
    - thickness: Thickness to add.
    - apply: If True (default), bake the modifier into the mesh. If False, leave it as a live modifier.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the object's name, whether the modifier was applied, and updated vertex/edge/polygon counts.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "mesh_solidify",
            {
                "object_name": object_name,
                "thickness": thickness,
                "apply": apply,
            },
        )
        return result
    except Exception as e:
        logger.error(f"Error solidifying mesh: {str(e)}")
        return f"Error solidifying mesh: {str(e)}"


@mcp.tool()
@trajectory_tool("model_match_reference")
async def model_match_reference(
    ctx: Context,
    object_name: str,
    reference_object_name: str,
    match_location: bool = True,
    match_rotation: bool = True,
    match_scale: bool = True,
    user_prompt: str = "",
) -> str:
    """
    Align an object's transform to another object's transform in the scene.

    Parameters:
    - object_name: Name of the object to move/rotate/scale.
    - reference_object_name: Name of the object whose transform to copy.
    - match_location: Copy the reference object's location.
    - match_rotation: Copy the reference object's rotation.
    - match_scale: Copy the reference object's scale.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the object's name and resulting location/rotation/scale.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "model_match_reference",
            {
                "object_name": object_name,
                "reference_object_name": reference_object_name,
                "match_location": match_location,
                "match_rotation": match_rotation,
                "match_scale": match_scale,
            },
        )
        return result
    except Exception as e:
        logger.error(f"Error matching reference transform: {str(e)}")
        return f"Error matching reference transform: {str(e)}"


@mcp.tool()
@trajectory_tool("model_blockout")
async def model_blockout(
    ctx: Context,
    name: str,
    primitive_type: str = "CUBE",
    size: list[float] = (1, 1, 1),
    location: list[float] = (0, 0, 0),
    user_prompt: str = "",
) -> str:
    """
    Create a simple placeholder primitive scaled to size, tagged as a blockout proxy for later refinement.

    Parameters:
    - name: Name for the created blockout object.
    - primitive_type: One of CUBE, SPHERE, CYLINDER, CONE, TORUS, PLANE, CURVE (case-insensitive).
    - size: [x, y, z] scale applied to the primitive.
    - location: [x, y, z] location for the new object.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the created object's name, type, location, and scale.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "model_blockout",
            {
                "name": name,
                "primitive_type": primitive_type,
                "size": list(size),
                "location": list(location),
            },
        )
        return result
    except Exception as e:
        logger.error(f"Error creating blockout: {str(e)}")
        return f"Error creating blockout: {str(e)}"


@mcp.tool()
@trajectory_tool("model_refine")
async def model_refine(
    ctx: Context,
    object_name: str,
    levels: int = 1,
    apply: bool = False,
    user_prompt: str = "",
) -> str:
    """
    Smooth a mesh and increase its effective resolution via a Subdivision Surface modifier.

    Parameters:
    - object_name: Name of the mesh object to refine.
    - levels: Subdivision levels (viewport and render).
    - apply: If True, bake the modifier into the mesh. If False (default), leave it as a live modifier.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the object's name, whether the modifier was applied, and updated vertex/edge/polygon counts.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "model_refine",
            {
                "object_name": object_name,
                "levels": levels,
                "apply": apply,
            },
        )
        return result
    except Exception as e:
        logger.error(f"Error refining model: {str(e)}")
        return f"Error refining model: {str(e)}"


@mcp.tool()
@trajectory_tool("model_detail")
async def model_detail(
    ctx: Context,
    object_name: str,
    strength: float = 0.1,
    scale: float = 5.0,
    texture_type: str = "NOISE",
    apply: bool = False,
    user_prompt: str = "",
) -> str:
    """
    Add fine procedural surface detail to a mesh via a Displace modifier driven by a procedural texture.

    Parameters:
    - object_name: Name of the mesh object to detail.
    - strength: Displacement strength.
    - scale: Noise scale of the driving texture.
    - texture_type: Blender texture type to drive the displacement, e.g. NOISE or VORONOI.
    - apply: If True, bake the modifier into the mesh. If False (default), leave it as a live modifier.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the object's name, whether the modifier was applied, and updated vertex/edge/polygon counts.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "model_detail",
            {
                "object_name": object_name,
                "strength": strength,
                "scale": scale,
                "texture_type": texture_type,
                "apply": apply,
            },
        )
        return result
    except Exception as e:
        logger.error(f"Error adding model detail: {str(e)}")
        return f"Error adding model detail: {str(e)}"


@mcp.tool()
@trajectory_tool("model_symmetrize")
async def model_symmetrize(
    ctx: Context,
    object_name: str,
    direction: str = "NEGATIVE_X_TO_POSITIVE_X",
    user_prompt: str = "",
) -> str:
    """
    Symmetrize a mesh across an axis, mirroring one half of the geometry onto the other.

    Parameters:
    - object_name: Name of the mesh object to symmetrize.
    - direction: One of NEGATIVE_X_TO_POSITIVE_X, POSITIVE_X_TO_NEGATIVE_X, NEGATIVE_Y_TO_POSITIVE_Y, POSITIVE_Y_TO_NEGATIVE_Y, NEGATIVE_Z_TO_POSITIVE_Z, POSITIVE_Z_TO_NEGATIVE_Z.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the object's name and updated vertex/edge/polygon counts.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "model_symmetrize",
            {
                "object_name": object_name,
                "direction": direction,
            },
        )
        return result
    except Exception as e:
        logger.error(f"Error symmetrizing model: {str(e)}")
        return f"Error symmetrizing model: {str(e)}"


@mcp.tool()
@trajectory_tool("model_mirror")
async def model_mirror(
    ctx: Context,
    object_name: str,
    axis: str = "X",
    merge: bool = True,
    apply: bool = False,
    user_prompt: str = "",
) -> str:
    """
    Add a Mirror modifier to an object across the given axis.

    Parameters:
    - object_name: Name of the mesh object to mirror.
    - axis: One of X, Y, Z.
    - merge: Clip/merge vertices at the mirror plane.
    - apply: If True, bake the modifier into the mesh. If False (default), leave it as a live modifier.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the object's name, whether the modifier was applied, and updated vertex/edge/polygon counts.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "model_mirror",
            {
                "object_name": object_name,
                "axis": axis,
                "merge": merge,
                "apply": apply,
            },
        )
        return result
    except Exception as e:
        logger.error(f"Error mirroring model: {str(e)}")
        return f"Error mirroring model: {str(e)}"


@mcp.tool()
@trajectory_tool("model_array")
async def model_array(
    ctx: Context,
    object_name: str,
    count: int = 2,
    relative_offset: list[float] = (1, 0, 0),
    apply: bool = False,
    user_prompt: str = "",
) -> str:
    """
    Add a linear Array modifier to an object, duplicating it along an offset direction.

    Parameters:
    - object_name: Name of the mesh object to array.
    - count: Number of copies (including the original).
    - relative_offset: [x, y, z] offset between copies, relative to the object's bounding box.
    - apply: If True, bake the modifier into the mesh. If False (default), leave it as a live modifier.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the object's name, whether the modifier was applied, and updated vertex/edge/polygon counts.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "model_array",
            {
                "object_name": object_name,
                "count": count,
                "relative_offset": list(relative_offset),
                "apply": apply,
            },
        )
        return result
    except Exception as e:
        logger.error(f"Error arraying model: {str(e)}")
        return f"Error arraying model: {str(e)}"


@mcp.tool()
@trajectory_tool("model_radial_array")
async def model_radial_array(
    ctx: Context,
    object_name: str,
    count: int = 6,
    axis: str = "Z",
    apply: bool = False,
    user_prompt: str = "",
) -> str:
    """
    Duplicate an object radially around its origin, evenly spaced about an axis.

    Parameters:
    - object_name: Name of the mesh object to array.
    - count: Number of copies around the circle (including the original). Must be at least 2.
    - axis: One of X, Y, Z — the axis to rotate around.
    - apply: If True, bake the modifier into the mesh and remove the helper empty. If False (default), leave both live.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the object's name, whether the modifier was applied, and updated vertex/edge/polygon counts.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "model_radial_array",
            {
                "object_name": object_name,
                "count": count,
                "axis": axis,
                "apply": apply,
            },
        )
        return result
    except Exception as e:
        logger.error(f"Error creating radial array: {str(e)}")
        return f"Error creating radial array: {str(e)}"


@mcp.tool()
@trajectory_tool("nd_boolean")
async def nd_boolean(
    ctx: Context,
    object_name: str,
    cutter_object_name: str,
    mode: str = "DIFFERENCE",
    user_prompt: str = "",
) -> str:
    """
    ND non-destructive boolean: live Boolean modifier on object_name, with cutter_object_name
    converted into a wireframe ND utility object parented to it (not deleted, unlike mesh_boolean).

    Parameters:
    - object_name: Name of the mesh object the boolean is applied to (the result/target).
    - cutter_object_name: Name of the other mesh object used as the cutter/operand.
    - mode: One of UNION, DIFFERENCE, INTERSECT.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the target and cutter object names and updated vertex/edge/polygon counts.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "nd_boolean",
            {
                "object_name": object_name,
                "cutter_object_name": cutter_object_name,
                "mode": mode,
            },
        )
        return result
    except Exception as e:
        logger.error(f"Error applying ND boolean: {str(e)}")
        return f"Error applying ND boolean: {str(e)}"


@mcp.tool()
@trajectory_tool("nd_mark_as_util")
async def nd_mark_as_util(
    ctx: Context,
    object_names: list[str],
    unmark: bool = False,
    user_prompt: str = "",
) -> str:
    """
    Mark/unmark objects as ND utility objects (wireframe display, hidden from render and most
    viewport visibility categories).

    Parameters:
    - object_names: Names of the objects to mark/unmark.
    - unmark: If True, restore normal (SOLID/visible) display instead of marking as a utility.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the affected object names.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "nd_mark_as_util",
            {"object_names": object_names, "unmark": unmark},
        )
        return result
    except Exception as e:
        logger.error(f"Error marking ND utility objects: {str(e)}")
        return f"Error marking ND utility objects: {str(e)}"


@mcp.tool()
@trajectory_tool("nd_clean_utils")
async def nd_clean_utils(ctx: Context, user_prompt: str = "") -> str:
    """
    Remove orphaned boolean/array/mirror/lattice modifiers and their ND utility objects, scene-wide.

    Parameters:
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("nd_clean_utils", {})
        return result
    except Exception as e:
        logger.error(f"Error cleaning ND utility objects: {str(e)}")
        return f"Error cleaning ND utility objects: {str(e)}"


@mcp.tool()
@trajectory_tool("nd_create_id_material")
async def nd_create_id_material(
    ctx: Context,
    object_names: list[str],
    material_name: str,
    user_prompt: str = "",
) -> str:
    """
    Create/assign a single ND ID material to the given mesh/curve objects.

    Parameters:
    - object_names: Names of the objects to assign the material to.
    - material_name: Name of the ID material to create/reuse.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "nd_create_id_material",
            {"object_names": object_names, "material_name": material_name},
        )
        return result
    except Exception as e:
        logger.error(f"Error creating ND ID material: {str(e)}")
        return f"Error creating ND ID material: {str(e)}"


@mcp.tool()
@trajectory_tool("nd_bulk_create_id_materials")
async def nd_bulk_create_id_materials(
    ctx: Context, object_names: list[str], user_prompt: str = ""
) -> str:
    """
    Assign a random distinct ND ID material to each given mesh/curve object.

    Parameters:
    - object_names: Names of the objects to assign distinct ID materials to.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "nd_bulk_create_id_materials", {"object_names": object_names}
        )
        return result
    except Exception as e:
        logger.error(f"Error bulk-creating ND ID materials: {str(e)}")
        return f"Error bulk-creating ND ID materials: {str(e)}"


@mcp.tool()
@trajectory_tool("nd_clear_materials")
async def nd_clear_materials(
    ctx: Context, object_names: list[str], user_prompt: str = ""
) -> str:
    """
    Remove all material slots from the given mesh/curve objects.

    Parameters:
    - object_names: Names of the objects to clear materials from.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "nd_clear_materials", {"object_names": object_names}
        )
        return result
    except Exception as e:
        logger.error(f"Error clearing ND materials: {str(e)}")
        return f"Error clearing ND materials: {str(e)}"


@mcp.tool()
@trajectory_tool("nd_set_lod_suffix")
async def nd_set_lod_suffix(
    ctx: Context,
    object_names: list[str],
    mode: str = "HIGH",
    user_prompt: str = "",
) -> str:
    """
    Suffix object (and data-block) names with _high or _low, replacing any existing LOD suffix.

    Parameters:
    - object_names: Names of the objects to rename.
    - mode: One of HIGH, LOW.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "nd_set_lod_suffix", {"object_names": object_names, "mode": mode}
        )
        return result
    except Exception as e:
        logger.error(f"Error setting ND LOD suffix: {str(e)}")
        return f"Error setting ND LOD suffix: {str(e)}"


@mcp.tool()
@trajectory_tool("nd_name_sync")
async def nd_name_sync(
    ctx: Context, object_names: list[str], user_prompt: str = ""
) -> str:
    """
    Sync each object's data-block name to match its object name.

    Parameters:
    - object_names: Names of the objects to sync.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("nd_name_sync", {"object_names": object_names})
        return result
    except Exception as e:
        logger.error(f"Error syncing ND names: {str(e)}")
        return f"Error syncing ND names: {str(e)}"


@mcp.tool()
@trajectory_tool("nd_single_vertex")
async def nd_single_vertex(
    ctx: Context,
    location: list[float] = (0, 0, 0),
    user_prompt: str = "",
) -> str:
    """
    Create an ND single-vertex sketch object at location, left in Object mode.

    Parameters:
    - location: [x, y, z] world location for the new vertex object.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the new object's name and location.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("nd_single_vertex", {"location": list(location)})
        return result
    except Exception as e:
        logger.error(f"Error creating ND single vertex: {str(e)}")
        return f"Error creating ND single vertex: {str(e)}"


@mcp.tool()
@trajectory_tool("nd_clear_edge_marks")
async def nd_clear_edge_marks(
    ctx: Context, object_name: str, user_prompt: str = ""
) -> str:
    """
    Remove sharp/seam/freestyle edge marks from a mesh object.

    Parameters:
    - object_name: Name of the mesh object to clear edge marks from.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "nd_clear_edge_marks", {"object_name": object_name}
        )
        return result
    except Exception as e:
        logger.error(f"Error clearing ND edge marks: {str(e)}")
        return f"Error clearing ND edge marks: {str(e)}"


@mcp.tool()
@trajectory_tool("nd_clear_vertex_groups")
async def nd_clear_vertex_groups(
    ctx: Context, object_name: str, user_prompt: str = ""
) -> str:
    """
    Remove all vertex groups from a mesh object.

    Parameters:
    - object_name: Name of the mesh object to clear vertex groups from.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "nd_clear_vertex_groups", {"object_name": object_name}
        )
        return result
    except Exception as e:
        logger.error(f"Error clearing ND vertex groups: {str(e)}")
        return f"Error clearing ND vertex groups: {str(e)}"


@mcp.tool()
@trajectory_tool("nd_apply_modifiers")
async def nd_apply_modifiers(
    ctx: Context, object_names: list[str], user_prompt: str = ""
) -> str:
    """
    Apply modifiers on the given objects via ND. Always runs ND's default REGULAR apply mode
    (selective, with ND's built-in exclusions for bevel/weighted-normals/etc.) - the
    SOFT/HARD/duplicate variants are driven by modifier keys in ND's UI and are not reachable
    from a script.

    Parameters:
    - object_names: Names of the objects to apply modifiers on.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "nd_apply_modifiers", {"object_names": object_names}
        )
        return result
    except Exception as e:
        logger.error(f"Error applying ND modifiers: {str(e)}")
        return f"Error applying ND modifiers: {str(e)}"


@mcp.tool()
@trajectory_tool("nd_viewport_toggle")
async def nd_viewport_toggle(ctx: Context, toggle: str, user_prompt: str = "") -> str:
    """
    Toggle an ND viewport display setting.

    Parameters:
    - toggle: One of CAVITY, WIREFRAMES, FACE_ORIENTATION, CLEAR_VIEW, CUSTOM_VIEW, UTILS.
      (ND's SILHOUETTE toggle is a genuine modal operator and is intentionally not exposed here.)
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("nd_viewport_toggle", {"toggle": toggle})
        return result
    except Exception as e:
        logger.error(f"Error toggling ND viewport setting: {str(e)}")
        return f"Error toggling ND viewport setting: {str(e)}"


@mcp.tool()
@trajectory_tool("nd_capture_utils")
async def nd_capture_utils(ctx: Context, user_prompt: str = "") -> str:
    """
    Display and select all ND utility objects in the scene.

    Parameters:
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("nd_capture_utils", {})
        return result
    except Exception as e:
        logger.error(f"Error capturing ND utility objects: {str(e)}")
        return f"Error capturing ND utility objects: {str(e)}"


@mcp.tool()
@telemetry_tool("get_nd_status")
async def get_nd_status(ctx: Context, user_prompt: str = "") -> str:
    """
    Check if ND (HugeMenace) non-destructive workflow integration is enabled in Blender.
    Returns a message indicating whether ND features are available.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_nd_status")
        return result.get("message", "")
    except Exception as e:
        logger.error(f"Error checking ND status: {str(e)}")
        return f"Error checking ND status: {str(e)}"


@mcp.tool()
@trajectory_tool("execute_blender_code", capture_code=True)
async def execute_blender_code(ctx: Context, code: str, user_prompt: str = "") -> str:
    """
    Execute arbitrary Python code in Blender. Make sure to do it step-by-step by breaking it into smaller chunks.

    Parameters:
    - code: The Python code to execute
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.
    """
    try:
        # Get the global connection
        blender = get_blender_connection()
        result = blender.send_command("execute_code", {"code": code})
        return f"Code executed successfully: {result.get('result', '')}"
    except Exception as e:
        logger.error(f"Error executing code: {str(e)}")
        return f"Error executing code: {str(e)}"


@mcp.tool()
@telemetry_tool("get_polyhaven_categories")
async def get_polyhaven_categories(
    ctx: Context, asset_type: str = "hdris", user_prompt: str = ""
) -> str:
    """
    Get a list of categories for a specific asset type on Polyhaven.

    Parameters:
    - asset_type: The type of asset to get categories for (hdris, textures, models, all)
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.
    """
    try:
        blender = get_blender_connection()
        status = blender.send_command("get_polyhaven_status")
        if not status.get("enabled", False):
            return "PolyHaven integration is disabled. Select it in the sidebar in BlenderMCP, then run it again."
        result = blender.send_command(
            "get_polyhaven_categories", {"asset_type": asset_type}
        )

        if "error" in result:
            return f"Error: {result['error']}"

        # Format the categories in a more readable way
        categories = result["categories"]
        formatted_output = f"Categories for {asset_type}:\n\n"

        # Sort categories by count (descending)
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)

        for category, count in sorted_categories:
            formatted_output += f"- {category}: {count} assets\n"

        return formatted_output
    except Exception as e:
        logger.error(f"Error getting Polyhaven categories: {str(e)}")
        return f"Error getting Polyhaven categories: {str(e)}"


@mcp.tool()
@telemetry_tool("search_polyhaven_assets")
async def search_polyhaven_assets(
    ctx: Context, asset_type: str = "all", categories: str = None, user_prompt: str = ""
) -> str:
    """
    Search for assets on Polyhaven with optional filtering.

    Parameters:
    - asset_type: Type of assets to search for (hdris, textures, models, all)
    - categories: Optional comma-separated list of categories to filter by
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns a list of matching assets with basic information.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "search_polyhaven_assets",
            {"asset_type": asset_type, "categories": categories},
        )

        if "error" in result:
            return f"Error: {result['error']}"

        # Format the assets in a more readable way
        assets = result["assets"]
        total_count = result["total_count"]
        returned_count = result["returned_count"]

        formatted_output = f"Found {total_count} assets"
        if categories:
            formatted_output += f" in categories: {categories}"
        formatted_output += f"\nShowing {returned_count} assets:\n\n"

        # Sort assets by download count (popularity)
        sorted_assets = sorted(
            assets.items(), key=lambda x: x[1].get("download_count", 0), reverse=True
        )

        for asset_id, asset_data in sorted_assets:
            formatted_output += (
                f"- {asset_data.get('name', asset_id)} (ID: {asset_id})\n"
            )
            formatted_output += (
                f"  Type: {['HDRI', 'Texture', 'Model'][asset_data.get('type', 0)]}\n"
            )
            formatted_output += (
                f"  Categories: {', '.join(asset_data.get('categories', []))}\n"
            )
            formatted_output += (
                f"  Downloads: {asset_data.get('download_count', 'Unknown')}\n\n"
            )

        return formatted_output
    except Exception as e:
        logger.error(f"Error searching Polyhaven assets: {str(e)}")
        return f"Error searching Polyhaven assets: {str(e)}"


@mcp.tool()
@trajectory_tool("download_polyhaven_asset")
async def download_polyhaven_asset(
    ctx: Context,
    asset_id: str,
    asset_type: str,
    resolution: str = "1k",
    file_format: str = None,
    user_prompt: str = "",
) -> str:
    """
    Download and import a Polyhaven asset into Blender.

    Parameters:
    - asset_id: The ID of the asset to download
    - asset_type: The type of asset (hdris, textures, models)
    - resolution: The resolution to download (e.g., 1k, 2k, 4k)
    - file_format: Optional file format (e.g., hdr, exr for HDRIs; jpg, png for textures; gltf, fbx for models)
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns a message indicating success or failure.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "download_polyhaven_asset",
            {
                "asset_id": asset_id,
                "asset_type": asset_type,
                "resolution": resolution,
                "file_format": file_format,
            },
        )

        if "error" in result:
            return f"Error: {result['error']}"

        if result.get("success"):
            message = result.get(
                "message", "Asset downloaded and imported successfully"
            )

            # Add additional information based on asset type
            if asset_type == "hdris":
                return f"{message}. The HDRI has been set as the world environment."
            elif asset_type == "textures":
                material_name = result.get("material", "")
                maps = ", ".join(result.get("maps", []))
                return (
                    f"{message}. Created material '{material_name}' with maps: {maps}."
                )
            elif asset_type == "models":
                return f"{message}. The model has been imported into the current scene."
            else:
                return message
        else:
            return f"Failed to download asset: {result.get('message', 'Unknown error')}"
    except Exception as e:
        logger.error(f"Error downloading Polyhaven asset: {str(e)}")
        return f"Error downloading Polyhaven asset: {str(e)}"


@mcp.tool()
@trajectory_tool("set_texture")
async def set_texture(
    ctx: Context, object_name: str, texture_id: str, user_prompt: str = ""
) -> str:
    """
    Apply a previously downloaded Polyhaven texture to an object.

    Parameters:
    - object_name: Name of the object to apply the texture to
    - texture_id: ID of the Polyhaven texture to apply (must be downloaded first)
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns a message indicating success or failure.
    """
    try:
        # Get the global connection
        blender = get_blender_connection()
        result = blender.send_command(
            "set_texture", {"object_name": object_name, "texture_id": texture_id}
        )

        if "error" in result:
            return f"Error: {result['error']}"

        if result.get("success"):
            material_name = result.get("material", "")
            maps = ", ".join(result.get("maps", []))

            # Add detailed material info
            material_info = result.get("material_info", {})
            node_count = material_info.get("node_count", 0)
            has_nodes = material_info.get("has_nodes", False)
            texture_nodes = material_info.get("texture_nodes", [])

            output = f"Successfully applied texture '{texture_id}' to {object_name}.\n"
            output += f"Using material '{material_name}' with maps: {maps}.\n\n"
            output += f"Material has nodes: {has_nodes}\n"
            output += f"Total node count: {node_count}\n\n"

            if texture_nodes:
                output += "Texture nodes:\n"
                for node in texture_nodes:
                    output += f"- {node['name']} using image: {node['image']}\n"
                    if node["connections"]:
                        output += "  Connections:\n"
                        for conn in node["connections"]:
                            output += f"    {conn}\n"
            else:
                output += "No texture nodes found in the material.\n"

            return output
        else:
            return f"Failed to apply texture: {result.get('message', 'Unknown error')}"
    except Exception as e:
        logger.error(f"Error applying texture: {str(e)}")
        return f"Error applying texture: {str(e)}"


@mcp.tool()
@telemetry_tool("get_polyhaven_status")
async def get_polyhaven_status(ctx: Context, user_prompt: str = "") -> str:
    """
    Check if PolyHaven integration is enabled in Blender.
    Returns a message indicating whether PolyHaven features are available.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_polyhaven_status")
        enabled = result.get("enabled", False)
        message = result.get("message", "")
        if enabled:
            message += "PolyHaven is good at Textures, and has a wider variety of textures than Sketchfab."
        return message
    except Exception as e:
        logger.error(f"Error checking PolyHaven status: {str(e)}")
        return f"Error checking PolyHaven status: {str(e)}"


@mcp.tool()
@telemetry_tool("get_hyper3d_status")
async def get_hyper3d_status(ctx: Context, user_prompt: str = "") -> str:
    """
    Check if Hyper3D Rodin integration is enabled in Blender.
    Returns a message indicating whether Hyper3D Rodin features are available.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_hyper3d_status")
        enabled = result.get("enabled", False)
        message = result.get("message", "")
        if enabled:
            message += ""
        return message
    except Exception as e:
        logger.error(f"Error checking Hyper3D status: {str(e)}")
        return f"Error checking Hyper3D status: {str(e)}"


@mcp.tool()
@telemetry_tool("get_sketchfab_status")
async def get_sketchfab_status(ctx: Context, user_prompt: str = "") -> str:
    """
    Check if Sketchfab integration is enabled in Blender.
    Returns a message indicating whether Sketchfab features are available.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_sketchfab_status")
        enabled = result.get("enabled", False)
        message = result.get("message", "")
        if enabled:
            message += "Sketchfab is good at Realistic models, and has a wider variety of models than PolyHaven."
        return message
    except Exception as e:
        logger.error(f"Error checking Sketchfab status: {str(e)}")
        return f"Error checking Sketchfab status: {str(e)}"


@mcp.tool()
@telemetry_tool("search_sketchfab_models")
async def search_sketchfab_models(
    ctx: Context,
    query: str,
    categories: str = None,
    count: int = 20,
    downloadable: bool = True,
    user_prompt: str = "",
) -> str:
    """
    Search for models on Sketchfab with optional filtering.

    Parameters:
    - query: Text to search for
    - categories: Optional comma-separated list of categories
    - count: Maximum number of results to return (default 20)
    - downloadable: Whether to include only downloadable models (default True)
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns a formatted list of matching models.
    """
    try:
        blender = get_blender_connection()
        logger.info(
            f"Searching Sketchfab models with query: {query}, categories: {categories}, count: {count}, downloadable: {downloadable}"
        )
        result = blender.send_command(
            "search_sketchfab_models",
            {
                "query": query,
                "categories": categories,
                "count": count,
                "downloadable": downloadable,
            },
        )

        if "error" in result:
            logger.error(f"Error from Sketchfab search: {result['error']}")
            return f"Error: {result['error']}"

        # Safely get results with fallbacks for None
        if result is None:
            logger.error("Received None result from Sketchfab search")
            return "Error: Received no response from Sketchfab search"

        # Format the results
        models = result.get("results", []) or []
        if not models:
            return f"No models found matching '{query}'"

        formatted_output = f"Found {len(models)} models matching '{query}':\n\n"

        for model in models:
            if model is None:
                continue

            model_name = model.get("name", "Unnamed model")
            model_uid = model.get("uid", "Unknown ID")
            formatted_output += f"- {model_name} (UID: {model_uid})\n"

            # Get user info with safety checks
            user = model.get("user") or {}
            username = (
                user.get("username", "Unknown author")
                if isinstance(user, dict)
                else "Unknown author"
            )
            formatted_output += f"  Author: {username}\n"

            # Get license info with safety checks
            license_data = model.get("license") or {}
            license_label = (
                license_data.get("label", "Unknown")
                if isinstance(license_data, dict)
                else "Unknown"
            )
            formatted_output += f"  License: {license_label}\n"

            # Add face count and downloadable status
            face_count = model.get("faceCount", "Unknown")
            is_downloadable = "Yes" if model.get("isDownloadable") else "No"
            formatted_output += f"  Face count: {face_count}\n"
            formatted_output += f"  Downloadable: {is_downloadable}\n\n"

        return formatted_output
    except Exception as e:
        logger.error(f"Error searching Sketchfab models: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return f"Error searching Sketchfab models: {str(e)}"


@mcp.tool()
@telemetry_tool("get_sketchfab_model_preview")
async def get_sketchfab_model_preview(
    ctx: Context, uid: str, user_prompt: str = ""
) -> Image:
    """
    Get a preview thumbnail of a Sketchfab model by its UID.
    Use this to visually confirm a model before downloading.

    Parameters:
    - uid: The unique identifier of the Sketchfab model (obtained from search_sketchfab_models)
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the model's thumbnail as an Image for visual confirmation.
    """
    try:
        blender = get_blender_connection()
        logger.info(f"Getting Sketchfab model preview for UID: {uid}")

        result = blender.send_command("get_sketchfab_model_preview", {"uid": uid})

        if result is None:
            raise Exception("Received no response from Blender")

        if "error" in result:
            raise Exception(result["error"])

        # Decode base64 image data
        image_data = base64.b64decode(result["image_data"])
        img_format = result.get("format", "jpeg")

        # Log model info
        model_name = result.get("model_name", "Unknown")
        author = result.get("author", "Unknown")
        logger.info(f"Preview retrieved for '{model_name}' by {author}")

        return Image(data=image_data, format=img_format)

    except Exception as e:
        logger.error(f"Error getting Sketchfab preview: {str(e)}")
        raise Exception(f"Failed to get preview: {str(e)}") from e


@mcp.tool()
@trajectory_tool("download_sketchfab_model")
async def download_sketchfab_model(
    ctx: Context, uid: str, target_size: float, user_prompt: str = ""
) -> str:
    """
    Download and import a Sketchfab model by its UID.
    The model will be scaled so its largest dimension equals target_size.

    Parameters:
    - uid: The unique identifier of the Sketchfab model
    - target_size: REQUIRED. The target size in Blender units/meters for the largest dimension.
                  You must specify the desired size for the model.
                  Examples:
                  - Chair: target_size=1.0 (1 meter tall)
                  - Table: target_size=0.75 (75cm tall)
                  - Car: target_size=4.5 (4.5 meters long)
                  - Person: target_size=1.7 (1.7 meters tall)
                  - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.
                  - Small object (cup, phone): target_size=0.1 to 0.3

    Returns a message with import details including object names, dimensions, and bounding box.
    The model must be downloadable and you must have proper access rights.
    """
    try:
        blender = get_blender_connection()
        logger.info(f"Downloading Sketchfab model: {uid}, target_size={target_size}")

        result = blender.send_command(
            "download_sketchfab_model",
            {
                "uid": uid,
                "normalize_size": True,  # Always normalize
                "target_size": target_size,
            },
        )

        if result is None:
            logger.error("Received None result from Sketchfab download")
            return "Error: Received no response from Sketchfab download request"

        if "error" in result:
            logger.error(f"Error from Sketchfab download: {result['error']}")
            return f"Error: {result['error']}"

        if result.get("success"):
            imported_objects = result.get("imported_objects", [])
            object_names = ", ".join(imported_objects) if imported_objects else "none"

            output = "Successfully imported model.\n"
            output += f"Created objects: {object_names}\n"

            # Add dimension info if available
            if result.get("dimensions"):
                dims = result["dimensions"]
                output += f"Dimensions (X, Y, Z): {dims[0]:.3f} x {dims[1]:.3f} x {dims[2]:.3f} meters\n"

            # Add bounding box info if available
            if result.get("world_bounding_box"):
                bbox = result["world_bounding_box"]
                output += f"Bounding box: min={bbox[0]}, max={bbox[1]}\n"

            # Add normalization info if applied
            if result.get("normalized"):
                scale = result.get("scale_applied", 1.0)
                output += f"Size normalized: scale factor {scale:.6f} applied (target size: {target_size}m)\n"

            return output
        else:
            return f"Failed to download model: {result.get('message', 'Unknown error')}"
    except Exception as e:
        logger.error(f"Error downloading Sketchfab model: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return f"Error downloading Sketchfab model: {str(e)}"


def _process_bbox(original_bbox: list[float] | list[int] | None) -> list[int] | None:
    if original_bbox is None:
        return None
    if any(i <= 0 for i in original_bbox):
        raise ValueError("Incorrect number range: bbox must be bigger than zero!")
    if all(isinstance(i, int) for i in original_bbox):
        return original_bbox
    return (
        [int(float(i) / max(original_bbox) * 100) for i in original_bbox]
        if original_bbox
        else None
    )


@mcp.tool()
@trajectory_tool("generate_hyper3d_model_via_text")
async def generate_hyper3d_model_via_text(
    ctx: Context,
    text_prompt: str,
    bbox_condition: list[float] = None,
    user_prompt: str = "",
) -> str:
    """
    Generate 3D asset using Hyper3D by giving description of the desired asset, and import the asset into Blender.
    The 3D asset has built-in materials.
    The generated model has a normalized size, so re-scaling after generation can be useful.

    Parameters:
    - text_prompt: A short description of the desired model in **English**.
    - bbox_condition: Optional. If given, it has to be a list of floats of length 3. Controls the ratio between [Length, Width, Height] of the model.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns a message indicating success or failure.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "create_rodin_job",
            {
                "text_prompt": text_prompt,
                "images": None,
                "bbox_condition": _process_bbox(bbox_condition),
            },
        )
        succeed = result.get("submit_time", False)
        if succeed:
            return json.dumps(
                {
                    "task_uuid": result["uuid"],
                    "subscription_key": result["jobs"]["subscription_key"],
                }
            )
        else:
            return json.dumps(result)
    except Exception as e:
        logger.error(f"Error generating Hyper3D task: {str(e)}")
        return f"Error generating Hyper3D task: {str(e)}"


@mcp.tool()
@trajectory_tool("generate_hyper3d_model_via_images")
async def generate_hyper3d_model_via_images(
    ctx: Context,
    input_image_paths: list[str] = None,
    input_image_urls: list[str] = None,
    bbox_condition: list[float] = None,
    user_prompt: str = "",
) -> str:
    """
    Generate 3D asset using Hyper3D by giving images of the wanted asset, and import the generated asset into Blender.
    The 3D asset has built-in materials.
    The generated model has a normalized size, so re-scaling after generation can be useful.

    Parameters:
    - input_image_paths: The **absolute** paths of input images. Even if only one image is provided, wrap it into a list. Required if Hyper3D Rodin in MAIN_SITE mode.
    - input_image_urls: The URLs of input images. Even if only one image is provided, wrap it into a list. Required if Hyper3D Rodin in FAL_AI mode.
    - bbox_condition: Optional. If given, it has to be a list of ints of length 3. Controls the ratio between [Length, Width, Height] of the model.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Only one of {input_image_paths, input_image_urls} should be given at a time, depending on the Hyper3D Rodin's current mode.
    Returns a message indicating success or failure.
    """
    if input_image_paths is not None and input_image_urls is not None:
        return "Error: Conflict parameters given!"
    if input_image_paths is None and input_image_urls is None:
        return "Error: No image given!"
    if input_image_paths is not None:
        if not all(os.path.exists(i) for i in input_image_paths):
            return "Error: not all image paths are valid!"
        images = []
        for path in input_image_paths:
            with open(path, "rb") as f:
                images.append(
                    (Path(path).suffix, base64.b64encode(f.read()).decode("ascii"))
                )
    elif input_image_urls is not None:
        if not all(urlparse(i) for i in input_image_paths):
            return "Error: not all image URLs are valid!"
        images = input_image_urls.copy()
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "create_rodin_job",
            {
                "text_prompt": None,
                "images": images,
                "bbox_condition": _process_bbox(bbox_condition),
            },
        )
        succeed = result.get("submit_time", False)
        if succeed:
            return json.dumps(
                {
                    "task_uuid": result["uuid"],
                    "subscription_key": result["jobs"]["subscription_key"],
                }
            )
        else:
            return json.dumps(result)
    except Exception as e:
        logger.error(f"Error generating Hyper3D task: {str(e)}")
        return f"Error generating Hyper3D task: {str(e)}"


@mcp.tool()
@telemetry_tool("poll_rodin_job_status")
async def poll_rodin_job_status(
    ctx: Context,
    subscription_key: str = None,
    request_id: str = None,
):
    """
    Check if the Hyper3D Rodin generation task is completed.

    For Hyper3D Rodin mode MAIN_SITE:
        Parameters:
        - subscription_key: The subscription_key given in the generate model step.

        Returns a list of status. The task is done if all status are "Done".
        If "Failed" showed up, the generating process failed.
        This is a polling API, so only proceed if the status are finally determined ("Done" or "Canceled").

    For Hyper3D Rodin mode FAL_AI:
        Parameters:
        - request_id: The request_id given in the generate model step.

        Returns the generation task status. The task is done if status is "COMPLETED".
        The task is in progress if status is "IN_PROGRESS".
        If status other than "COMPLETED", "IN_PROGRESS", "IN_QUEUE" showed up, the generating process might be failed.
        This is a polling API, so only proceed if the status are finally determined ("COMPLETED" or some failed state).
    """
    try:
        blender = get_blender_connection()
        kwargs = {}
        if subscription_key:
            kwargs = {
                "subscription_key": subscription_key,
            }
        elif request_id:
            kwargs = {
                "request_id": request_id,
            }
        result = blender.send_command("poll_rodin_job_status", kwargs)
        return result
    except Exception as e:
        logger.error(f"Error generating Hyper3D task: {str(e)}")
        return f"Error generating Hyper3D task: {str(e)}"


@mcp.tool()
@trajectory_tool("import_generated_asset")
async def import_generated_asset(
    ctx: Context,
    name: str,
    task_uuid: str = None,
    request_id: str = None,
):
    """
    Import the asset generated by Hyper3D Rodin after the generation task is completed.

    Parameters:
    - name: The name of the object in scene
    - task_uuid: For Hyper3D Rodin mode MAIN_SITE: The task_uuid given in the generate model step.
    - request_id: For Hyper3D Rodin mode FAL_AI: The request_id given in the generate model step.

    Only give one of {task_uuid, request_id} based on the Hyper3D Rodin Mode!
    Return if the asset has been imported successfully.
    """
    try:
        blender = get_blender_connection()
        kwargs = {"name": name}
        if task_uuid:
            kwargs["task_uuid"] = task_uuid
        elif request_id:
            kwargs["request_id"] = request_id
        result = blender.send_command("import_generated_asset", kwargs)
        return result
    except Exception as e:
        logger.error(f"Error generating Hyper3D task: {str(e)}")
        return f"Error generating Hyper3D task: {str(e)}"


@mcp.tool()
def get_hunyuan3d_status(ctx: Context, user_prompt: str = "") -> str:
    """
    Check if Hunyuan3D integration is enabled in Blender.
    Returns a message indicating whether Hunyuan3D features are available.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_hunyuan3d_status")
        message = result.get("message", "")
        return message
    except Exception as e:
        logger.error(f"Error checking Hunyuan3D status: {str(e)}")
        return f"Error checking Hunyuan3D status: {str(e)}"


@mcp.tool()
@trajectory_tool("generate_hunyuan3d_model")
async def generate_hunyuan3d_model(
    ctx: Context,
    text_prompt: str = None,
    input_image_url: str = None,
    user_prompt: str = "",
) -> str:
    """
    Generate 3D asset using Hunyuan3D by providing either text description, image reference,
    or both for the desired asset, and import the asset into Blender.
    The 3D asset has built-in materials.

    Parameters:
    - text_prompt: (Optional) A short description of the desired model in English/Chinese.
    - input_image_url: (Optional) The local or remote url of the input image. Accepts None if only using text prompt.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns:
    - When successful, returns a JSON with job_id (format: "job_xxx") indicating the task is in progress
    - When the job completes, the status will change to "DONE" indicating the model has been imported
    - Returns error message if the operation fails
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "create_hunyuan_job",
            {
                "text_prompt": text_prompt,
                "image": input_image_url,
            },
        )
        if "JobId" in result.get("Response", {}):
            job_id = result["Response"]["JobId"]
            formatted_job_id = f"job_{job_id}"
            return json.dumps(
                {
                    "job_id": formatted_job_id,
                }
            )
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Error generating Hunyuan3D task: {str(e)}")
        return f"Error generating Hunyuan3D task: {str(e)}"


@mcp.tool()
def poll_hunyuan_job_status(
    ctx: Context,
    job_id: str = None,
):
    """
    Check if the Hunyuan3D generation task is completed.

    For Hunyuan3D:
        Parameters:
        - job_id: The job_id given in the generate model step.

        Returns the generation task status. The task is done if status is "DONE".
        The task is in progress if status is "RUN".
        If status is "DONE", returns ResultFile3Ds with one or more downloadable model URLs.
        Prefer a .glb URL when present (self-contained with materials); otherwise use a .zip/.obj asset URL.
        This is a polling API, so only proceed if the status are finally determined ("DONE" or some failed state).
    """
    try:
        blender = get_blender_connection()
        kwargs = {
            "job_id": job_id,
        }
        result = blender.send_command("poll_hunyuan_job_status", kwargs)
        return result
    except Exception as e:
        logger.error(f"Error generating Hunyuan3D task: {str(e)}")
        return f"Error generating Hunyuan3D task: {str(e)}"


@mcp.tool()
@trajectory_tool("import_generated_asset_hunyuan")
async def import_generated_asset_hunyuan(
    ctx: Context,
    name: str,
    zip_file_url: str,
):
    """
    Import the asset generated by Hunyuan3D after the generation task is completed.

    Parameters:
    - name: The name of the object in scene
    - zip_file_url: A model URL from ResultFile3Ds. Prefer a .glb URL when available; .zip/.obj URLs still work as a fallback.

    Return if the asset has been imported successfully.
    """
    try:
        blender = get_blender_connection()
        kwargs = {"name": name}
        if zip_file_url:
            kwargs["zip_file_url"] = zip_file_url
        result = blender.send_command("import_generated_asset_hunyuan", kwargs)
        return result
    except Exception as e:
        logger.error(f"Error generating Hunyuan3D task: {str(e)}")
        return f"Error generating Hunyuan3D task: {str(e)}"


# ---------------------------------------------------------------------------
# model_from_reference / model_generate_from_description orchestration
#
# These collapse the generate -> poll -> import workflow (three separate
# tool calls above, per provider) into a single call, auto-selecting
# whichever provider is enabled in Blender.
# ---------------------------------------------------------------------------


def _rodin_extract_job_ids(result: dict[str, Any]) -> dict[str, str]:
    if not isinstance(result, dict):
        raise ValueError(f"Unexpected response from Hyper3D: {result}")
    if result.get("error"):
        raise ValueError(f"Hyper3D error: {result['error']}")
    if "uuid" in result and "jobs" in result:
        return {
            "task_uuid": result["uuid"],
            "subscription_key": result["jobs"]["subscription_key"],
        }
    if "request_id" in result:
        return {"request_id": result["request_id"]}
    raise ValueError(f"Could not determine Hyper3D job id from response: {result}")


async def _rodin_wait_until_done(
    blender, job_ids: dict[str, str], timeout_s: float
) -> None:
    poll_kwargs = {
        k: v for k, v in job_ids.items() if k in ("subscription_key", "request_id")
    }
    deadline = time.monotonic() + timeout_s
    while True:
        status = blender.send_command("poll_rodin_job_status", poll_kwargs)
        if not isinstance(status, dict):
            raise ValueError(f"Unexpected Hyper3D poll response: {status}")
        if "status_list" in status:
            statuses = status["status_list"]
            if any(s == "Failed" for s in statuses):
                raise ValueError(f"Hyper3D generation failed: {statuses}")
            if statuses and all(s == "Done" for s in statuses):
                return
        else:
            job_status = status.get("status")
            if job_status == "COMPLETED":
                return
            if job_status not in (None, "IN_PROGRESS", "IN_QUEUE"):
                raise ValueError(f"Hyper3D generation failed: {status}")
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"Timed out after {timeout_s}s waiting for Hyper3D generation"
            )
        await asyncio.sleep(3)


async def _generate_hyper3d_and_import(
    blender,
    *,
    name: str = None,
    text_prompt: str = None,
    images: list = None,
    bbox_condition: list = None,
    timeout_s: float,
) -> dict[str, Any]:
    result = blender.send_command(
        "create_rodin_job",
        {
            "text_prompt": text_prompt,
            "images": images,
            "bbox_condition": _process_bbox(bbox_condition),
        },
    )
    job_ids = _rodin_extract_job_ids(result)
    await _rodin_wait_until_done(blender, job_ids, timeout_s)
    import_kwargs = {"name": name or "GeneratedModel"}
    import_kwargs.update(
        {k: v for k, v in job_ids.items() if k in ("task_uuid", "request_id")}
    )
    import_result = blender.send_command("import_generated_asset", import_kwargs)
    if isinstance(import_result, dict) and import_result.get("succeed") is False:
        raise ValueError(
            f"Hyper3D import failed: {import_result.get('error', import_result)}"
        )
    return {"provider": "hyper3d", "import_result": import_result}


def _find_urls(value) -> list:
    """Recursively collect http(s) URL strings from an arbitrary JSON-like structure."""
    urls = []
    if isinstance(value, str):
        if value.startswith("http://") or value.startswith("https://"):
            urls.append(value)
    elif isinstance(value, dict):
        for v in value.values():
            urls.extend(_find_urls(v))
    elif isinstance(value, list):
        for v in value:
            urls.extend(_find_urls(v))
    return urls


async def _hunyuan_wait_for_model_url(blender, job_id: str, timeout_s: float) -> str:
    deadline = time.monotonic() + timeout_s
    while True:
        status = blender.send_command("poll_hunyuan_job_status", {"job_id": job_id})
        if not isinstance(status, dict):
            raise ValueError(f"Unexpected Hunyuan3D poll response: {status}")
        if status.get("error"):
            raise ValueError(f"Hunyuan3D error: {status['error']}")
        response = status.get("Response", {})
        job_status = response.get("Status")
        if job_status == "DONE":
            urls = _find_urls(response.get("ResultFile3Ds", response))
            glb = next(
                (
                    u
                    for u in urls
                    if u.split("?", 1)[0].split("#", 1)[0].lower().endswith(".glb")
                ),
                None,
            )
            model_url = glb or (urls[0] if urls else None)
            if not model_url:
                raise ValueError(
                    f"Hunyuan3D job completed but no result file URL was found: {status}"
                )
            return model_url
        if job_status not in (
            None,
            "WAIT",
            "RUN",
            "SUBMITTED",
            "PENDING",
            "IN_PROGRESS",
        ):
            raise ValueError(f"Hunyuan3D generation failed: {status}")
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"Timed out after {timeout_s}s waiting for Hunyuan3D generation"
            )
        await asyncio.sleep(3)


async def _generate_hunyuan_and_import(
    blender,
    *,
    name: str = None,
    text_prompt: str = None,
    image: str = None,
    timeout_s: float,
) -> dict[str, Any]:
    result = blender.send_command(
        "create_hunyuan_job",
        {
            "text_prompt": text_prompt,
            "image": image,
        },
    )
    if not isinstance(result, dict):
        raise ValueError(f"Unexpected response from Hunyuan3D: {result}")
    if result.get("error"):
        raise ValueError(f"Hunyuan3D error: {result['error']}")
    response = result.get("Response", {})
    if "JobId" in response:
        job_id = f"job_{response['JobId']}"
        model_url = await _hunyuan_wait_for_model_url(blender, job_id, timeout_s)
        import_result = blender.send_command(
            "import_generated_asset_hunyuan",
            {
                "name": name or "GeneratedModel",
                "zip_file_url": model_url,
            },
        )
        return {"provider": "hunyuan3d", "import_result": import_result}
    if result.get("status") == "DONE":
        # LOCAL_API mode generates and imports synchronously within create_hunyuan_job.
        return {"provider": "hunyuan3d", "import_result": result}
    raise ValueError(f"Unexpected response from Hunyuan3D: {result}")


async def _select_3d_provider(blender, provider: str) -> str:
    provider = (provider or "auto").lower()
    if provider not in ("auto", "hyper3d", "hunyuan3d"):
        raise ValueError(
            f"Unknown provider: {provider}. Must be one of auto, hyper3d, hunyuan3d"
        )
    hyper3d_enabled = False
    hunyuan3d_enabled = False
    if provider in ("auto", "hyper3d"):
        status = blender.send_command("get_hyper3d_status")
        hyper3d_enabled = bool(status.get("enabled", False))
    if provider in ("auto", "hunyuan3d"):
        status = blender.send_command("get_hunyuan3d_status")
        hunyuan3d_enabled = bool(status.get("enabled", False))
    if provider == "hyper3d":
        if not hyper3d_enabled:
            raise ValueError("Hyper3D Rodin is not enabled in Blender.")
        return "hyper3d"
    if provider == "hunyuan3d":
        if not hunyuan3d_enabled:
            raise ValueError("Hunyuan3D is not enabled in Blender.")
        return "hunyuan3d"
    if hyper3d_enabled:
        return "hyper3d"
    if hunyuan3d_enabled:
        return "hunyuan3d"
    raise ValueError(
        "No 3D generation provider is enabled in Blender. Enable Hyper3D Rodin or Hunyuan3D in the addon preferences."
    )


@mcp.tool()
@trajectory_tool("model_from_reference")
async def model_from_reference(
    ctx: Context,
    image_path_or_url: str,
    name: str = None,
    provider: str = "auto",
    timeout_s: float = 180,
    user_prompt: str = "",
) -> str:
    """
    Generate a 3D model from a reference image and import it into the scene.
    Auto-selects an enabled AI provider (Hyper3D Rodin or Hunyuan3D), collapsing the
    generate -> poll -> import workflow into a single call.

    Parameters:
    - image_path_or_url: Absolute local file path or http(s) URL of the reference image.
    - name: Optional name for the imported object. Defaults to a generic generated name.
    - provider: "auto" (default, prefers Hyper3D if enabled), "hyper3d", or "hunyuan3d".
    - timeout_s: Maximum seconds to wait for generation to finish before giving up.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the import result, or an error if no provider is enabled or generation fails.
    """
    try:
        blender = get_blender_connection()
        chosen = await _select_3d_provider(blender, provider)
        if chosen == "hyper3d":
            if os.path.exists(image_path_or_url):
                with open(image_path_or_url, "rb") as f:
                    images = [
                        (
                            Path(image_path_or_url).suffix,
                            base64.b64encode(f.read()).decode("ascii"),
                        )
                    ]
            else:
                images = [image_path_or_url]
            result = await _generate_hyper3d_and_import(
                blender,
                name=name,
                images=images,
                timeout_s=timeout_s,
            )
        else:
            result = await _generate_hunyuan_and_import(
                blender,
                name=name,
                image=image_path_or_url,
                timeout_s=timeout_s,
            )
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Error generating model from reference: {str(e)}")
        return f"Error generating model from reference: {str(e)}"


@mcp.tool()
@trajectory_tool("model_generate_from_description")
async def model_generate_from_description(
    ctx: Context,
    text_prompt: str,
    bbox_condition: list[float] = None,
    name: str = None,
    provider: str = "auto",
    timeout_s: float = 180,
    user_prompt: str = "",
) -> str:
    """
    Generate a 3D model from a text description and import it into the scene.
    Auto-selects an enabled AI provider (Hyper3D Rodin or Hunyuan3D), collapsing the
    generate -> poll -> import workflow into a single call.

    Parameters:
    - text_prompt: A short description of the desired model in English.
    - bbox_condition: Optional list of floats of length 3 controlling the [Length, Width, Height] ratio (Hyper3D only).
    - name: Optional name for the imported object. Defaults to a generic generated name.
    - provider: "auto" (default, prefers Hyper3D if enabled), "hyper3d", or "hunyuan3d".
    - timeout_s: Maximum seconds to wait for generation to finish before giving up.
    - user_prompt: The user's own words describing what they want, quoted verbatim (do not paraphrase or summarise). Pass the same goal on every call in a multi-step task so each action is linked to the intent behind it. Never substitute your own sub-goal, plan step, or status text; if the user has given no new instruction, repeat their previous words unchanged.

    Returns the import result, or an error if no provider is enabled or generation fails.
    """
    try:
        blender = get_blender_connection()
        chosen = await _select_3d_provider(blender, provider)
        if chosen == "hyper3d":
            result = await _generate_hyper3d_and_import(
                blender,
                name=name,
                text_prompt=text_prompt,
                bbox_condition=bbox_condition,
                timeout_s=timeout_s,
            )
        else:
            result = await _generate_hunyuan_and_import(
                blender,
                name=name,
                text_prompt=text_prompt,
                timeout_s=timeout_s,
            )
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Error generating model from description: {str(e)}")
        return f"Error generating model from description: {str(e)}"


@mcp.tool()
def record_trajectory_feedback(
    ctx: Context,
    feedback: str,
    correction_text: str = None,
    step_index: int = None,
    user_prompt: str = "",
) -> str:
    """
    Record evaluation feedback for a captured trajectory step.

    Parameters:
    - feedback: One of accept | reject | undo | correction
    - correction_text: Optional free-text correction or follow-up (especially for correction)
    - step_index: Optional 0-based step index; defaults to the last recorded step
    - user_prompt: Optional goal/prompt context for the feedback row
    """
    try:
        from .trajectory import get_trajectory_recorder

        allowed = {"accept", "reject", "undo", "correction"}
        if feedback not in allowed:
            return f"Error: feedback must be one of {sorted(allowed)}"

        recorder = get_trajectory_recorder()
        ok = recorder.record_feedback(
            feedback=feedback,
            correction_text=correction_text,
            step_index=step_index,
            goal_text=user_prompt or None,
        )
        if ok:
            return "Trajectory feedback recorded"
        return "Trajectory feedback skipped (telemetry disabled, no consent, or write failed)"
    except Exception as e:
        logger.debug(f"record_trajectory_feedback failed: {e}")
        return f"Trajectory feedback skipped: {e}"


@mcp.prompt()
def asset_creation_strategy() -> str:
    """Defines the preferred strategy for creating assets in Blender"""
    return """When creating 3D content in Blender, always start by checking if integrations are available:

    0. Before anything, always check the scene from get_scene_info()
    
    **IMPORTANT: Visual Verification**
    - Use get_viewport_screenshot() BEFORE making changes to see the current state
    - Use get_viewport_screenshot() AFTER executing code or importing assets to verify the result
    - This helps confirm your changes worked as expected and catch any visual issues

    **IMPORTANT: Trajectory feedback**
    - When the user accepts a result ("looks good", "keep that"), call record_trajectory_feedback(feedback="accept")
    - When they reject or ask to undo, call record_trajectory_feedback(feedback="reject" or "undo")
    - When they correct you ("too dark", "make it taller"), call record_trajectory_feedback(feedback="correction", correction_text=<their correction>)
    1. First use the following tools to verify if the following integrations are enabled:
        1. PolyHaven
            Use get_polyhaven_status() to verify its status
            If PolyHaven is enabled:
            - For objects/models: Use download_polyhaven_asset() with asset_type="models"
            - For materials/textures: Use download_polyhaven_asset() with asset_type="textures"
            - For environment lighting: Use download_polyhaven_asset() with asset_type="hdris"
        2. Sketchfab
            Sketchfab is good at Realistic models, and has a wider variety of models than PolyHaven.
            Use get_sketchfab_status() to verify its status
            If Sketchfab is enabled:
            - For objects/models: First search using search_sketchfab_models() with your query
            - Then download specific models using download_sketchfab_model() with the UID
            - Note that only downloadable models can be accessed, and API key must be properly configured
            - Sketchfab has a wider variety of models than PolyHaven, especially for specific subjects
        3. Hyper3D(Rodin)
            Hyper3D Rodin is good at generating 3D models for single item.
            So don't try to:
            1. Generate the whole scene with one shot
            2. Generate ground using Hyper3D
            3. Generate parts of the items separately and put them together afterwards

            Use get_hyper3d_status() to verify its status
            If Hyper3D is enabled:
            - For objects/models, do the following steps:
                1. Create the model generation task
                    - Use generate_hyper3d_model_via_images() if image(s) is/are given
                    - Use generate_hyper3d_model_via_text() if generating 3D asset using text prompt
                    If key type is free_trial and insufficient balance error returned, tell the user that the free trial key can only generated limited models everyday, they can choose to:
                    - Wait for another day and try again
                    - Go to hyper3d.ai to find out how to get their own API key
                    - Go to fal.ai to get their own private API key
                2. Poll the status
                    - Use poll_rodin_job_status() to check if the generation task has completed or failed
                3. Import the asset
                    - Use import_generated_asset() to import the generated GLB model the asset
                4. After importing the asset, ALWAYS check the world_bounding_box of the imported mesh, and adjust the mesh's location and size
                    Adjust the imported mesh's location, scale, rotation, so that the mesh is on the right spot.

                You can reuse assets previous generated by running python code to duplicate the object, without creating another generation task.
        4. Hunyuan3D
            Hunyuan3D is good at generating 3D models for single item.
            So don't try to:
            1. Generate the whole scene with one shot
            2. Generate ground using Hunyuan3D
            3. Generate parts of the items separately and put them together afterwards

            Use get_hunyuan3d_status() to verify its status
            If Hunyuan3D is enabled:
                if Hunyuan3D mode is "OFFICIAL_API":
                    - For objects/models, do the following steps:
                        1. Create the model generation task
                            - Use generate_hunyuan3d_model by providing either a **text description** OR an **image(local or urls) reference**.
                            - Go to cloud.tencent.com out how to get their own SecretId and SecretKey
                        2. Poll the status
                            - Use poll_hunyuan_job_status() to check if the generation task has completed or failed
                        3. Import the asset
                            - Use import_generated_asset_hunyuan() with a ResultFile3Ds URL (prefer .glb, else .zip/.obj)
                    if Hunyuan3D mode is "LOCAL_API":
                        - For objects/models, do the following steps:
                        1. Create the model generation task
                            - Use generate_hunyuan3d_model if image (local or urls)  or text prompt is given and import the asset

                You can reuse assets previous generated by running python code to duplicate the object, without creating another generation task.

        You can also skip the create/poll/import steps above and call model_from_reference() (image-to-3D)
        or model_generate_from_description() (text-to-3D) directly - they auto-select whichever of
        Hyper3D/Hunyuan3D is enabled and do the generate/poll/import in one call.

    2. For primitives and direct mesh/model editing, use the dedicated tools instead of execute_blender_code:
        - mesh_create_primitive() for cubes, spheres, cylinders, cones, tori, planes, and curves
        - mesh_extrude(), mesh_inset(), mesh_bevel(), mesh_bridge(), mesh_boolean(), mesh_subdivide(), mesh_remesh(), mesh_solidify() for direct mesh edits
        - model_match_reference(), model_blockout(), model_refine(), model_detail(), model_symmetrize(), model_mirror(), model_array(), model_radial_array() for higher-level modeling operations

    2.5. For non-destructive hard-surface workflows (utility objects, ID materials, LOD naming, viewport overlays), use the ND (HugeMenace) tools instead of execute_blender_code:
        - Use get_nd_status() to verify its status
        - nd_boolean(), nd_mark_as_util(), nd_clean_utils() for the utility-object boolean workflow
        - nd_create_id_material(), nd_bulk_create_id_materials(), nd_clear_materials(), nd_set_lod_suffix(), nd_name_sync() for export/packaging prep
        - nd_single_vertex(), nd_clear_edge_marks(), nd_clear_vertex_groups(), nd_apply_modifiers() for sketch/data cleanup
        - nd_viewport_toggle(), nd_capture_utils() for viewport helpers

    3. Always check the world_bounding_box for each item so that:
        - Ensure that all objects that should not be clipping are not clipping.
        - Items have right spatial relationship.
    
    4. Recommended asset source priority:
        - For specific existing objects: First try Sketchfab, then PolyHaven
        - For generic objects/furniture: First try PolyHaven, then Sketchfab
        - For custom or unique items not available in libraries: Use Hyper3D Rodin or Hunyuan3D
        - For environment lighting: Use PolyHaven HDRIs
        - For materials/textures: Use PolyHaven textures

    Only fall back to execute_blender_code scripting when:
    - PolyHaven, Sketchfab, Hyper3D, and Hunyuan3D are all disabled and no suitable asset exists in any of the libraries
    - Hyper3D Rodin or Hunyuan3D failed to generate the desired asset
    - The task specifically requires a basic material/color
    - The needed operation has no dedicated mesh_*/model_* tool (e.g. a primitive is explicitly requested - use mesh_create_primitive() instead, or a mesh edit covered by mesh_extrude/mesh_inset/mesh_bevel/mesh_bridge/mesh_boolean/mesh_subdivide/mesh_remesh/mesh_solidify/model_match_reference/model_blockout/model_refine/model_detail/model_symmetrize/model_mirror/model_array/model_radial_array)

    **Best Practices:**
    - Always take a screenshot after completing a task to verify the visual result
    - Always call get_scene_info() after completing a task to verify the changes worked
    - When executing multiple operations, take intermediate screenshots to confirm each step
    - If something looks wrong in the screenshot or scene info, investigate and fix before proceeding
    """


# Main execution


def main():
    """Run the MCP server, or addon install CLI subcommands."""
    if len(sys.argv) > 1 and sys.argv[1] in {
        "install-addon",
        "addon-paths",
        "-h",
        "--help",
    }:
        code = run_addon_cli(sys.argv[1:])
        if code >= 0:
            raise SystemExit(code)

    # When run by hand (stdin is a TTY) the server appears to "hang" while it
    # silently waits for an MCP client; log a hint so that state is obvious.
    # Launched by a client, stdin is a pipe so this is skipped, and logging goes
    # to stderr, never to the stdio protocol on stdout.
    try:
        interactive = sys.stdin.isatty()
    except (AttributeError, OSError):
        interactive = False
    if interactive:
        logger.info(
            "BlenderMCP is an MCP server and is meant to be launched by your MCP "
            "client (Claude Desktop, Cursor, VS Code, ...), not run by hand. "
            "It will now wait silently for a client on stdin -- that is normal, "
            "not a hang. Press Ctrl-C to exit. "
            "Setup guide: https://github.com/ahujasid/blender-mcp#installation "
            "(if the addon is outdated this logs how to update it: uvx blender-mcp install-addon)"
        )
    mcp.run()


if __name__ == "__main__":
    main()
