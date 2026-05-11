# blender_mcp_server.py
from mcp.server.fastmcp import FastMCP, Context, Image
import socket
import json
import asyncio
import logging
import tempfile
from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any
import os

# Import telemetry
from .telemetry import record_startup, get_telemetry
from .telemetry_decorator import telemetry_tool

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BlenderMCPServer")

# Default configuration
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876

@dataclass
class BlenderConnection:
    host: str
    port: int
    sock: socket.socket = None

    def connect(self) -> bool:
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
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error disconnecting from Blender: {str(e)}")
            finally:
                self.sock = None

    def receive_full_response(self, sock, buffer_size=8192):
        chunks = []
        sock.settimeout(180.0)
        try:
            while True:
                try:
                    chunk = sock.recv(buffer_size)
                    if not chunk:
                        if not chunks:
                            raise Exception("Connection closed before receiving any data")
                        break
                    chunks.append(chunk)
                    try:
                        data = b''.join(chunks)
                        json.loads(data.decode('utf-8'))
                        logger.info(f"Received complete response ({len(data)} bytes)")
                        return data
                    except json.JSONDecodeError:
                        continue
                except socket.timeout:
                    logger.warning("Socket timeout during chunked receive")
                    break
                except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                    logger.error(f"Socket connection error during receive: {str(e)}")
                    raise
        except socket.timeout:
            logger.warning("Socket timeout during chunked receive")
        except Exception as e:
            logger.error(f"Error during receive: {str(e)}")
            raise

        if chunks:
            data = b''.join(chunks)
            logger.info(f"Returning data after receive completion ({len(data)} bytes)")
            try:
                json.loads(data.decode('utf-8'))
                return data
            except json.JSONDecodeError:
                raise Exception("Incomplete JSON response received")
        else:
            raise Exception("No data received")

    def send_command(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.sock and not self.connect():
            raise ConnectionError("Not connected to Blender")

        command = {"type": command_type, "params": params or {}}

        try:
            logger.info(f"Sending command: {command_type} with params: {params}")
            self.sock.sendall(json.dumps(command).encode('utf-8'))
            logger.info(f"Command sent, waiting for response...")
            self.sock.settimeout(180.0)
            response_data = self.receive_full_response(self.sock)
            logger.info(f"Received {len(response_data)} bytes of data")
            response = json.loads(response_data.decode('utf-8'))
            logger.info(f"Response parsed, status: {response.get('status', 'unknown')}")

            if response.get("status") == "error":
                logger.error(f"Blender error: {response.get('message')}")
                raise Exception(response.get("message", "Unknown error from Blender"))

            return response.get("result", {})
        except socket.timeout:
            logger.error("Socket timeout while waiting for response from Blender")
            self.sock = None
            raise Exception("Timeout waiting for Blender response - try simplifying your request")
        except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
            logger.error(f"Socket connection error: {str(e)}")
            self.sock = None
            raise Exception(f"Connection to Blender lost: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Blender: {str(e)}")
            if 'response_data' in locals() and response_data:
                logger.error(f"Raw response (first 200 bytes): {response_data[:200]}")
            raise Exception(f"Invalid response from Blender: {str(e)}")
        except Exception as e:
            logger.error(f"Error communicating with Blender: {str(e)}")
            self.sock = None
            raise Exception(f"Communication error with Blender: {str(e)}")

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    try:
        logger.info("BlenderMCP server starting up")

        try:
            record_startup()
        except Exception as e:
            logger.debug(f"Failed to record startup telemetry: {e}")

        try:
            blender = get_blender_connection()
            logger.info("Successfully connected to Blender on startup")
        except Exception as e:
            logger.warning(f"Could not connect to Blender on startup: {str(e)}")
            logger.warning("Make sure the Blender addon is running before using Blender resources or tools")

        yield {}
    finally:
        global _blender_connection
        if _blender_connection:
            logger.info("Disconnecting from Blender on shutdown")
            _blender_connection.disconnect()
            _blender_connection = None
        logger.info("BlenderMCP server shut down")

mcp = FastMCP("BlenderMCP", lifespan=server_lifespan)

_blender_connection = None

def get_blender_connection():
    global _blender_connection

    if _blender_connection is not None:
        try:
            _blender_connection.send_command("ping")
            return _blender_connection
        except Exception as e:
            logger.warning(f"Existing connection is no longer valid: {str(e)}")
            try:
                _blender_connection.disconnect()
            except:
                pass
            _blender_connection = None

    if _blender_connection is None:
        host = os.getenv("BLENDER_HOST", DEFAULT_HOST)
        port = int(os.getenv("BLENDER_PORT", DEFAULT_PORT))
        _blender_connection = BlenderConnection(host=host, port=port)
        if not _blender_connection.connect():
            logger.error("Failed to connect to Blender")
            _blender_connection = None
            raise Exception("Could not connect to Blender. Make sure the Blender addon is running.")
        logger.info("Created new persistent connection to Blender")

    return _blender_connection


@telemetry_tool("get_scene_info")
@mcp.tool()
def get_scene_info(ctx: Context) -> str:
    """Get detailed information about the current Blender scene."""
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_scene_info")
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting scene info from Blender: {str(e)}")
        return f"Error getting scene info: {str(e)}"

@telemetry_tool("get_object_info")
@mcp.tool()
def get_object_info(ctx: Context, object_name: str) -> str:
    """
    Get detailed information about a specific object in the Blender scene.

    Parameters:
    - object_name: The name of the object to get information about
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_object_info", {"name": object_name})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting object info from Blender: {str(e)}")
        return f"Error getting object info: {str(e)}"

@telemetry_tool("get_viewport_screenshot")
@mcp.tool()
def get_viewport_screenshot(ctx: Context, max_size: int = 800) -> Image:
    """
    Capture a screenshot of the current Blender 3D viewport.

    Parameters:
    - max_size: Maximum size in pixels for the largest dimension (default: 800)
    """
    try:
        blender = get_blender_connection()
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"blender_screenshot_{os.getpid()}.png")

        result = blender.send_command("get_viewport_screenshot", {
            "max_size": max_size,
            "filepath": temp_path,
            "format": "png"
        })

        if "error" in result:
            raise Exception(result["error"])
        if not os.path.exists(temp_path):
            raise Exception("Screenshot file was not created")

        with open(temp_path, 'rb') as f:
            image_bytes = f.read()
        os.remove(temp_path)

        return Image(data=image_bytes, format="png")
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        raise Exception(f"Screenshot failed: {str(e)}")


@telemetry_tool("execute_blender_code")
@mcp.tool()
def execute_blender_code(ctx: Context, code: str) -> str:
    """
    Execute arbitrary Python code in Blender. Break complex operations into smaller chunks.

    Parameters:
    - code: The Python code to execute
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("execute_code", {"code": code})
        return f"Code executed successfully: {result.get('result', '')}"
    except Exception as e:
        logger.error(f"Error executing code: {str(e)}")
        return f"Error executing code: {str(e)}"


@telemetry_tool("import_stl")
@mcp.tool()
def import_stl(ctx: Context, filepath: str, object_name: str = None) -> str:
    """
    Import an STL file into the current Blender scene. Use this as the first step
    of any print-prep pipeline.

    Parameters:
    - filepath: Absolute path to the .stl file on disk.
    - object_name: Optional. Rename the imported object to this name (otherwise
      Blender derives it from the filename).

    Returns JSON with imported object name, vertex/edge/face count, dimensions in
    millimeters (assuming Blender units == meters, the default), and bounding box.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("import_stl", {
            "filepath": filepath,
            "object_name": object_name,
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error importing STL: {str(e)}")
        return f"Error importing STL: {str(e)}"


@telemetry_tool("export_stl")
@mcp.tool()
def export_stl(
    ctx: Context,
    object_name: str,
    filepath: str,
    apply_modifiers: bool = True,
) -> str:
    """
    Export a single object as an STL file, ready to feed to a slicer.

    Parameters:
    - object_name: Name of the object to export.
    - filepath: Absolute path for the output .stl file (will be overwritten).
    - apply_modifiers: If True, modifiers are baked into the exported geometry
      (default and recommended for print-ready output).

    Returns JSON with the written filepath and final triangle count.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("export_stl", {
            "object_name": object_name,
            "filepath": filepath,
            "apply_modifiers": apply_modifiers,
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error exporting STL: {str(e)}")
        return f"Error exporting STL: {str(e)}"


@telemetry_tool("analyze_mesh_for_print")
@mcp.tool()
def analyze_mesh_for_print(ctx: Context, object_name: str) -> str:
    """
    Run a structured print-readiness check on a mesh and return JSON.

    Reports: vertex/edge/face count, dimensions in millimeters, watertightness
    (non-manifold edge count), boundary loops (holes), disconnected shells,
    inverted-normal face count, degenerate triangle count, and a "ready_to_slice"
    boolean.

    Use this BEFORE running cleanup ops (so you know what to fix) and AFTER
    (so you know it's done). Cheaper for the LLM than asking it to parse
    free-text output from execute_blender_code.

    Parameters:
    - object_name: Name of the mesh object to analyze.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("analyze_mesh_for_print", {
            "object_name": object_name,
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error analyzing mesh: {str(e)}")
        return f"Error analyzing mesh: {str(e)}"


@mcp.prompt()
def print_prep_strategy() -> str:
    """Defines the preferred strategy for preparing AI-generated STL meshes for FDM 3D printing."""
    return """Your job: take an STL produced by an AI mesh generator (e.g. Meshy)
and turn it into a print-ready file for FDM 3D printing. You are NOT building
models from scratch and you are NOT doing rendering, materials, or animation.

Workflow:

0. Inspect the current scene with get_scene_info(). If a mesh is already loaded,
   skip step 1.

1. Import the source STL with import_stl(filepath=...). Note the reported
   dimensions in mm. AI-generated meshes are often arbitrarily scaled - if the
   bounding box looks wrong for the intended physical size, scale it (and then
   re-run analyze_mesh_for_print to confirm dimensions).

2. Run analyze_mesh_for_print(object_name=...) BEFORE touching anything. This
   gives you the baseline: vertex count, manifold status, hole count, inverted
   normals, disconnected shells.

3. Consult the knowledge base via the blender-kb MCP server for the right
   cleanup recipe. Useful entry points:
   - kb_get_topic("mesh_repair") for non-manifold / holes / inverted normals
   - kb_get_topic("fdm_printing_constraints") for wall thickness, overhangs,
     minimum feature size
   - kb_search("decimate") or kb_search("remesh") if poly count is too high
   - kb_get_topic("print_orientation") for build-plate orientation

   Don't guess - if a topic exists, read it before writing bpy code.

4. Apply the cleanup steps using execute_blender_code. Typical pipeline:
   merge by distance -> fill holes -> recalculate normals outside ->
   (optional) remesh or decimate -> orient flattest face down -> move to origin.

5. Re-run analyze_mesh_for_print. The "ready_to_slice" flag should be True
   and non_manifold_edges should be 0. If not, iterate.

6. Take a get_viewport_screenshot() for visual sanity check (especially after
   reorientation).

7. Export with export_stl(object_name=..., filepath=..., apply_modifiers=True).

Hard rules:
- Never add materials, textures, lighting, or animation. Irrelevant for FDM.
- Never download external assets. The user supplies the STL.
- Prefer the structured analyze_mesh_for_print output over parsing free-text
  from execute_blender_code.
- Operations that can mutate the file (export_stl with an existing path) should
  be confirmed with the user if the target already exists and you're not sure.
"""


def main():
    """Run the MCP server"""
    mcp.run()

if __name__ == "__main__":
    main()
