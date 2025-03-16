# blender_mcp_server.py
from mcp.server.fastmcp import FastMCP, Context, Image
import socket
import json
import asyncio
import logging
from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BlenderMCPServer")

# Import geometry nodes module
from .geometry_nodes import create_geometry_nodes_setup, create_common_geometry_setup, parse_natural_language_to_geometry_nodes

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
    description="Blender integration through the Model Context Protocol",
    lifespan=server_lifespan
)

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
        _blender_connection = BlenderConnection(host="localhost", port=9876)
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
def create_object(
    ctx: Context,
    type: str = "CUBE",
    name: str = None,
    location: List[float] = None,
    rotation: List[float] = None,
    scale: List[float] = None,
    # Torus-specific parameters
    align: str = "WORLD",
    major_segments: int = 48,
    minor_segments: int = 12,
    mode: str = "MAJOR_MINOR",
    major_radius: float = 1.0,
    minor_radius: float = 0.25,
    abso_major_rad: float = 1.25,
    abso_minor_rad: float = 0.75,
    generate_uvs: bool = True
) -> str:
    """
    Create a new object in the Blender scene.
    
    Parameters:
    - type: Object type (CUBE, SPHERE, CYLINDER, PLANE, CONE, TORUS, EMPTY, CAMERA, LIGHT)
    - name: Optional name for the object
    - location: Optional [x, y, z] location coordinates
    - rotation: Optional [x, y, z] rotation in radians
    - scale: Optional [x, y, z] scale factors (not used for TORUS)
    
    Torus-specific parameters (only used when type == "TORUS"):
    - align: How to align the torus ('WORLD', 'VIEW', or 'CURSOR')
    - major_segments: Number of segments for the main ring
    - minor_segments: Number of segments for the cross-section
    - mode: Dimension mode ('MAJOR_MINOR' or 'EXT_INT')
    - major_radius: Radius from the origin to the center of the cross sections
    - minor_radius: Radius of the torus' cross section
    - abso_major_rad: Total exterior radius of the torus
    - abso_minor_rad: Total interior radius of the torus
    - generate_uvs: Whether to generate a default UV map
    
    Returns:
    A message indicating the created object name.
    """
    try:
        # Get the global connection
        blender = get_blender_connection()
        
        # Set default values for missing parameters
        loc = location or [0, 0, 0]
        rot = rotation or [0, 0, 0]
        sc = scale or [1, 1, 1]
        
        params = {
            "type": type,
            "location": loc,
            "rotation": rot,
        }
        
        if name:
            params["name"] = name

        if type == "TORUS":
            # For torus, the scale is not used.
            params.update({
                "align": align,
                "major_segments": major_segments,
                "minor_segments": minor_segments,
                "mode": mode,
                "major_radius": major_radius,
                "minor_radius": minor_radius,
                "abso_major_rad": abso_major_rad,
                "abso_minor_rad": abso_minor_rad,
                "generate_uvs": generate_uvs
            })
            result = blender.send_command("create_object", params)
            return f"Created {type} object: {result['name']}"
        else:
            # For non-torus objects, include scale
            params["scale"] = sc
            result = blender.send_command("create_object", params)
            return f"Created {type} object: {result['name']}"
    except Exception as e:
        logger.error(f"Error creating object: {str(e)}")
        return f"Error creating object: {str(e)}"


@mcp.tool()
def modify_object(
    ctx: Context,
    name: str,
    location: List[float] = None,
    rotation: List[float] = None,
    scale: List[float] = None,
    visible: bool = None
) -> str:
    """
    Modify an existing object in the Blender scene.
    
    Parameters:
    - name: Name of the object to modify
    - location: Optional [x, y, z] location coordinates
    - rotation: Optional [x, y, z] rotation in radians
    - scale: Optional [x, y, z] scale factors
    - visible: Optional boolean to set visibility
    """
    try:
        # Get the global connection
        blender = get_blender_connection()
        
        params = {"name": name}
        
        if location is not None:
            params["location"] = location
        if rotation is not None:
            params["rotation"] = rotation
        if scale is not None:
            params["scale"] = scale
        if visible is not None:
            params["visible"] = visible
            
        result = blender.send_command("modify_object", params)
        return f"Modified object: {result['name']}"
    except Exception as e:
        logger.error(f"Error modifying object: {str(e)}")
        return f"Error modifying object: {str(e)}"

@mcp.tool()
def delete_object(ctx: Context, name: str) -> str:
    """
    Delete an object from the Blender scene.
    
    Parameters:
    - name: Name of the object to delete
    """
    try:
        # Get the global connection
        blender = get_blender_connection()
        
        result = blender.send_command("delete_object", {"name": name})
        return f"Deleted object: {name}"
    except Exception as e:
        logger.error(f"Error deleting object: {str(e)}")
        return f"Error deleting object: {str(e)}"

@mcp.tool()
def set_material(
    ctx: Context,
    object_name: str,
    material_name: str = None,
    color: List[float] = None
) -> str:
    """
    Set or create a material for an object.
    
    Parameters:
    - object_name: Name of the object to apply the material to
    - material_name: Optional name of the material to use or create
    - color: Optional [R, G, B] color values (0.0-1.0)
    """
    try:
        # Get the global connection
        blender = get_blender_connection()
        
        params = {"object_name": object_name}
        
        if material_name:
            params["material_name"] = material_name
        if color:
            params["color"] = color
            
        result = blender.send_command("set_material", params)
        return f"Applied material to {object_name}: {result.get('material_name', 'unknown')}"
    except Exception as e:
        logger.error(f"Error setting material: {str(e)}")
        return f"Error setting material: {str(e)}"

@mcp.tool()
def execute_blender_code(ctx: Context, code: str) -> str:
    """
    Execute arbitrary Python code in Blender.
    
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
        
        return message
    except Exception as e:
        logger.error(f"Error checking PolyHaven status: {str(e)}")
        return f"Error checking PolyHaven status: {str(e)}"

@mcp.prompt()
def asset_creation_strategy() -> str:
    """Defines the preferred strategy for creating assets in Blender"""
    return """When creating 3D content in Blender, always start by checking if PolyHaven is available:

    0. Before anything, always check the scene from get_scene_info()
    1. First use get_polyhaven_status() to verify if PolyHaven integration is enabled.

    2. If PolyHaven is enabled:
       - For objects/models: Use download_polyhaven_asset() with asset_type="models"
       - For materials/textures: Use download_polyhaven_asset() with asset_type="textures"
       - For environment lighting: Use download_polyhaven_asset() with asset_type="hdris"

    3. If PolyHaven is disabled or when falling back to basic tools:
       - create_object() for basic primitives (CUBE, SPHERE, CYLINDER, etc.)
       - set_material() for basic colors and materials

    Only fall back to basic creation tools when:
    - PolyHaven is disabled
    - A simple primitive is explicitly requested
    - No suitable PolyHaven asset exists
    - The task specifically requires a basic material/color
    """

@mcp.tool()
def create_geometry_nodes(ctx: Context, object_name: str, setup_name: str, nodes: List[Dict[str, Any]], links: List[Dict[str, Any]]) -> str:
    """
    创建一个几何节点设置，允许精确控制节点和连接。
    
    Parameters:
    - object_name: 要添加几何节点修改器的对象名称
    - setup_name: 几何节点修改器和节点组的名称
    - nodes: 节点定义列表，每个节点包含id、type、name、location和params
    - links: 节点连接列表，每个连接包含from_node、from_socket、to_node和to_socket
    """
    try:
        # 获取全局连接
        blender = get_blender_connection()
        
        # 生成几何节点设置代码
        code = create_geometry_nodes_setup({
            "object_name": object_name,
            "setup_name": setup_name,
            "nodes": nodes,
            "links": links
        })
        
        # 在Blender中执行代码
        result = blender.send_command("execute_code", {"code": code})
        return f"几何节点设置已创建: {setup_name}"
    except Exception as e:
        logger.error(f"创建几何节点时出错: {str(e)}")
        return f"创建几何节点时出错: {str(e)}"

@mcp.tool()
def create_common_geometry_node_setup(ctx: Context, object_name: str, setup_type: str, **setup_params) -> str:
    """
    创建一个预定义的几何节点设置，如阵列、散点分布、变形或布尔操作。
    
    Parameters:
    - object_name: 要添加几何节点修改器的对象名称
    - setup_type: 设置类型 (array, scatter, deform, boolean)
    - **setup_params: 特定于设置类型的参数
    
    对于array类型:
    - count_x, count_y, count_z: 每个方向的实例数量
    - spacing_x, spacing_y, spacing_z: 每个方向的间距
    
    对于scatter类型:
    - count: 点的数量
    - seed: 随机种子
    - density_max: 最大密度
    
    对于deform类型:
    - deform_type: 变形类型 (noise, wave)
    - strength: 变形强度
    
    对于boolean类型:
    - operation: 布尔操作 (DIFFERENCE, UNION, INTERSECT)
    - primitive_type: 图元类型 (cube, sphere, cylinder)
    - primitive_size: 图元大小
    - primitive_location: 图元位置 [x, y, z]
    """
    try:
        # 获取全局连接
        blender = get_blender_connection()
        
        # 生成几何节点设置代码
        code = create_common_geometry_setup({
            "type": setup_type,
            "object_name": object_name,
            "setup_params": setup_params
        })
        
        # 在Blender中执行代码
        result = blender.send_command("execute_code", {"code": code})
        return f"几何节点设置已创建: {setup_type.capitalize()}"
    except Exception as e:
        logger.error(f"创建几何节点时出错: {str(e)}")
        return f"创建几何节点时出错: {str(e)}"

@mcp.tool()
def create_geometry_nodes_from_description(ctx: Context, object_name: str, description: str) -> str:
    """
    根据自然语言描述创建几何节点设置。
    
    Parameters:
    - object_name: 要添加几何节点修改器的对象名称
    - description: 几何节点设置的自然语言描述
    
    示例描述:
    - "创建一个3x3的网格阵列，间距为2"
    - "在表面上随机分布100个点"
    - "使用噪波变形，强度为0.5"
    - "使用球体进行布尔减法操作，大小为1.5"
    """
    try:
        # 获取全局连接
        blender = get_blender_connection()
        
        # 解析自然语言描述并生成几何节点设置代码
        code = parse_natural_language_to_geometry_nodes({
            "description": description,
            "object_name": object_name
        })
        
        # 在Blender中执行代码
        result = blender.send_command("execute_code", {"code": code})
        return f"根据描述创建了几何节点设置: '{description}'"
    except Exception as e:
        logger.error(f"创建几何节点时出错: {str(e)}")
        return f"创建几何节点时出错: {str(e)}"

@mcp.tool()
def get_geometry_nodes_info(ctx: Context, object_name: str) -> str:
    """
    获取对象上的几何节点修改器信息。
    
    Parameters:
    - object_name: 要获取几何节点信息的对象名称
    """
    try:
        # 获取全局连接
        blender = get_blender_connection()
        
        # 生成代码来获取几何节点信息
        code = f"""
import bpy
import json

obj = bpy.data.objects.get('{object_name}')
if not obj:
    result = {{"error": f"对象 {object_name} 未找到"}}
else:
    modifiers = []
    for mod in obj.modifiers:
        if mod.type == 'NODES':
            mod_info = {{
                "name": mod.name,
                "show_viewport": mod.show_viewport,
                "show_render": mod.show_render
            }}
            
            # 获取节点组信息
            if mod.node_group:
                node_group = mod.node_group
                nodes = []
                
                for node in node_group.nodes:
                    node_info = {{
                        "name": node.name,
                        "type": node.type,
                        "location": [node.location.x, node.location.y]
                    }}
                    nodes.append(node_info)
                
                mod_info["node_group"] = {{
                    "name": node_group.name,
                    "nodes_count": len(nodes),
                    "nodes": nodes
                }}
            
            modifiers.append(mod_info)
    
    if modifiers:
        result = {{"modifiers": modifiers}}
    else:
        result = {{"message": f"对象 {object_name} 没有几何节点修改器"}}

json.dumps(result)
"""
        
        # 在Blender中执行代码
        result = blender.send_command("execute_code", {"code": code})
        
        # 解析结果
        try:
            info = json.loads(result.get("result", "{}"))
            return json.dumps(info, indent=2)
        except:
            return f"获取几何节点信息时出错: 无法解析结果"
    except Exception as e:
        logger.error(f"获取几何节点信息时出错: {str(e)}")
        return f"获取几何节点信息时出错: {str(e)}"

@mcp.tool()
def modify_geometry_nodes(ctx: Context, object_name: str, modifier_name: str, enabled: bool = None) -> str:
    """
    修改几何节点修改器的属性。
    
    Parameters:
    - object_name: 对象名称
    - modifier_name: 修改器名称
    - enabled: 是否启用修改器
    """
    try:
        # 获取全局连接
        blender = get_blender_connection()
        
        # 生成代码来修改几何节点修改器
        code = f"""
import bpy

obj = bpy.data.objects.get('{object_name}')
if not obj:
    result = {{"error": f"对象 {object_name} 未找到"}}
else:
    mod = obj.modifiers.get('{modifier_name}')
    if not mod:
        result = {{"error": f"修改器 {modifier_name} 未找到"}}
    elif mod.type != 'NODES':
        result = {{"error": f"修改器 {modifier_name} 不是几何节点修改器"}}
    else:
        # 修改属性
        changes = []
"""
        
        if enabled is not None:
            code += f"""
        mod.show_viewport = {str(enabled).lower()}
        mod.show_render = {str(enabled).lower()}
        changes.append("enabled = {str(enabled)}")
"""
        
        code += f"""
        if changes:
            result = {{"message": f"修改了几何节点修改器 {modifier_name}: " + ", ".join(changes)}}
        else:
            result = {{"message": f"没有对几何节点修改器 {modifier_name} 进行更改"}}

result
"""
        
        # 在Blender中执行代码
        result = blender.send_command("execute_code", {"code": code})
        
        # 解析结果
        try:
            info = result.get("result", {})
            if isinstance(info, str):
                info = json.loads(info)
            
            if "error" in info:
                return f"修改几何节点时出错: {info['error']}"
            else:
                return info.get("message", "几何节点修改器已更新")
        except:
            return f"修改几何节点时出错: 无法解析结果"
    except Exception as e:
        logger.error(f"修改几何节点时出错: {str(e)}")
        return f"修改几何节点时出错: {str(e)}"

# Main execution

def main():
    """Run the MCP server"""
    mcp.run()

if __name__ == "__main__":
    main()