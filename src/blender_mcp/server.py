# blender_mcp_server.py
from mcp.server.fastmcp import FastMCP, Context, Image
import socket
import json
import asyncio
import logging
import tempfile
from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, List, Optional
import os
from pathlib import Path
import base64
from urllib.parse import urlparse, urljoin
import re
import requests
from blender_mcp.settings import get_settings_manager, ModelRing

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BlenderMCPServer")

# Default configuration
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876
SETTINGS = get_settings_manager()
_VLLM_HEALTH_CACHE: Dict[str, bool] = {}

@dataclass
class BlenderConnection:
    host: str
    port: int
    sock: socket.socket = None  # Changed from 'socket' to 'sock' to avoid naming conflict
    
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
        sock.settimeout(15.0)  # Match the addon's timeout
        
        try:
            while True:
                try:
                    chunk = sock.recv(buffer_size)
                    if not chunk:
                        # If we get an empty chunk, the connection might be closed
                        if not chunks:  # If we haven't received anything yet, this is an error
                            raise Exception("Connection closed before receiving any data")
                        break
                    
                    chunks.append(chunk)
                    
                    # Check if we've received a complete JSON object
                    try:
                        data = b''.join(chunks)
                        json.loads(data.decode('utf-8'))
                        # If we get here, it parsed successfully
                        logger.info(f"Received complete response ({len(data)} bytes)")
                        return data
                    except json.JSONDecodeError:
                        # Incomplete JSON, continue receiving
                        continue
                except socket.timeout:
                    # If we hit a timeout during receiving, break the loop and try to use what we have
                    logger.warning("Socket timeout during chunked receive")
                    break
                except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                    logger.error(f"Socket connection error during receive: {str(e)}")
                    raise  # Re-raise to be handled by the caller
        except socket.timeout:
            logger.warning("Socket timeout during chunked receive")
        except Exception as e:
            logger.error(f"Error during receive: {str(e)}")
            raise
            
        # If we get here, we either timed out or broke out of the loop
        # Try to use what we have
        if chunks:
            data = b''.join(chunks)
            logger.info(f"Returning data after receive completion ({len(data)} bytes)")
            try:
                # Try to parse what we have
                json.loads(data.decode('utf-8'))
                return data
            except json.JSONDecodeError:
                # If we can't parse it, it's incomplete
                raise Exception("Incomplete JSON response received")
        else:
            raise Exception("No data received")

    def send_command(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a command to Blender and return the response"""
        if not self.sock and not self.connect():
            raise ConnectionError("Not connected to Blender")
        
        command = {
            "type": command_type,
            "params": params or {}
        }
        
        try:
            # Log the command being sent
            logger.info(f"Sending command: {command_type} with params: {params}")
            
            # Send the command
            self.sock.sendall(json.dumps(command).encode('utf-8'))
            logger.info(f"Command sent, waiting for response...")
            
            # Set a timeout for receiving - use the same timeout as in receive_full_response
            self.sock.settimeout(15.0)  # Match the addon's timeout
            
            # Receive the response using the improved receive_full_response method
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
            # Don't try to reconnect here - let the get_blender_connection handle reconnection
            # Just invalidate the current socket so it will be recreated next time
            self.sock = None
            raise Exception("Timeout waiting for Blender response - try simplifying your request")
        except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
            logger.error(f"Socket connection error: {str(e)}")
            self.sock = None
            raise Exception(f"Connection to Blender lost: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Blender: {str(e)}")
            # Try to log what was received
            if 'response_data' in locals() and response_data:
                logger.error(f"Raw response (first 200 bytes): {response_data[:200]}")
            raise Exception(f"Invalid response from Blender: {str(e)}")
        except Exception as e:
            logger.error(f"Error communicating with Blender: {str(e)}")
            # Don't try to reconnect here - let the get_blender_connection handle reconnection
            self.sock = None
            raise Exception(f"Communication error with Blender: {str(e)}")

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage server startup and shutdown lifecycle"""
    # We don't need to create a connection here since we're using the global connection
    # for resources and tools
    
    try:
        # Just log that we're starting up
        logger.info("BlenderMCP server starting up")
        
        # Try to connect to Blender on startup to verify it's available
        try:
            # This will initialize the global connection if needed
            blender = get_blender_connection()
            logger.info("Successfully connected to Blender on startup")
        except Exception as e:
            logger.warning(f"Could not connect to Blender on startup: {str(e)}")
            logger.warning("Make sure the Blender addon is running before using Blender resources or tools")
        
        # Return an empty context - we're using the global connection
        yield {}
    finally:
        # Clean up the global connection on shutdown
        global _blender_connection
        if _blender_connection:
            logger.info("Disconnecting from Blender on shutdown")
            _blender_connection.disconnect()
            _blender_connection = None
        logger.info("BlenderMCP server shut down")

# Create the MCP server with lifespan support
mcp = FastMCP(
    "BlenderMCP",
    lifespan=server_lifespan
)

@mcp.tool()
def ping(ctx: Context) -> str:
    """
    Lightweight health check that does not contact Blender.
    Returns 'ok' when the MCP server process is up and serving stdio.
    """
    return "ok"


# Resource endpoints

# Global connection for resources (since resources can't access context)
_blender_connection = None
_polyhaven_enabled = False  # Add this global variable

def get_blender_connection():
    """Get or create a persistent Blender connection"""
    global _blender_connection, _polyhaven_enabled  # Add _polyhaven_enabled to globals
    
    # If we have an existing connection, check if it's still valid
    if _blender_connection is not None:
        try:
            # First check if PolyHaven is enabled by sending a ping command
            result = _blender_connection.send_command("get_polyhaven_status")
            # Store the PolyHaven status globally
            _polyhaven_enabled = result.get("enabled", False)
            return _blender_connection
        except Exception as e:
            # Connection is dead, close it and create a new one
            logger.warning(f"Existing connection is no longer valid: {str(e)}")
            try:
                _blender_connection.disconnect()
            except:
                pass
            _blender_connection = None
    
    # Create a new connection if needed
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


@mcp.tool()
def get_scene_info(ctx: Context) -> str:
    """Get detailed information about the current Blender scene"""
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_scene_info")
        
        # Just return the JSON representation of what Blender sent us
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting scene info from Blender: {str(e)}")
        return f"Error getting scene info: {str(e)}"

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
        
        # Just return the JSON representation of what Blender sent us
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting object info from Blender: {str(e)}")
        return f"Error getting object info: {str(e)}"

@mcp.tool()
def get_viewport_screenshot(ctx: Context, max_size: int = 800) -> Image:
    """
    Capture a screenshot of the current Blender 3D viewport.
    
    Parameters:
    - max_size: Maximum size in pixels for the largest dimension (default: 800)
    
    Returns the screenshot as an Image.
    """
    try:
        blender = get_blender_connection()
        
        # Create temp file path
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
        
        # Read the file
        with open(temp_path, 'rb') as f:
            image_bytes = f.read()
        
        # Delete the temp file
        os.remove(temp_path)
        
        return Image(data=image_bytes, format="png")
        
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        raise Exception(f"Screenshot failed: {str(e)}")


@mcp.tool()
def execute_blender_code(ctx: Context, code: str) -> str:
    """
    Execute arbitrary Python code in Blender. Make sure to do it step-by-step by breaking it into smaller chunks.
    
    Parameters:
    - code: The Python code to execute
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
def get_polyhaven_categories(ctx: Context, asset_type: str = "hdris") -> str:
    """
    Get a list of categories for a specific asset type on Polyhaven.
    
    Parameters:
    - asset_type: The type of asset to get categories for (hdris, textures, models, all)
    """
    try:
        blender = get_blender_connection()
        if not _polyhaven_enabled:
            return "PolyHaven integration is disabled. Select it in the sidebar in BlenderMCP, then run it again."
        result = blender.send_command("get_polyhaven_categories", {"asset_type": asset_type})
        
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
def search_polyhaven_assets(
    ctx: Context,
    asset_type: str = "all",
    categories: str = None
) -> str:
    """
    Search for assets on Polyhaven with optional filtering.
    
    Parameters:
    - asset_type: Type of assets to search for (hdris, textures, models, all)
    - categories: Optional comma-separated list of categories to filter by
    
    Returns a list of matching assets with basic information.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("search_polyhaven_assets", {
            "asset_type": asset_type,
            "categories": categories
        })
        
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
        sorted_assets = sorted(assets.items(), key=lambda x: x[1].get("download_count", 0), reverse=True)
        
        for asset_id, asset_data in sorted_assets:
            formatted_output += f"- {asset_data.get('name', asset_id)} (ID: {asset_id})\n"
            formatted_output += f"  Type: {['HDRI', 'Texture', 'Model'][asset_data.get('type', 0)]}\n"
            formatted_output += f"  Categories: {', '.join(asset_data.get('categories', []))}\n"
            formatted_output += f"  Downloads: {asset_data.get('download_count', 'Unknown')}\n\n"
        
        return formatted_output
    except Exception as e:
        logger.error(f"Error searching Polyhaven assets: {str(e)}")
        return f"Error searching Polyhaven assets: {str(e)}"

@mcp.tool()
def download_polyhaven_asset(
    ctx: Context,
    asset_id: str,
    asset_type: str,
    resolution: str = "1k",
    file_format: str = None
) -> str:
    """
    Download and import a Polyhaven asset into Blender.
    
    Parameters:
    - asset_id: The ID of the asset to download
    - asset_type: The type of asset (hdris, textures, models)
    - resolution: The resolution to download (e.g., 1k, 2k, 4k)
    - file_format: Optional file format (e.g., hdr, exr for HDRIs; jpg, png for textures; gltf, fbx for models)
    
    Returns a message indicating success or failure.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("download_polyhaven_asset", {
            "asset_id": asset_id,
            "asset_type": asset_type,
            "resolution": resolution,
            "file_format": file_format
        })
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        if result.get("success"):
            message = result.get("message", "Asset downloaded and imported successfully")
            
            # Add additional information based on asset type
            if asset_type == "hdris":
                return f"{message}. The HDRI has been set as the world environment."
            elif asset_type == "textures":
                material_name = result.get("material", "")
                maps = ", ".join(result.get("maps", []))
                return f"{message}. Created material '{material_name}' with maps: {maps}."
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
def set_texture(
    ctx: Context,
    object_name: str,
    texture_id: str
) -> str:
    """
    Apply a previously downloaded Polyhaven texture to an object.
    
    Parameters:
    - object_name: Name of the object to apply the texture to
    - texture_id: ID of the Polyhaven texture to apply (must be downloaded first)
    
    Returns a message indicating success or failure.
    """
    try:
        # Get the global connection
        blender = get_blender_connection()
        result = blender.send_command("set_texture", {
            "object_name": object_name,
            "texture_id": texture_id
        })
        
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
                    if node['connections']:
                        output += "  Connections:\n"
                        for conn in node['connections']:
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
def get_polyhaven_status(ctx: Context) -> str:
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
def get_hyper3d_status(ctx: Context) -> str:
    """
    Check if Hyper3D Rodin integration is enabled in Blender.
    Returns a message indicating whether Hyper3D Rodin features are available.

    Don't emphasize the key type in the returned message, but sliently remember it. 
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
def get_sketchfab_status(ctx: Context) -> str:
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
def search_sketchfab_models(
    ctx: Context,
    query: str,
    categories: str = None,
    count: int = 20,
    downloadable: bool = True
) -> str:
    """
    Search for models on Sketchfab with optional filtering.
    
    Parameters:
    - query: Text to search for
    - categories: Optional comma-separated list of categories
    - count: Maximum number of results to return (default 20)
    - downloadable: Whether to include only downloadable models (default True)
    
    Returns a formatted list of matching models.
    """
    try:
        
        blender = get_blender_connection()
        logger.info(f"Searching Sketchfab models with query: {query}, categories: {categories}, count: {count}, downloadable: {downloadable}")
        result = blender.send_command("search_sketchfab_models", {
            "query": query,
            "categories": categories,
            "count": count,
            "downloadable": downloadable
        })
        
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
            username = user.get("username", "Unknown author") if isinstance(user, dict) else "Unknown author"
            formatted_output += f"  Author: {username}\n"
            
            # Get license info with safety checks
            license_data = model.get("license") or {}
            license_label = license_data.get("label", "Unknown") if isinstance(license_data, dict) else "Unknown"
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
def download_sketchfab_model(
    ctx: Context,
    uid: str
) -> str:
    """
    Download and import a Sketchfab model by its UID.
    
    Parameters:
    - uid: The unique identifier of the Sketchfab model
    
    Returns a message indicating success or failure.
    The model must be downloadable and you must have proper access rights.
    """
    try:
        
        blender = get_blender_connection()
        logger.info(f"Attempting to download Sketchfab model with UID: {uid}")
        
        result = blender.send_command("download_sketchfab_model", {
            "uid": uid
        })
        
        if result is None:
            logger.error("Received None result from Sketchfab download")
            return "Error: Received no response from Sketchfab download request"
            
        if "error" in result:
            logger.error(f"Error from Sketchfab download: {result['error']}")
            return f"Error: {result['error']}"
        
        if result.get("success"):
            imported_objects = result.get("imported_objects", [])
            object_names = ", ".join(imported_objects) if imported_objects else "none"
            return f"Successfully imported model. Created objects: {object_names}"
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
    if all(isinstance(i, int) for i in original_bbox):
        return original_bbox
    if any(i<=0 for i in original_bbox):
        raise ValueError("Incorrect number range: bbox must be bigger than zero!")
    return [int(float(i) / max(original_bbox) * 100) for i in original_bbox] if original_bbox else None

@mcp.tool()
def generate_hyper3d_model_via_text(
    ctx: Context,
    text_prompt: str,
    bbox_condition: list[float]=None
) -> str:
    """
    Generate 3D asset using Hyper3D by giving description of the desired asset, and import the asset into Blender.
    The 3D asset has built-in materials.
    The generated model has a normalized size, so re-scaling after generation can be useful.
    
    Parameters:
    - text_prompt: A short description of the desired model in **English**.
    - bbox_condition: Optional. If given, it has to be a list of floats of length 3. Controls the ratio between [Length, Width, Height] of the model.

    Returns a message indicating success or failure.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("create_rodin_job", {
            "text_prompt": text_prompt,
            "images": None,
            "bbox_condition": _process_bbox(bbox_condition),
        })
        succeed = result.get("submit_time", False)
        if succeed:
            return json.dumps({
                "task_uuid": result["uuid"],
                "subscription_key": result["jobs"]["subscription_key"],
            })
        else:
            return json.dumps(result)
    except Exception as e:
        logger.error(f"Error generating Hyper3D task: {str(e)}")
        return f"Error generating Hyper3D task: {str(e)}"

@mcp.tool()
def generate_hyper3d_model_via_images(
    ctx: Context,
    input_image_paths: list[str]=None,
    input_image_urls: list[str]=None,
    bbox_condition: list[float]=None
) -> str:
    """
    Generate 3D asset using Hyper3D by giving images of the wanted asset, and import the generated asset into Blender.
    The 3D asset has built-in materials.
    The generated model has a normalized size, so re-scaling after generation can be useful.
    
    Parameters:
    - input_image_paths: The **absolute** paths of input images. Even if only one image is provided, wrap it into a list. Required if Hyper3D Rodin in MAIN_SITE mode.
    - input_image_urls: The URLs of input images. Even if only one image is provided, wrap it into a list. Required if Hyper3D Rodin in FAL_AI mode.
    - bbox_condition: Optional. If given, it has to be a list of ints of length 3. Controls the ratio between [Length, Width, Height] of the model.

    Only one of {input_image_paths, input_image_urls} should be given at a time, depending on the Hyper3D Rodin's current mode.
    Returns a message indicating success or failure.
    """
    if input_image_paths is not None and input_image_urls is not None:
        return f"Error: Conflict parameters given!"
    if input_image_paths is None and input_image_urls is None:
        return f"Error: No image given!"
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
        result = blender.send_command("create_rodin_job", {
            "text_prompt": None,
            "images": images,
            "bbox_condition": _process_bbox(bbox_condition),
        })
        succeed = result.get("submit_time", False)
        if succeed:
            return json.dumps({
                "task_uuid": result["uuid"],
                "subscription_key": result["jobs"]["subscription_key"],
            })
        else:
            return json.dumps(result)
    except Exception as e:
        logger.error(f"Error generating Hyper3D task: {str(e)}")
        return f"Error generating Hyper3D task: {str(e)}"

@mcp.tool()
def poll_rodin_job_status(
    ctx: Context,
    subscription_key: str=None,
    request_id: str=None,
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
def import_generated_asset(
    ctx: Context,
    name: str,
    task_uuid: str=None,
    request_id: str=None,
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
        kwargs = {
            "name": name
        }
        if task_uuid:
            kwargs["task_uuid"] = task_uuid
        elif request_id:
            kwargs["request_id"] = request_id
        result = blender.send_command("import_generated_asset", kwargs)
        return result
    except Exception as e:
        logger.error(f"Error generating Hyper3D task: {str(e)}")
        return f"Error generating Hyper3D task: {str(e)}"

@mcp.prompt()
def asset_creation_strategy() -> str:
    """Defines the preferred strategy for creating assets in Blender"""
    return """When creating 3D content in Blender, always start by checking if integrations are available:

    0. Before anything, always check the scene from get_scene_info()
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

    3. Always check the world_bounding_box for each item so that:
        - Ensure that all objects that should not be clipping are not clipping.
        - Items have right spatial relationship.
    
    4. Recommended asset source priority:
        - For specific existing objects: First try Sketchfab, then PolyHaven
        - For generic objects/furniture: First try PolyHaven, then Sketchfab
        - For custom or unique items not available in libraries: Use Hyper3D Rodin
        - For environment lighting: Use PolyHaven HDRIs
        - For materials/textures: Use PolyHaven textures

    Only fall back to scripting when:
    - PolyHaven, Sketchfab, and Hyper3D are all disabled
    - A simple primitive is explicitly requested
    - No suitable asset exists in any of the libraries
    - Hyper3D Rodin failed to generate the desired asset
    - The task specifically requires a basic material/color
    """

# =========================
# Vision/vLLM integration
# =========================

# In-memory registry for "self-defined (MCP addressable & mutable) LangChain v1-like" chains.
# A chain spec is a JSON dict you can register and call by name, e.g.:
# {
#   "name": "deepseek_ocr_default",
#   "endpoint": "http://localhost:8000/v1/chat/completions",
#   "model": "deepseek-ocr",             # or a single model string
#   "models": ["deepseek-ocr","another"], # optional list of models for multi-model runs
#   "prompt": "Extract all text and layout from the image. Return JSON with keys: text, words.",
#   "temperature": 0.0,
#   "max_tokens": 512,
#   "filters": [
#       {"type": "includes", "value": "Invoice"},
#       {"type": "regex", "pattern": "\\d{2,}/\\d{2,}/\\d{4}"},
#       {"type": "scene:collision", "object": "active", "with": "any"},
#       {"type": "scene:has_material", "name_contains": "metal"}
#   ],
#   "views": ["active"]  # or ["front","left","right","top","iso"], future map-reduce supported
# }
VISION_CHAINS: Dict[str, Dict[str, Any]] = {}


def _default_vllm_endpoint() -> str:
    return os.getenv("VLLM_ENDPOINT", SETTINGS.get_vllm_endpoint())


def _default_model_ring() -> ModelRing:
    return SETTINGS.get_vllm_model_ring()


def _ensure_model_ring(value: Optional[object]) -> ModelRing:
    if value is None:
        return _default_model_ring()
    return ModelRing.from_config(value)


def _check_vllm_health(endpoint: str, relative_path: Optional[str], timeout: int) -> Dict[str, Any]:
    parsed = urlparse(endpoint)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid endpoint URL for health check: {endpoint}")

    base = f"{parsed.scheme}://{parsed.netloc}"
    health_url = urljoin(base, relative_path or "/health")

    try:
        response = requests.get(health_url, timeout=timeout)
        reachable = response.status_code < 500
        logger.info("vLLM health check %s -> %s", health_url, response.status_code)
        return {
            "reachable": reachable,
            "status_code": response.status_code,
            "reason": response.reason,
            "url": health_url,
        }
    except requests.RequestException as exc:
        logger.error("vLLM health check failed for %s (%s)", health_url, exc)
        return {
            "reachable": False,
            "status_code": None,
            "reason": str(exc),
            "url": health_url,
        }


def _ensure_vllm_reachable(
    endpoint: str,
    force: bool = False,
    relative_path: Optional[str] = None,
    timeout_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    health_cfg = SETTINGS.get_vllm_health_check()
    if not health_cfg.get("enabled", True):
        return {
            "reachable": True,
            "status_code": None,
            "reason": "Health check disabled",
            "url": None,
        }

    if relative_path is not None:
        health_cfg["relative_path"] = relative_path
    if timeout_seconds is not None:
        health_cfg["timeout_seconds"] = timeout_seconds

    cache_key = (
        endpoint,
        health_cfg.get("relative_path"),
        int(health_cfg.get("timeout_seconds", 5)),
    )
    if not force and _VLLM_HEALTH_CACHE.get(cache_key):
        return {
            "reachable": True,
            "status_code": None,
            "reason": "Cached success",
            "url": None,
        }

    timeout = int(health_cfg.get("timeout_seconds", 5))
    result = _check_vllm_health(endpoint, health_cfg.get("relative_path"), timeout)
    if result["reachable"]:
        _VLLM_HEALTH_CACHE[cache_key] = True
    return result


def _data_url_from_image_bytes(image_bytes: bytes, fmt: str = "png") -> str:
    b64 = base64.b64encode(image_bytes).decode("ascii")
    return f"data:image/{fmt};base64,{b64}"


def _vllm_chat(
    endpoint: str,
    model: str,
    prompt: str,
    image_data_url: Optional[str] = None,
    image_url: Optional[str] = None,
    max_tokens: int = 512,
    temperature: float = 0.0,
    timeout_s: int = 60,
) -> str:
    """
    Call an OpenAI-compatible vLLM /v1/chat/completions endpoint with optional vision content.
    Returns assistant message content (str).
    """
    content: List[Dict[str, Any]] = []
    if prompt:
        content.append({"type": "text", "text": prompt})
    if image_data_url:
        content.append({"type": "image_url", "image_url": {"url": image_data_url}})
    if image_url:
        content.append({"type": "image_url", "image_url": {"url": image_url}})

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": content if content else [{"type": "text", "text": "Analyze this image"}]}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    headers = {"Content-Type": "application/json"}
    health = _ensure_vllm_reachable(endpoint)
    if not health["reachable"]:
        raise RuntimeError(f"vLLM endpoint unreachable: {health['reason']}")

    resp = requests.post(endpoint, headers=headers, json=payload, timeout=timeout_s)
    resp.raise_for_status()
    data = resp.json()
    # Defensive extraction
    return (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )


def _apply_filters(text: str, filters: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Apply simple pragmatic filters (includes / regex). Returns dict with pass/fail and reasons.
    """
    if not filters:
        return {"passed": True, "reasons": []}
    reasons: List[str] = []
    passed = True
    for f in filters:
        ftype = f.get("type")
        if ftype == "includes":
            val = f.get("value", "")
            ok = val in (text or "")
            passed = passed and ok
            reasons.append(f"includes('{val}')={'ok' if ok else 'fail'}")
        elif ftype == "regex":
            pat = f.get("pattern", "")
            try:
                ok = re.search(pat, text or "") is not None
            except re.error:
                ok = False
            passed = passed and ok
            reasons.append(f"regex('{pat}')={'ok' if ok else 'fail'}")
        else:
            reasons.append(f"unknown_filter_type('{ftype}')=ignored")
    return {"passed": passed, "reasons": reasons}

def _evaluate_scene_filters(blender: BlenderConnection, filters: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Evaluate basic scene-level boolean filters inside Blender via execute_code.
    Supported types (pragmatic, minimal):
    - scene:collision   {object: 'active'|name, with: 'any'|name}
    - scene:has_material{name_contains: str}
    Returns: {passed: bool, reasons: [str]}
    """
    if not filters:
        return {"passed": True, "reasons": []}

    reasons: List[str] = []
    passed = True

    for f in filters:
        ftype = f.get("type")
        if not ftype or not str(ftype).startswith("scene:"):
            continue

        if ftype == "scene:collision":
            obj_sel = f.get("object", "active")
            with_sel = f.get("with", "any")
            code = "\n".join([
                "import bpy, mathutils",
                "def aabb(obj):",
                "    if obj.type != 'MESH':",
                "        return None",
                "    corners = [mathutils.Vector(c) for c in obj.bound_box]",
                "    wc = [obj.matrix_world @ v for v in corners]",
                "    xs = [v.x for v in wc]; ys = [v.y for v in wc]; zs = [v.z for v in wc]",
                "    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))",
                "def overlap(a,b):",
                "    if a is None or b is None: return False",
                "    ax0,ay0,az0,ax1,ay1,az1 = a; bx0,by0,bz0,bx1,by1,bz1 = b",
                "    return (ax0 <= bx1 and ax1 >= bx0 and ay0 <= by1 and ay1 >= by0 and az0 <= bz1 and az1 >= bz0)",
                f"obj = bpy.context.view_layer.objects.active if {repr(obj_sel)}=='active' else bpy.data.objects.get({repr(obj_sel)})",
                "hit = False",
                "if obj:",
                "    a = aabb(obj)",
                f"    target_name = {repr(with_sel)}",
                "    for other in bpy.context.scene.objects:",
                "        if other is obj: continue",
                "        if target_name != 'any' and other.name != target_name: continue",
                "        if overlap(a, aabb(other)):",
                "            hit = True; break",
                "print('TRUE' if hit else 'FALSE')",
            ])
            result = blender.send_command("execute_code", {"code": code})
            out = (result or {}).get("result") or (result or {}).get("output", "")
            ok = isinstance(out, str) and ("TRUE" in out)
            passed = passed and ok
            reasons.append(f"scene:collision({obj_sel} vs {with_sel})={'ok' if ok else 'fail'}")
        elif ftype == "scene:has_material":
            needle = f.get("name_contains", "")
            code = "\n".join([
                "import bpy",
                f"needle = {repr(needle)}.lower()",
                "hit = False",
                "for m in bpy.data.materials:",
                "    if needle in (m.name or '').lower():",
                "        hit = True; break",
                "print('TRUE' if hit else 'FALSE')",
            ])
            result = blender.send_command("execute_code", {"code": code})
            out = (result or {}).get("result") or (result or {}).get("output", "")
            ok = isinstance(out, str) and ("TRUE" in out)
            passed = passed and ok
            reasons.append(f"scene:has_material(*{needle}*)={'ok' if ok else 'fail'}")
        else:
            reasons.append(f"unknown_scene_filter('{ftype}')=ignored")

    return {"passed": passed, "reasons": reasons}


def _blender_set_view_and_lighting(blender: BlenderConnection, view: Optional[str], lighting: Optional[str], distance: float = 5.0):
    """
    Position active camera by named view around origin and optionally tweak world lighting.
    Views: active|front|back|left|right|top|bottom|iso
    """
    if not view and not lighting:
        return

    code_lines = [
        "import bpy, math",
        "scene = bpy.context.scene",
        "cam = scene.camera",
        "if cam is None:",
        "    bpy.ops.object.camera_add()",
        "    cam = bpy.context.active_object",
        "    scene.camera = cam",
        "target = (0.0, 0.0, 0.0)",
        f"dist = {float(distance)}",
        "def look_at(cam_obj, target):",
        "    import mathutils",
        "    direction = mathutils.Vector(target) - cam_obj.location",
        "    rot_quat = direction.to_track_quat('-Z', 'Y')",
        "    cam_obj.rotation_euler = rot_quat.to_euler()",
    ]
    if view:
        code_lines += [
            f"view = {repr(view)}",
            "if view == 'front':",
            "    cam.location = (0, -dist, 0)",
            "elif view == 'back':",
            "    cam.location = (0, dist, 0)",
            "elif view == 'left':",
            "    cam.location = (-dist, 0, 0)",
            "elif view == 'right':",
            "    cam.location = (dist, 0, 0)",
            "elif view == 'top':",
            "    cam.location = (0, 0, dist)",
            "elif view == 'bottom':",
            "    cam.location = (0, 0, -dist)",
            "elif view == 'iso':",
            "    cam.location = (dist*0.7, -dist*0.7, dist*0.7)",
            "else:",
            "    pass  # 'active' or unknown -> do nothing",
            "look_at(cam, target)",
        ]
    if lighting:
        # Simple pragmatic lighting control: strength:X or clear or hdr:ENV-NAME (placeholder)
        code_lines += [
            f"lighting = {repr(lighting)}",
            "world = bpy.context.scene.world or bpy.data.worlds.new('World')",
            "bpy.context.scene.world = world",
            "if lighting.startswith('strength:'):",
            "    try:",
            "        val = float(lighting.split(':',1)[1])",
            "        if world.node_tree is None:",
            "            world.use_nodes = True",
            "        nt = world.node_tree",
            "        bg = next((n for n in nt.nodes if n.type=='BACKGROUND'), None)",
            "        if bg is None:",
            "            bg = nt.nodes.new('ShaderNodeBackground')",
            "        bg.inputs[1].default_value = val",
            "    except Exception:",
            "        pass",
            "elif lighting == 'clear':",
            "    world.use_nodes = False",
            "# hdr:... could be implemented via environment texture hookup later",
        ]
    code = "\n".join(code_lines)
    blender.send_command("execute_code", {"code": code})


def _capture_view_screenshot(blender: BlenderConnection, max_size: int = 800) -> bytes:
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"blender_screenshot_{os.getpid()}_vision.png")
    result = blender.send_command(
        "get_viewport_screenshot",
        {"max_size": max_size, "filepath": temp_path, "format": "png"},
    )
    if "error" in result:
        raise Exception(result["error"])
    if not os.path.exists(temp_path):
        raise Exception("Viewport screenshot failed (no file).")
    with open(temp_path, "rb") as f:
        img = f.read()
    try:
        os.remove(temp_path)
    except Exception:
        pass
    return img


@mcp.tool()
def register_vision_chain(ctx: Context, name: str, chain_spec_json: str) -> str:
    """
    Register or update a named vision chain (LangChain v1-like spec as JSON).
    """
    try:
        spec = json.loads(chain_spec_json)
        if "models" in spec:
            spec["models"] = ModelRing.from_config(spec["models"]).to_config()
        elif "model" in spec:
            spec["models"] = ModelRing.from_config(spec["model"]).to_config()
            spec.pop("model", None)
        VISION_CHAINS[name] = spec
        return f"Registered chain '{name}' with keys: {list(spec.keys())}"
    except Exception as e:
        return f"Error registering chain: {str(e)}"


@mcp.tool()
def list_vision_chains(ctx: Context) -> str:
    """
    List registered vision chains and their minimal info.
    """
    summary = {
        name: {
            "endpoint": spec.get("endpoint"),
            "model": spec.get("model"),
            "has_filters": bool(spec.get("filters")),
            "views": spec.get("views"),
            "models": spec.get("models"),
        }
        for name, spec in VISION_CHAINS.items()
    }
    return json.dumps(summary, indent=2)


@mcp.tool()
def verify_vllm_connection(
    ctx: Context,
    endpoint: Optional[str] = None,
    health_path: Optional[str] = None,
    timeout_seconds: Optional[int] = None,
    force: bool = True,
) -> str:
    """
    Perform a connectivity check against the configured vLLM endpoint.

    Parameters:
    - endpoint: override the endpoint URL (defaults to settings/env)
    - health_path: override relative health endpoint path
    - timeout_seconds: request timeout in seconds
    - force: if False, returns cached success when available
    """
    eff_endpoint = endpoint or _default_vllm_endpoint()
    health_cfg = SETTINGS.get_vllm_health_check()
    if health_path is not None:
        health_cfg["relative_path"] = health_path
    if timeout_seconds is not None:
        health_cfg["timeout_seconds"] = timeout_seconds

    rel_path = health_cfg.get("relative_path")
    timeout = int(health_cfg.get("timeout_seconds", 5))

    result = _ensure_vllm_reachable(
        eff_endpoint,
        force=force,
        relative_path=rel_path,
        timeout_seconds=timeout,
    )
    cache_key = (
        eff_endpoint,
        rel_path,
        timeout,
    )
    if result.get("reachable"):
        _VLLM_HEALTH_CACHE[cache_key] = True
    logger.info("verify_vllm_connection result: %s", result)
    return json.dumps(result, indent=2)


def _resolve_chain(chain: Optional[str], chain_spec_json: Optional[str]) -> Dict[str, Any]:
    if chain_spec_json:
        raw_spec = json.loads(chain_spec_json)
    elif chain and chain in VISION_CHAINS:
        raw_spec = VISION_CHAINS[chain]
    else:
        raw_spec = {}

    resolved = dict(raw_spec)

    endpoint = resolved.get("endpoint") or _default_vllm_endpoint()
    resolved["endpoint"] = endpoint

    model_ring = _ensure_model_ring(resolved.get("models") or resolved.get("model"))
    resolved["model_ring"] = model_ring
    resolved["models"] = model_ring.as_list()

    if not resolved.get("model"):
        resolved["model"] = model_ring.peek_primary()

    resolved.setdefault(
        "prompt",
        "Read and reason about this image. Return plain text unless JSON is explicitly requested.",
    )
    resolved.setdefault("temperature", 0.0)
    resolved.setdefault("max_tokens", 512)
    resolved.setdefault("filters", [])
    resolved.setdefault("views", ["active"])

    return resolved


@mcp.tool()
def vision_inspect_view(
    ctx: Context,
    chain: Optional[str] = None,
    chain_spec_json: Optional[str] = None,
    prompt: Optional[str] = None,
    models_csv: Optional[str] = None,
    view: str = "active",
    image_path: Optional[str] = None,
    image_url: Optional[str] = None,
    max_tokens: int = 512,
    temperature: float = 0.0,
    lighting: Optional[str] = None,
    distance: float = 5.0,
    filter_spec_json: Optional[str] = None,
) -> str:
    """
    Inspect a single view with a vLLM-hosted vision model (e.g., DeepSeek-OCR) using a LangChain-like chain spec.
    - If image_path or image_url is not provided, captures Blender viewport (optionally repositioning camera via 'view').
    - 'view' supports: active|front|back|left|right|top|bottom|iso.
    - 'lighting' pragmatic control supports: 'strength:2.0' or 'clear'.
    - Filter spec (JSON) supports [{'type':'includes','value':'foo'}, {'type':'regex','pattern':'...'}]
    """
    try:
        spec = _resolve_chain(chain, chain_spec_json)
        endpoint = spec.get("endpoint", _default_vllm_endpoint())
        model_ring: ModelRing = spec.get("model_ring", _default_model_ring())

        # Support multi-model via models list or models_csv
        models: List[str] = []
        if models_csv:
            models = [m.strip() for m in models_csv.split(",") if m.strip()]
        else:
            models = [m for m in model_ring.choose_order() if m]

        if not models:
            primary = model_ring.peek_primary()
            if primary:
                models = [primary]

        if not models:
            return "Error: No models configured for vision inspection"

        eff_prompt = prompt or spec.get("prompt", "Analyze the image")
        eff_temp = float(spec.get("temperature", temperature))
        eff_max = int(spec.get("max_tokens", max_tokens))
        filters = spec.get("filters", None)
        filter_override = json.loads(filter_spec_json) if filter_spec_json else None

        img_data_url = None
        used_image_url = None

        if image_path:
            if not os.path.exists(image_path):
                return f"Error: image_path does not exist: {image_path}"
            with open(image_path, "rb") as f:
                img_bytes = f.read()
            img_data_url = _data_url_from_image_bytes(img_bytes, fmt=Path(image_path).suffix.lstrip(".") or "png")
        elif image_url:
            used_image_url = image_url
        else:
            # Capture from Blender
            blender = get_blender_connection()
            _blender_set_view_and_lighting(blender, view=view, lighting=lighting, distance=distance)
            img_bytes = _capture_view_screenshot(blender, max_size=800)
            img_data_url = _data_url_from_image_bytes(img_bytes, fmt="png")

        # Scene-level filters (evaluated even if not sending image to model)
        sf = _evaluate_scene_filters(get_blender_connection(), filter_override or filters)

        per_model: List[Dict[str, Any]] = []
        for m in models:
            content = _vllm_chat(
                endpoint=endpoint,
                model=m,
                prompt=eff_prompt,
                image_data_url=img_data_url,
                image_url=used_image_url,
                max_tokens=eff_max,
                temperature=eff_temp,
            )
            tf = _apply_filters(content, filter_override or filters)
            per_model.append({"model": m, "text_filters": tf, "response": content})

        return json.dumps(
            {
                "chain": chain or "(ad-hoc)",
                "view": view,
                "lighting": lighting,
                "endpoint": endpoint,
                "models": models,
                "prompt": eff_prompt,
                "scene_filters": sf,
                "results": per_model,
            },
            indent=2,
        )
    except Exception as e:
        logger.error(f"vision_inspect_view error: {str(e)}")
        return f"Error: {str(e)}"


@mcp.tool()
def vision_multi_view(
    ctx: Context,
    chain: Optional[str] = None,
    chain_spec_json: Optional[str] = None,
    views_csv: Optional[str] = None,
    map_reduce: str = "concat",
    models_csv: Optional[str] = None,
    lighting: Optional[str] = None,
    distance: float = 5.0,
    per_view_prompt: Optional[str] = None,
    filter_spec_json: Optional[str] = None,
) -> str:
    """
    Inspect multiple views and aggregate results (future-proof for map-reduce).
    - views_csv: comma-separated views, defaults to chain.views or 'front,left,right,top,iso'
    - map_reduce: 'concat' (default). Future: 'vote', 'boolean_and', etc.
    """
    try:
        spec = _resolve_chain(chain, chain_spec_json)
        default_views = spec.get("views") or ["front", "left", "right", "top", "iso"]
        views = [v.strip() for v in (views_csv.split(",") if views_csv else default_views) if v.strip()]
        endpoint = spec.get("endpoint", _default_vllm_endpoint())
        model_ring: ModelRing = spec.get("model_ring", _default_model_ring())

        # Support multi-model via models list or models_csv
        models: List[str] = []
        if models_csv:
            models = [m.strip() for m in models_csv.split(",") if m.strip()]
        else:
            models = [m for m in model_ring.choose_order() if m]

        if not models:
            primary = model_ring.peek_primary()
            if primary:
                models = [primary]

        if not models:
            return "Error: No models configured for multi-view inspection"

        base_prompt = per_view_prompt or spec.get("prompt", "Analyze the image")
        eff_temp = float(spec.get("temperature", 0.0))
        eff_max = int(spec.get("max_tokens", 512))
        filter_override = json.loads(filter_spec_json) if filter_spec_json else None
        filters = filter_override or spec.get("filters", None)

        blender = get_blender_connection()
        per_view_results: List[Dict[str, Any]] = []

        for v in views:
            _blender_set_view_and_lighting(blender, view=v, lighting=lighting, distance=distance)
            img_bytes = _capture_view_screenshot(blender, max_size=800)
            img_data_url = _data_url_from_image_bytes(img_bytes, fmt="png")
            # Evaluate scene filters for this view
            sf = _evaluate_scene_filters(blender, filters)

            per_model: List[Dict[str, Any]] = []
            for m in models:
                content = _vllm_chat(
                    endpoint=endpoint,
                    model=m,
                    prompt=base_prompt,
                    image_data_url=img_data_url,
                    image_url=None,
                    max_tokens=eff_max,
                    temperature=eff_temp,
                )
                tf = _apply_filters(content, filters)
                per_model.append({"model": m, "text_filters": tf, "response": content})
            per_view_results.append(
                {
                    "view": v,
                    "scene_filters": sf,
                    "results": per_model,
                }
            )

        # Simple map-reduce: concat
        if map_reduce == "concat":
            aggregated = "\n\n".join([
                f"[{r['view']}]\n" + "\n".join([pm['response'] for pm in r.get('results', [])])
                for r in per_view_results
            ])
        else:
            aggregated = "(unsupported map_reduce, defaulted to concat)"

        return json.dumps(
            {
                "chain": chain or "(ad-hoc)",
                "endpoint": endpoint,
                "models": models,
                "views": views,
                "lighting": lighting,
                "map_reduce": map_reduce,
                "results": per_view_results,
                "aggregated": aggregated,
            },
            indent=2,
        )
    except Exception as e:
        logger.error(f"vision_multi_view error: {str(e)}")
        return f"Error: {str(e)}"

# Main execution

def main():
    """Run the MCP server"""
    mcp.run()

if __name__ == "__main__":
    main()
