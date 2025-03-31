import bpy
import mathutils
import json
import threading
import socket
import time
import requests
import tempfile
import traceback
import os
import shutil
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty
from dataclasses import dataclass, field
from typing import List, Dict, Union, Any, Optional, Tuple

bl_info = {
    "name": "Blender MCP",
    "author": "BlenderMCP",
    "version": (0, 2),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > BlenderMCP",
    "description": "Connect Blender to Claude via MCP",
    "category": "Interface",
}

RODIN_FREE_TRIAL_KEY = "k9TcfFoEhNd9cCPP2guHAHHHkctZHIRhZDywZ1euGUXwihbYLpOjQhofby80NJez"

# region GeometryNodeDataClass
IS_BLENDER_4 = bpy.app.version[0] >= 4


@dataclass
class NodeDefinition:
    """Node definition data class"""
    type: str  # Node type name
    location: List[float] = field(default_factory=lambda: [0.0, 0.0])  # Node position [x, y]
    label: str = ""  # Node label
    inputs: Dict[str, Any] = field(default_factory=dict)  # Input values dictionary
    properties: Dict[str, Any] = field(default_factory=dict)  # Node properties parameter dictionary


@dataclass
class NodeLink:
    """Node connection data class"""
    from_node: Union[str, int]  # Source node name or index
    from_socket: Union[str, int]  # Source socket name or index
    to_node: Union[str, int]  # Target node name or index
    to_socket: Union[str, int]  # Target socket name or index


@dataclass
class GeometryNodeNetwork:
    """Geometry node network data class"""
    object_name: str  # Object name
    nodes: List[NodeDefinition] = field(default_factory=list)  # Node list
    links: List[NodeLink] = field(default_factory=list)  # Connection list
    input_sockets: List[Dict[str, str]] = field(default_factory=list)  # Input interface definition
    output_sockets: List[Dict[str, str]] = field(default_factory=list)  # Output interface definition


@dataclass
class SocketInfo:
    """Socket information data class"""
    name: str  # Socket name
    type: str  # Socket type
    description: str  # Socket description
    identifier: str  # Socket identifier
    enabled: bool  # Whether enabled
    hide: bool  # Whether hidden
    default_value: Any = None  # Default value (if any)


@dataclass
class PropertyInfo:
    """Node property information data class"""
    identifier: str  # Property identifier
    name: str  # Property name
    description: str  # Property description
    type: str  # Property type
    default_value: Any = None  # Default value (if any)
    enum_items: List[Dict[str, str]] = field(default_factory=list)  # Enum options (if any)


@dataclass
class NodeInfo:
    """Node information data class"""
    name: str  # Node type name (identifier used to create the node)
    description: str  # Node description
    inputs: List[SocketInfo] = field(default_factory=list)  # Input socket information
    outputs: List[SocketInfo] = field(default_factory=list)  # Output socket information
    properties: List[PropertyInfo] = field(default_factory=list)  # Node property information


# endregion

class BlenderMCPServer:
    def __init__(self, host='localhost', port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None

    def start(self):
        if self.running:
            print("Server is already running")
            return

        self.running = True

        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)

            # Start server thread
            self.server_thread = threading.Thread(target=self._server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()

            print(f"BlenderMCP server started on {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to start server: {str(e)}")
            self.stop()

    def stop(self):
        self.running = False

        # Close socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

        # Wait for thread to finish
        if self.server_thread:
            try:
                if self.server_thread.is_alive():
                    self.server_thread.join(timeout=1.0)
            except:
                pass
            self.server_thread = None

        print("BlenderMCP server stopped")

    def _server_loop(self):
        """Main server loop in a separate thread"""
        print("Server thread started")
        self.socket.settimeout(1.0)  # Timeout to allow for stopping

        while self.running:
            try:
                # Accept new connection
                try:
                    client, address = self.socket.accept()
                    print(f"Connected to client: {address}")

                    # Handle client in a separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except socket.timeout:
                    # Just check running condition
                    continue
                except Exception as e:
                    print(f"Error accepting connection: {str(e)}")
                    time.sleep(0.5)
            except Exception as e:
                print(f"Error in server loop: {str(e)}")
                if not self.running:
                    break
                time.sleep(0.5)

        print("Server thread stopped")

    def _handle_client(self, client):
        """Handle connected client"""
        print("Client handler started")
        client.settimeout(None)  # No timeout
        buffer = b''

        try:
            while self.running:
                # Receive data
                try:
                    data = client.recv(8192)
                    if not data:
                        print("Client disconnected")
                        break

                    buffer += data
                    try:
                        # Try to parse command
                        command = json.loads(buffer.decode('utf-8'))
                        buffer = b''

                        # Execute command in Blender's main thread
                        def execute_wrapper():
                            try:
                                response = self.execute_command(command)
                                response_json = json.dumps(response)
                                try:
                                    client.sendall(response_json.encode('utf-8'))
                                except:
                                    print("Failed to send response - client disconnected")
                            except Exception as e:
                                print(f"Error executing command: {str(e)}")
                                traceback.print_exc()
                                try:
                                    error_response = {
                                        "status": "error",
                                        "message": str(e)
                                    }
                                    client.sendall(json.dumps(error_response).encode('utf-8'))
                                except:
                                    pass
                            return None

                        # Schedule execution in main thread
                        bpy.app.timers.register(execute_wrapper, first_interval=0.0)
                    except json.JSONDecodeError:
                        # Incomplete data, wait for more
                        pass
                except Exception as e:
                    print(f"Error receiving data: {str(e)}")
                    break
        except Exception as e:
            print(f"Error in client handler: {str(e)}")
        finally:
            try:
                client.close()
            except:
                pass
            print("Client handler stopped")

    def execute_command(self, command):
        """Execute a command in the main Blender thread"""
        try:
            cmd_type = command.get("type")
            params = command.get("params", {})

            # Ensure we're in the right context
            if cmd_type in ["create_object", "modify_object", "delete_object"]:
                override = bpy.context.copy()
                override['area'] = [area for area in bpy.context.screen.areas if area.type == 'VIEW_3D'][0]
                with bpy.context.temp_override(**override):
                    return self._execute_command_internal(command)
            else:
                return self._execute_command_internal(command)

        except Exception as e:
            print(f"Error executing command: {str(e)}")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def _execute_command_internal(self, command):
        """Internal command execution with proper context"""
        cmd_type = command.get("type")
        params = command.get("params", {})

        # Add a handler for checking PolyHaven status
        if cmd_type == "get_polyhaven_status":
            return {"status": "success", "result": self.get_polyhaven_status()}

        # Add a handler for checking Hyper3D status
        if cmd_type == "get_hyper3d_status":
            return {"status": "success", "result": self.get_hyper3d_status()}

        # Add a handler for checking GeometryNodes status
        if cmd_type == "get_geometry_nodes_status":
            return {"status": "success", "result": self.get_geometry_nodes_status()}

        # Base handlers that are always available
        handlers = {
            "get_scene_info": self.get_scene_info,
            "create_object": self.create_object,
            "modify_object": self.modify_object,
            "delete_object": self.delete_object,
            "get_object_info": self.get_object_info,
            "execute_code": self.execute_code,
            "set_material": self.set_material,
            "get_polyhaven_status": self.get_polyhaven_status,
            "get_hyper3d_status": self.get_hyper3d_status,
            "get_geometry_nodes_status": self.get_geometry_nodes_status,
        }

        # Add Polyhaven handlers only if enabled
        if bpy.context.scene.blendermcp_use_polyhaven:
            polyhaven_handlers = {
                "get_polyhaven_categories": self.get_polyhaven_categories,
                "search_polyhaven_assets": self.search_polyhaven_assets,
                "download_polyhaven_asset": self.download_polyhaven_asset,
                "set_texture": self.set_texture,
            }
            handlers.update(polyhaven_handlers)

        # Add Hyper3d handlers only if enabled
        if bpy.context.scene.blendermcp_use_hyper3d:
            hyper3d_handlers = {
                "create_rodin_job": self.create_rodin_job,
                "poll_rodin_job_status": self.poll_rodin_job_status,
                "import_generated_asset": self.import_generated_asset,
            }
            handlers.update(hyper3d_handlers)

        # Add geometry nodes handlers only if enabled
        if bpy.context.scene.blendermcp_use_geometry_nodes:
            geometry_nodes_handlers = {
                "get_node_info": self.get_node_info,
                "complete_geometry_node": self.complete_geometry_node,
            }
            handlers.update(geometry_nodes_handlers)

        handler = handlers.get(cmd_type)
        if handler:
            try:
                print(f"Executing handler for {cmd_type}")
                result = handler(**params)
                print(f"Handler execution complete")
                return {"status": "success", "result": result}
            except Exception as e:
                print(f"Error in handler: {str(e)}")
                traceback.print_exc()
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"Unknown command type: {cmd_type}"}

    def get_simple_info(self):
        """Get basic Blender information"""
        return {
            "blender_version": ".".join(str(v) for v in bpy.app.version),
            "scene_name": bpy.context.scene.name,
            "object_count": len(bpy.context.scene.objects)
        }

    def get_scene_info(self):
        """Get information about the current Blender scene"""
        try:
            print("Getting scene info...")
            # Simplify the scene info to reduce data size
            scene_info = {
                "name": bpy.context.scene.name,
                "object_count": len(bpy.context.scene.objects),
                "objects": [],
                "materials_count": len(bpy.data.materials),
            }

            # Collect minimal object information (limit to first 10 objects)
            for i, obj in enumerate(bpy.context.scene.objects):
                if i >= 10:  # Reduced from 20 to 10
                    break

                obj_info = {
                    "name": obj.name,
                    "type": obj.type,
                    # Only include basic location data
                    "location": [round(float(obj.location.x), 2),
                                 round(float(obj.location.y), 2),
                                 round(float(obj.location.z), 2)],
                }
                scene_info["objects"].append(obj_info)

            print(f"Scene info collected: {len(scene_info['objects'])} objects")
            return scene_info
        except Exception as e:
            print(f"Error in get_scene_info: {str(e)}")
            traceback.print_exc()
            return {"error": str(e)}

    @staticmethod
    def _get_aabb(obj):
        """ Returns the world-space axis-aligned bounding box (AABB) of an object. """
        if obj.type != 'MESH':
            raise TypeError("Object must be a mesh")

        # Get the bounding box corners in local space
        local_bbox_corners = [mathutils.Vector(corner) for corner in obj.bound_box]

        # Convert to world coordinates
        world_bbox_corners = [obj.matrix_world @ corner for corner in local_bbox_corners]

        # Compute axis-aligned min/max coordinates
        min_corner = mathutils.Vector(map(min, zip(*world_bbox_corners)))
        max_corner = mathutils.Vector(map(max, zip(*world_bbox_corners)))

        return [
            [*min_corner], [*max_corner]
        ]

    def create_object(self, type="CUBE", name=None, location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1),
                      align="WORLD", major_segments=48, minor_segments=12, mode="MAJOR_MINOR",
                      major_radius=1.0, minor_radius=0.25, abso_major_rad=1.25, abso_minor_rad=0.75, generate_uvs=True):
        """Create a new object in the scene"""
        try:
            # Deselect all objects first
            bpy.ops.object.select_all(action='DESELECT')

            # Create the object based on type
            if type == "CUBE":
                bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation, scale=scale)
            elif type == "SPHERE":
                bpy.ops.mesh.primitive_uv_sphere_add(location=location, rotation=rotation, scale=scale)
            elif type == "CYLINDER":
                bpy.ops.mesh.primitive_cylinder_add(location=location, rotation=rotation, scale=scale)
            elif type == "PLANE":
                bpy.ops.mesh.primitive_plane_add(location=location, rotation=rotation, scale=scale)
            elif type == "CONE":
                bpy.ops.mesh.primitive_cone_add(location=location, rotation=rotation, scale=scale)
            elif type == "TORUS":
                bpy.ops.mesh.primitive_torus_add(
                    align=align,
                    location=location,
                    rotation=rotation,
                    major_segments=major_segments,
                    minor_segments=minor_segments,
                    mode=mode,
                    major_radius=major_radius,
                    minor_radius=minor_radius,
                    abso_major_rad=abso_major_rad,
                    abso_minor_rad=abso_minor_rad,
                    generate_uvs=generate_uvs
                )
            elif type == "EMPTY":
                bpy.ops.object.empty_add(location=location, rotation=rotation, scale=scale)
            elif type == "CAMERA":
                bpy.ops.object.camera_add(location=location, rotation=rotation)
            elif type == "LIGHT":
                bpy.ops.object.light_add(type='POINT', location=location, rotation=rotation, scale=scale)
            else:
                raise ValueError(f"Unsupported object type: {type}")

            # Force update the view layer
            bpy.context.view_layer.update()

            # Get the active object (which should be our newly created object)
            obj = bpy.context.view_layer.objects.active

            # If we don't have an active object, something went wrong
            if obj is None:
                raise RuntimeError("Failed to create object - no active object")

            # Make sure it's selected
            obj.select_set(True)

            # Rename if name is provided
            if name:
                obj.name = name
                if obj.data:
                    obj.data.name = name

            # Patch for PLANE: scale don't work with bpy.ops.mesh.primitive_plane_add()
            if type in {"PLANE"}:
                obj.scale = scale

            # Return the object info
            result = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
                "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            }

            if obj.type == "MESH":
                bounding_box = self._get_aabb(obj)
                result["world_bounding_box"] = bounding_box

            return result
        except Exception as e:
            print(f"Error in create_object: {str(e)}")
            traceback.print_exc()
            return {"error": str(e)}

    def modify_object(self, name, location=None, rotation=None, scale=None, visible=None):
        """Modify an existing object in the scene"""
        # Find the object by name
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")

        # Modify properties as requested
        if location is not None:
            obj.location = location

        if rotation is not None:
            obj.rotation_euler = rotation

        if scale is not None:
            obj.scale = scale

        if visible is not None:
            obj.hide_viewport = not visible
            obj.hide_render = not visible

        result = {
            "name": obj.name,
            "type": obj.type,
            "location": [obj.location.x, obj.location.y, obj.location.z],
            "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
            "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            "visible": obj.visible_get(),
        }

        if obj.type == "MESH":
            bounding_box = self._get_aabb(obj)
            result["world_bounding_box"] = bounding_box

        return result

    def delete_object(self, name):
        """Delete an object from the scene"""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")

        # Store the name to return
        obj_name = obj.name

        # Select and delete the object
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)

        return {"deleted": obj_name}

    def get_object_info(self, name):
        """Get detailed information about a specific object"""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")

        # Basic object info
        obj_info = {
            "name": obj.name,
            "type": obj.type,
            "location": [obj.location.x, obj.location.y, obj.location.z],
            "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
            "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            "visible": obj.visible_get(),
            "materials": [],
        }

        if obj.type == "MESH":
            bounding_box = self._get_aabb(obj)
            obj_info["world_bounding_box"] = bounding_box

        # Add material slots
        for slot in obj.material_slots:
            if slot.material:
                obj_info["materials"].append(slot.material.name)

        # Add mesh data if applicable
        if obj.type == 'MESH' and obj.data:
            mesh = obj.data
            obj_info["mesh"] = {
                "vertices": len(mesh.vertices),
                "edges": len(mesh.edges),
                "polygons": len(mesh.polygons),
            }

        return obj_info

    def execute_code(self, code):
        """Execute arbitrary Blender Python code"""
        # This is powerful but potentially dangerous - use with caution
        try:
            # Create a local namespace for execution
            namespace = {"bpy": bpy}
            exec(code, namespace)
            return {"executed": True}
        except Exception as e:
            raise Exception(f"Code execution error: {str(e)}")

    def set_material(self, object_name, material_name=None, create_if_missing=True, color=None):
        """Set or create a material for an object"""
        try:
            # Get the object
            obj = bpy.data.objects.get(object_name)
            if not obj:
                raise ValueError(f"Object not found: {object_name}")

            # Make sure object can accept materials
            if not hasattr(obj, 'data') or not hasattr(obj.data, 'materials'):
                raise ValueError(f"Object {object_name} cannot accept materials")

            # Create or get material
            if material_name:
                mat = bpy.data.materials.get(material_name)
                if not mat and create_if_missing:
                    mat = bpy.data.materials.new(name=material_name)
                    print(f"Created new material: {material_name}")
            else:
                # Generate unique material name if none provided
                mat_name = f"{object_name}_material"
                mat = bpy.data.materials.get(mat_name)
                if not mat:
                    mat = bpy.data.materials.new(name=mat_name)
                material_name = mat_name
                print(f"Using material: {mat_name}")

            # Set up material nodes if needed
            if mat:
                if not mat.use_nodes:
                    mat.use_nodes = True

                # Get or create Principled BSDF
                principled = mat.node_tree.nodes.get('Principled BSDF')
                if not principled:
                    principled = mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
                    # Get or create Material Output
                    output = mat.node_tree.nodes.get('Material Output')
                    if not output:
                        output = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
                    # Link if not already linked
                    if not principled.outputs[0].links:
                        mat.node_tree.links.new(principled.outputs[0], output.inputs[0])

                # Set color if provided
                if color and len(color) >= 3:
                    principled.inputs['Base Color'].default_value = (
                        color[0],
                        color[1],
                        color[2],
                        1.0 if len(color) < 4 else color[3]
                    )
                    print(f"Set material color to {color}")

            # Assign material to object if not already assigned
            if mat:
                if not obj.data.materials:
                    obj.data.materials.append(mat)
                else:
                    # Only modify first material slot
                    obj.data.materials[0] = mat

                print(f"Assigned material {mat.name} to object {object_name}")

                return {
                    "status": "success",
                    "object": object_name,
                    "material": mat.name,
                    "color": color if color else None
                }
            else:
                raise ValueError(f"Failed to create or find material: {material_name}")

        except Exception as e:
            print(f"Error in set_material: {str(e)}")
            traceback.print_exc()
            return {
                "status": "error",
                "message": str(e),
                "object": object_name,
                "material": material_name if 'material_name' in locals() else None
            }

    def render_scene(self, output_path=None, resolution_x=None, resolution_y=None):
        """Render the current scene"""
        if resolution_x is not None:
            bpy.context.scene.render.resolution_x = resolution_x

        if resolution_y is not None:
            bpy.context.scene.render.resolution_y = resolution_y

        if output_path:
            bpy.context.scene.render.filepath = output_path

        # Render the scene
        bpy.ops.render.render(write_still=bool(output_path))

        return {
            "rendered": True,
            "output_path": output_path if output_path else "[not saved]",
            "resolution": [bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y],
        }

    def get_polyhaven_categories(self, asset_type):
        """Get categories for a specific asset type from Polyhaven"""
        try:
            if asset_type not in ["hdris", "textures", "models", "all"]:
                return {"error": f"Invalid asset type: {asset_type}. Must be one of: hdris, textures, models, all"}

            response = requests.get(f"https://api.polyhaven.com/categories/{asset_type}")
            if response.status_code == 200:
                return {"categories": response.json()}
            else:
                return {"error": f"API request failed with status code {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def search_polyhaven_assets(self, asset_type=None, categories=None):
        """Search for assets from Polyhaven with optional filtering"""
        try:
            url = "https://api.polyhaven.com/assets"
            params = {}

            if asset_type and asset_type != "all":
                if asset_type not in ["hdris", "textures", "models"]:
                    return {"error": f"Invalid asset type: {asset_type}. Must be one of: hdris, textures, models, all"}
                params["type"] = asset_type

            if categories:
                params["categories"] = categories

            response = requests.get(url, params=params)
            if response.status_code == 200:
                # Limit the response size to avoid overwhelming Blender
                assets = response.json()
                # Return only the first 20 assets to keep response size manageable
                limited_assets = {}
                for i, (key, value) in enumerate(assets.items()):
                    if i >= 20:  # Limit to 20 assets
                        break
                    limited_assets[key] = value

                return {"assets": limited_assets, "total_count": len(assets), "returned_count": len(limited_assets)}
            else:
                return {"error": f"API request failed with status code {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def download_polyhaven_asset(self, asset_id, asset_type, resolution="1k", file_format=None):
        try:
            # First get the files information
            files_response = requests.get(f"https://api.polyhaven.com/files/{asset_id}")
            if files_response.status_code != 200:
                return {"error": f"Failed to get asset files: {files_response.status_code}"}

            files_data = files_response.json()

            # Handle different asset types
            if asset_type == "hdris":
                # For HDRIs, download the .hdr or .exr file
                if not file_format:
                    file_format = "hdr"  # Default format for HDRIs

                if "hdri" in files_data and resolution in files_data["hdri"] and file_format in files_data["hdri"][
                    resolution]:
                    file_info = files_data["hdri"][resolution][file_format]
                    file_url = file_info["url"]

                    # For HDRIs, we need to save to a temporary file first
                    # since Blender can't properly load HDR data directly from memory
                    with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as tmp_file:
                        # Download the file
                        response = requests.get(file_url)
                        if response.status_code != 200:
                            return {"error": f"Failed to download HDRI: {response.status_code}"}

                        tmp_file.write(response.content)
                        tmp_path = tmp_file.name

                    try:
                        # Create a new world if none exists
                        if not bpy.data.worlds:
                            bpy.data.worlds.new("World")

                        world = bpy.data.worlds[0]
                        world.use_nodes = True
                        node_tree = world.node_tree

                        # Clear existing nodes
                        for node in node_tree.nodes:
                            node_tree.nodes.remove(node)

                        # Create nodes
                        tex_coord = node_tree.nodes.new(type='ShaderNodeTexCoord')
                        tex_coord.location = (-800, 0)

                        mapping = node_tree.nodes.new(type='ShaderNodeMapping')
                        mapping.location = (-600, 0)

                        # Load the image from the temporary file
                        env_tex = node_tree.nodes.new(type='ShaderNodeTexEnvironment')
                        env_tex.location = (-400, 0)
                        env_tex.image = bpy.data.images.load(tmp_path)

                        # Use a color space that exists in all Blender versions
                        if file_format.lower() == 'exr':
                            # Try to use Linear color space for EXR files
                            try:
                                env_tex.image.colorspace_settings.name = 'Linear'
                            except:
                                # Fallback to Non-Color if Linear isn't available
                                env_tex.image.colorspace_settings.name = 'Non-Color'
                        else:  # hdr
                            # For HDR files, try these options in order
                            for color_space in ['Linear', 'Linear Rec.709', 'Non-Color']:
                                try:
                                    env_tex.image.colorspace_settings.name = color_space
                                    break  # Stop if we successfully set a color space
                                except:
                                    continue

                        background = node_tree.nodes.new(type='ShaderNodeBackground')
                        background.location = (-200, 0)

                        output = node_tree.nodes.new(type='ShaderNodeOutputWorld')
                        output.location = (0, 0)

                        # Connect nodes
                        node_tree.links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
                        node_tree.links.new(mapping.outputs['Vector'], env_tex.inputs['Vector'])
                        node_tree.links.new(env_tex.outputs['Color'], background.inputs['Color'])
                        node_tree.links.new(background.outputs['Background'], output.inputs['Surface'])

                        # Set as active world
                        bpy.context.scene.world = world

                        # Clean up temporary file
                        try:
                            tempfile._cleanup()  # This will clean up all temporary files
                        except:
                            pass

                        return {
                            "success": True,
                            "message": f"HDRI {asset_id} imported successfully",
                            "image_name": env_tex.image.name
                        }
                    except Exception as e:
                        return {"error": f"Failed to set up HDRI in Blender: {str(e)}"}
                else:
                    return {"error": f"Requested resolution or format not available for this HDRI"}

            elif asset_type == "textures":
                if not file_format:
                    file_format = "jpg"  # Default format for textures

                downloaded_maps = {}

                try:
                    for map_type in files_data:
                        if map_type not in ["blend", "gltf"]:  # Skip non-texture files
                            if resolution in files_data[map_type] and file_format in files_data[map_type][resolution]:
                                file_info = files_data[map_type][resolution][file_format]
                                file_url = file_info["url"]

                                # Use NamedTemporaryFile like we do for HDRIs
                                with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as tmp_file:
                                    # Download the file
                                    response = requests.get(file_url)
                                    if response.status_code == 200:
                                        tmp_file.write(response.content)
                                        tmp_path = tmp_file.name

                                        # Load image from temporary file
                                        image = bpy.data.images.load(tmp_path)
                                        image.name = f"{asset_id}_{map_type}.{file_format}"

                                        # Pack the image into .blend file
                                        image.pack()

                                        # Set color space based on map type
                                        if map_type in ['color', 'diffuse', 'albedo']:
                                            try:
                                                image.colorspace_settings.name = 'sRGB'
                                            except:
                                                pass
                                        else:
                                            try:
                                                image.colorspace_settings.name = 'Non-Color'
                                            except:
                                                pass

                                        downloaded_maps[map_type] = image

                                        # Clean up temporary file
                                        try:
                                            os.unlink(tmp_path)
                                        except:
                                            pass

                    if not downloaded_maps:
                        return {"error": f"No texture maps found for the requested resolution and format"}

                    # Create a new material with the downloaded textures
                    mat = bpy.data.materials.new(name=asset_id)
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes
                    links = mat.node_tree.links

                    # Clear default nodes
                    for node in nodes:
                        nodes.remove(node)

                    # Create output node
                    output = nodes.new(type='ShaderNodeOutputMaterial')
                    output.location = (300, 0)

                    # Create principled BSDF node
                    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
                    principled.location = (0, 0)
                    links.new(principled.outputs[0], output.inputs[0])

                    # Add texture nodes based on available maps
                    tex_coord = nodes.new(type='ShaderNodeTexCoord')
                    tex_coord.location = (-800, 0)

                    mapping = nodes.new(type='ShaderNodeMapping')
                    mapping.location = (-600, 0)
                    mapping.vector_type = 'TEXTURE'  # Changed from default 'POINT' to 'TEXTURE'
                    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])

                    # Position offset for texture nodes
                    x_pos = -400
                    y_pos = 300

                    # Connect different texture maps
                    for map_type, image in downloaded_maps.items():
                        tex_node = nodes.new(type='ShaderNodeTexImage')
                        tex_node.location = (x_pos, y_pos)
                        tex_node.image = image

                        # Set color space based on map type
                        if map_type.lower() in ['color', 'diffuse', 'albedo']:
                            try:
                                tex_node.image.colorspace_settings.name = 'sRGB'
                            except:
                                pass  # Use default if sRGB not available
                        else:
                            try:
                                tex_node.image.colorspace_settings.name = 'Non-Color'
                            except:
                                pass  # Use default if Non-Color not available

                        links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])

                        # Connect to appropriate input on Principled BSDF
                        if map_type.lower() in ['color', 'diffuse', 'albedo']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Base Color'])
                        elif map_type.lower() in ['roughness', 'rough']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Roughness'])
                        elif map_type.lower() in ['metallic', 'metalness', 'metal']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Metallic'])
                        elif map_type.lower() in ['normal', 'nor']:
                            # Add normal map node
                            normal_map = nodes.new(type='ShaderNodeNormalMap')
                            normal_map.location = (x_pos + 200, y_pos)
                            links.new(tex_node.outputs['Color'], normal_map.inputs['Color'])
                            links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
                        elif map_type in ['displacement', 'disp', 'height']:
                            # Add displacement node
                            disp_node = nodes.new(type='ShaderNodeDisplacement')
                            disp_node.location = (x_pos + 200, y_pos - 200)
                            links.new(tex_node.outputs['Color'], disp_node.inputs['Height'])
                            links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])

                        y_pos -= 250

                    return {
                        "success": True,
                        "message": f"Texture {asset_id} imported as material",
                        "material": mat.name,
                        "maps": list(downloaded_maps.keys())
                    }

                except Exception as e:
                    return {"error": f"Failed to process textures: {str(e)}"}

            elif asset_type == "models":
                # For models, prefer glTF format if available
                if not file_format:
                    file_format = "gltf"  # Default format for models

                if file_format in files_data and resolution in files_data[file_format]:
                    file_info = files_data[file_format][resolution][file_format]
                    file_url = file_info["url"]

                    # Create a temporary directory to store the model and its dependencies
                    temp_dir = tempfile.mkdtemp()
                    main_file_path = ""

                    try:
                        # Download the main model file
                        main_file_name = file_url.split("/")[-1]
                        main_file_path = os.path.join(temp_dir, main_file_name)

                        response = requests.get(file_url)
                        if response.status_code != 200:
                            return {"error": f"Failed to download model: {response.status_code}"}

                        with open(main_file_path, "wb") as f:
                            f.write(response.content)

                        # Check for included files and download them
                        if "include" in file_info and file_info["include"]:
                            for include_path, include_info in file_info["include"].items():
                                # Get the URL for the included file - this is the fix
                                include_url = include_info["url"]

                                # Create the directory structure for the included file
                                include_file_path = os.path.join(temp_dir, include_path)
                                os.makedirs(os.path.dirname(include_file_path), exist_ok=True)

                                # Download the included file
                                include_response = requests.get(include_url)
                                if include_response.status_code == 200:
                                    with open(include_file_path, "wb") as f:
                                        f.write(include_response.content)
                                else:
                                    print(f"Failed to download included file: {include_path}")

                        # Import the model into Blender
                        if file_format == "gltf" or file_format == "glb":
                            bpy.ops.import_scene.gltf(filepath=main_file_path)
                        elif file_format == "fbx":
                            bpy.ops.import_scene.fbx(filepath=main_file_path)
                        elif file_format == "obj":
                            bpy.ops.import_scene.obj(filepath=main_file_path)
                        elif file_format == "blend":
                            # For blend files, we need to append or link
                            with bpy.data.libraries.load(main_file_path, link=False) as (data_from, data_to):
                                data_to.objects = data_from.objects

                            # Link the objects to the scene
                            for obj in data_to.objects:
                                if obj is not None:
                                    bpy.context.collection.objects.link(obj)
                        else:
                            return {"error": f"Unsupported model format: {file_format}"}

                        # Get the names of imported objects
                        imported_objects = [obj.name for obj in bpy.context.selected_objects]

                        return {
                            "success": True,
                            "message": f"Model {asset_id} imported successfully",
                            "imported_objects": imported_objects
                        }
                    except Exception as e:
                        return {"error": f"Failed to import model: {str(e)}"}
                    finally:
                        # Clean up temporary directory
                        try:
                            shutil.rmtree(temp_dir)
                        except:
                            print(f"Failed to clean up temporary directory: {temp_dir}")
                else:
                    return {"error": f"Requested format or resolution not available for this model"}

            else:
                return {"error": f"Unsupported asset type: {asset_type}"}

        except Exception as e:
            return {"error": f"Failed to download asset: {str(e)}"}

    def set_texture(self, object_name, texture_id):
        """Apply a previously downloaded Polyhaven texture to an object by creating a new material"""
        try:
            # Get the object
            obj = bpy.data.objects.get(object_name)
            if not obj:
                return {"error": f"Object not found: {object_name}"}

            # Make sure object can accept materials
            if not hasattr(obj, 'data') or not hasattr(obj.data, 'materials'):
                return {"error": f"Object {object_name} cannot accept materials"}

            # Find all images related to this texture and ensure they're properly loaded
            texture_images = {}
            for img in bpy.data.images:
                if img.name.startswith(texture_id + "_"):
                    # Extract the map type from the image name
                    map_type = img.name.split('_')[-1].split('.')[0]

                    # Force a reload of the image
                    img.reload()

                    # Ensure proper color space
                    if map_type.lower() in ['color', 'diffuse', 'albedo']:
                        try:
                            img.colorspace_settings.name = 'sRGB'
                        except:
                            pass
                    else:
                        try:
                            img.colorspace_settings.name = 'Non-Color'
                        except:
                            pass

                    # Ensure the image is packed
                    if not img.packed_file:
                        img.pack()

                    texture_images[map_type] = img
                    print(f"Loaded texture map: {map_type} - {img.name}")

                    # Debug info
                    print(f"Image size: {img.size[0]}x{img.size[1]}")
                    print(f"Color space: {img.colorspace_settings.name}")
                    print(f"File format: {img.file_format}")
                    print(f"Is packed: {bool(img.packed_file)}")

            if not texture_images:
                return {"error": f"No texture images found for: {texture_id}. Please download the texture first."}

            # Create a new material
            new_mat_name = f"{texture_id}_material_{object_name}"

            # Remove any existing material with this name to avoid conflicts
            existing_mat = bpy.data.materials.get(new_mat_name)
            if existing_mat:
                bpy.data.materials.remove(existing_mat)

            new_mat = bpy.data.materials.new(name=new_mat_name)
            new_mat.use_nodes = True

            # Set up the material nodes
            nodes = new_mat.node_tree.nodes
            links = new_mat.node_tree.links

            # Clear default nodes
            nodes.clear()

            # Create output node
            output = nodes.new(type='ShaderNodeOutputMaterial')
            output.location = (600, 0)

            # Create principled BSDF node
            principled = nodes.new(type='ShaderNodeBsdfPrincipled')
            principled.location = (300, 0)
            links.new(principled.outputs[0], output.inputs[0])

            # Add texture nodes based on available maps
            tex_coord = nodes.new(type='ShaderNodeTexCoord')
            tex_coord.location = (-800, 0)

            mapping = nodes.new(type='ShaderNodeMapping')
            mapping.location = (-600, 0)
            mapping.vector_type = 'TEXTURE'  # Changed from default 'POINT' to 'TEXTURE'
            links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])

            # Position offset for texture nodes
            x_pos = -400
            y_pos = 300

            # Connect different texture maps
            for map_type, image in texture_images.items():
                tex_node = nodes.new(type='ShaderNodeTexImage')
                tex_node.location = (x_pos, y_pos)
                tex_node.image = image

                # Set color space based on map type
                if map_type.lower() in ['color', 'diffuse', 'albedo']:
                    try:
                        tex_node.image.colorspace_settings.name = 'sRGB'
                    except:
                        pass  # Use default if sRGB not available
                else:
                    try:
                        tex_node.image.colorspace_settings.name = 'Non-Color'
                    except:
                        pass  # Use default if Non-Color not available

                links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])

                # Connect to appropriate input on Principled BSDF
                if map_type.lower() in ['color', 'diffuse', 'albedo']:
                    links.new(tex_node.outputs['Color'], principled.inputs['Base Color'])
                elif map_type.lower() in ['roughness', 'rough']:
                    links.new(tex_node.outputs['Color'], principled.inputs['Roughness'])
                elif map_type.lower() in ['metallic', 'metalness', 'metal']:
                    links.new(tex_node.outputs['Color'], principled.inputs['Metallic'])
                elif map_type.lower() in ['normal', 'nor', 'dx', 'gl']:
                    # Add normal map node
                    normal_map = nodes.new(type='ShaderNodeNormalMap')
                    normal_map.location = (x_pos + 200, y_pos)
                    links.new(tex_node.outputs['Color'], normal_map.inputs['Color'])
                    links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
                elif map_type.lower() in ['displacement', 'disp', 'height']:
                    # Add displacement node
                    disp_node = nodes.new(type='ShaderNodeDisplacement')
                    disp_node.location = (x_pos + 200, y_pos - 200)
                    disp_node.inputs['Scale'].default_value = 0.1  # Reduce displacement strength
                    links.new(tex_node.outputs['Color'], disp_node.inputs['Height'])
                    links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])

                y_pos -= 250

            # Second pass: Connect nodes with proper handling for special cases
            texture_nodes = {}

            # First find all texture nodes and store them by map type
            for node in nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    for map_type, image in texture_images.items():
                        if node.image == image:
                            texture_nodes[map_type] = node
                            break

            # Now connect everything using the nodes instead of images
            # Handle base color (diffuse)
            for map_name in ['color', 'diffuse', 'albedo']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Base Color'])
                    print(f"Connected {map_name} to Base Color")
                    break

            # Handle roughness
            for map_name in ['roughness', 'rough']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Roughness'])
                    print(f"Connected {map_name} to Roughness")
                    break

            # Handle metallic
            for map_name in ['metallic', 'metalness', 'metal']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Metallic'])
                    print(f"Connected {map_name} to Metallic")
                    break

            # Handle normal maps
            for map_name in ['gl', 'dx', 'nor']:
                if map_name in texture_nodes:
                    normal_map_node = nodes.new(type='ShaderNodeNormalMap')
                    normal_map_node.location = (100, 100)
                    links.new(texture_nodes[map_name].outputs['Color'], normal_map_node.inputs['Color'])
                    links.new(normal_map_node.outputs['Normal'], principled.inputs['Normal'])
                    print(f"Connected {map_name} to Normal")
                    break

            # Handle displacement
            for map_name in ['displacement', 'disp', 'height']:
                if map_name in texture_nodes:
                    disp_node = nodes.new(type='ShaderNodeDisplacement')
                    disp_node.location = (300, -200)
                    disp_node.inputs['Scale'].default_value = 0.1  # Reduce displacement strength
                    links.new(texture_nodes[map_name].outputs['Color'], disp_node.inputs['Height'])
                    links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])
                    print(f"Connected {map_name} to Displacement")
                    break

            # Handle ARM texture (Ambient Occlusion, Roughness, Metallic)
            if 'arm' in texture_nodes:
                separate_rgb = nodes.new(type='ShaderNodeSeparateRGB')
                separate_rgb.location = (-200, -100)
                links.new(texture_nodes['arm'].outputs['Color'], separate_rgb.inputs['Image'])

                # Connect Roughness (G) if no dedicated roughness map
                if not any(map_name in texture_nodes for map_name in ['roughness', 'rough']):
                    links.new(separate_rgb.outputs['G'], principled.inputs['Roughness'])
                    print("Connected ARM.G to Roughness")

                # Connect Metallic (B) if no dedicated metallic map
                if not any(map_name in texture_nodes for map_name in ['metallic', 'metalness', 'metal']):
                    links.new(separate_rgb.outputs['B'], principled.inputs['Metallic'])
                    print("Connected ARM.B to Metallic")

                # For AO (R channel), multiply with base color if we have one
                base_color_node = None
                for map_name in ['color', 'diffuse', 'albedo']:
                    if map_name in texture_nodes:
                        base_color_node = texture_nodes[map_name]
                        break

                if base_color_node:
                    mix_node = nodes.new(type='ShaderNodeMixRGB')
                    mix_node.location = (100, 200)
                    mix_node.blend_type = 'MULTIPLY'
                    mix_node.inputs['Fac'].default_value = 0.8  # 80% influence

                    # Disconnect direct connection to base color
                    for link in base_color_node.outputs['Color'].links:
                        if link.to_socket == principled.inputs['Base Color']:
                            links.remove(link)

                    # Connect through the mix node
                    links.new(base_color_node.outputs['Color'], mix_node.inputs[1])
                    links.new(separate_rgb.outputs['R'], mix_node.inputs[2])
                    links.new(mix_node.outputs['Color'], principled.inputs['Base Color'])
                    print("Connected ARM.R to AO mix with Base Color")

            # Handle AO (Ambient Occlusion) if separate
            if 'ao' in texture_nodes:
                base_color_node = None
                for map_name in ['color', 'diffuse', 'albedo']:
                    if map_name in texture_nodes:
                        base_color_node = texture_nodes[map_name]
                        break

                if base_color_node:
                    mix_node = nodes.new(type='ShaderNodeMixRGB')
                    mix_node.location = (100, 200)
                    mix_node.blend_type = 'MULTIPLY'
                    mix_node.inputs['Fac'].default_value = 0.8  # 80% influence

                    # Disconnect direct connection to base color
                    for link in base_color_node.outputs['Color'].links:
                        if link.to_socket == principled.inputs['Base Color']:
                            links.remove(link)

                    # Connect through the mix node
                    links.new(base_color_node.outputs['Color'], mix_node.inputs[1])
                    links.new(texture_nodes['ao'].outputs['Color'], mix_node.inputs[2])
                    links.new(mix_node.outputs['Color'], principled.inputs['Base Color'])
                    print("Connected AO to mix with Base Color")

            # CRITICAL: Make sure to clear all existing materials from the object
            while len(obj.data.materials) > 0:
                obj.data.materials.pop(index=0)

            # Assign the new material to the object
            obj.data.materials.append(new_mat)

            # CRITICAL: Make the object active and select it
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)

            # CRITICAL: Force Blender to update the material
            bpy.context.view_layer.update()

            # Get the list of texture maps
            texture_maps = list(texture_images.keys())

            # Get info about texture nodes for debugging
            material_info = {
                "name": new_mat.name,
                "has_nodes": new_mat.use_nodes,
                "node_count": len(new_mat.node_tree.nodes),
                "texture_nodes": []
            }

            for node in new_mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    connections = []
                    for output in node.outputs:
                        for link in output.links:
                            connections.append(f"{output.name} → {link.to_node.name}.{link.to_socket.name}")

                    material_info["texture_nodes"].append({
                        "name": node.name,
                        "image": node.image.name,
                        "colorspace": node.image.colorspace_settings.name,
                        "connections": connections
                    })

            return {
                "success": True,
                "message": f"Created new material and applied texture {texture_id} to {object_name}",
                "material": new_mat.name,
                "maps": texture_maps,
                "material_info": material_info
            }

        except Exception as e:
            print(f"Error in set_texture: {str(e)}")
            traceback.print_exc()
            return {"error": f"Failed to apply texture: {str(e)}"}

    def get_polyhaven_status(self):
        """Get the current status of PolyHaven integration"""
        enabled = bpy.context.scene.blendermcp_use_polyhaven
        if enabled:
            return {"enabled": True, "message": "PolyHaven integration is enabled and ready to use."}
        else:
            return {
                "enabled": False,
                "message": """PolyHaven integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the BlenderMCP panel in the sidebar (press N if hidden)
                            2. Check the 'Use assets from Poly Haven' checkbox
                            3. Restart the connection to Claude"""
            }

    # region Hyper3D
    def get_hyper3d_status(self):
        """Get the current status of Hyper3D Rodin integration"""
        enabled = bpy.context.scene.blendermcp_use_hyper3d
        if enabled:
            if not bpy.context.scene.blendermcp_hyper3d_api_key:
                return {
                    "enabled": False,
                    "message": """Hyper3D Rodin integration is currently enabled, but API key is not given. To enable it:
                                1. In the 3D Viewport, find the BlenderMCP panel in the sidebar (press N if hidden)
                                2. Keep the 'Use Hyper3D Rodin 3D model generation' checkbox checked
                                3. Choose the right plaform and fill in the API Key
                                4. Restart the connection to Claude"""
                }
            mode = bpy.context.scene.blendermcp_hyper3d_mode
            message = f"Hyper3D Rodin integration is enabled and ready to use. Mode: {mode}. " + \
                      f"Key type: {'private' if bpy.context.scene.blendermcp_hyper3d_api_key != RODIN_FREE_TRIAL_KEY else 'free_trial'}"
            return {
                "enabled": True,
                "message": message
            }
        else:
            return {
                "enabled": False,
                "message": """Hyper3D Rodin integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the BlenderMCP panel in the sidebar (press N if hidden)
                            2. Check the 'Use Hyper3D Rodin 3D model generation' checkbox
                            3. Restart the connection to Claude"""
            }

    def create_rodin_job(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.create_rodin_job_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.create_rodin_job_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def create_rodin_job_main_site(
            self,
            text_prompt: str = None,
            images: list[tuple[str, str]] = None,
            bbox_condition=None
    ):
        try:
            if images is None:
                images = []
            """Call Rodin API, get the job uuid and subscription key"""
            files = [
                *[("images", (f"{i:04d}{img_suffix}", img)) for i, (img_suffix, img) in enumerate(images)],
                ("tier", (None, "Sketch")),
                ("mesh_mode", (None, "Raw")),
            ]
            if text_prompt:
                files.append(("prompt", (None, text_prompt)))
            if bbox_condition:
                files.append(("bbox_condition", (None, json.dumps(bbox_condition))))
            response = requests.post(
                "https://hyperhuman.deemos.com/api/v2/rodin",
                headers={
                    "Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}",
                },
                files=files
            )
            data = response.json()
            return data
        except Exception as e:
            return {"error": str(e)}

    def create_rodin_job_fal_ai(
            self,
            text_prompt: str = None,
            images: list[tuple[str, str]] = None,
            bbox_condition=None
    ):
        try:
            req_data = {
                "tier": "Sketch",
            }
            if images:
                req_data["input_image_urls"] = images
            if text_prompt:
                req_data["prompt"] = text_prompt
            if bbox_condition:
                req_data["bbox_condition"] = bbox_condition
            response = requests.post(
                "https://queue.fal.run/fal-ai/hyper3d/rodin",
                headers={
                    "Authorization": f"Key {bpy.context.scene.blendermcp_hyper3d_api_key}",
                    "Content-Type": "application/json",
                },
                json=req_data
            )
            data = response.json()
            return data
        except Exception as e:
            return {"error": str(e)}

    def poll_rodin_job_status(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.poll_rodin_job_status_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.poll_rodin_job_status_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def poll_rodin_job_status_main_site(self, subscription_key: str):
        """Call the job status API to get the job status"""
        response = requests.post(
            "https://hyperhuman.deemos.com/api/v2/status",
            headers={
                "Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}",
            },
            json={
                "subscription_key": subscription_key,
            },
        )
        data = response.json()
        return {
            "status_list": [i["status"] for i in data["jobs"]]
        }

    def poll_rodin_job_status_fal_ai(self, request_id: str):
        """Call the job status API to get the job status"""
        response = requests.get(
            f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}/status",
            headers={
                "Authorization": f"KEY {bpy.context.scene.blendermcp_hyper3d_api_key}",
            },
        )
        data = response.json()
        return data

    @staticmethod
    def _clean_imported_glb(filepath, mesh_name=None):
        # Get the set of existing objects before import
        existing_objects = set(bpy.data.objects)

        # Import the GLB file
        bpy.ops.import_scene.gltf(filepath=filepath)

        # Ensure the context is updated
        bpy.context.view_layer.update()

        # Get all imported objects
        imported_objects = list(set(bpy.data.objects) - existing_objects)
        # imported_objects = [obj for obj in bpy.context.view_layer.objects if obj.select_get()]

        if not imported_objects:
            print("Error: No objects were imported.")
            return

        # Identify the mesh object
        mesh_obj = None

        if len(imported_objects) == 1 and imported_objects[0].type == 'MESH':
            mesh_obj = imported_objects[0]
            print("Single mesh imported, no cleanup needed.")
        else:
            parent_obj = imported_objects[0]
            if parent_obj.type == 'EMPTY' and len(parent_obj.children) == 1:
                potential_mesh = parent_obj.children[0]
                if potential_mesh.type == 'MESH':
                    print("GLB structure confirmed: Empty node with one mesh child.")

                    # Unparent the mesh from the empty node
                    potential_mesh.parent = None

                    # Remove the empty node
                    bpy.data.objects.remove(parent_obj)
                    print("Removed empty node, keeping only the mesh.")

                    mesh_obj = potential_mesh
                else:
                    print("Error: Child is not a mesh object.")
                    return
            else:
                print("Error: Expected an empty node with one mesh child or a single mesh object.")
                return

        # Rename the mesh if needed
        try:
            if mesh_obj and mesh_obj.name is not None and mesh_name:
                mesh_obj.name = mesh_name
                if mesh_obj.data.name is not None:
                    mesh_obj.data.name = mesh_name
                print(f"Mesh renamed to: {mesh_name}")
        except Exception as e:
            print("Having issue with renaming, give up renaming.")

        return mesh_obj

    def import_generated_asset(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.import_generated_asset_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.import_generated_asset_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def import_generated_asset_main_site(self, task_uuid: str, name: str):
        """Fetch the generated asset, import into blender"""
        response = requests.post(
            "https://hyperhuman.deemos.com/api/v2/download",
            headers={
                "Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}",
            },
            json={
                'task_uuid': task_uuid
            }
        )
        data_ = response.json()
        temp_file = None
        for i in data_["list"]:
            if i["name"].endswith(".glb"):
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    prefix=task_uuid,
                    suffix=".glb",
                )

                try:
                    # Download the content
                    response = requests.get(i["url"], stream=True)
                    response.raise_for_status()  # Raise an exception for HTTP errors

                    # Write the content to the temporary file
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)

                    # Close the file
                    temp_file.close()

                except Exception as e:
                    # Clean up the file if there's an error
                    temp_file.close()
                    os.unlink(temp_file.name)
                    return {"succeed": False, "error": str(e)}

                break

        try:
            obj = self._clean_imported_glb(
                filepath=temp_file.name,
                mesh_name=name
            )
            result = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
                "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            }

            if obj.type == "MESH":
                bounding_box = self._get_aabb(obj)
                result["world_bounding_box"] = bounding_box

            return {
                "succeed": True, **result
            }
        except Exception as e:
            return {"succeed": False, "error": str(e)}

    def import_generated_asset_fal_ai(self, request_id: str, name: str):
        """Fetch the generated asset, import into blender"""
        response = requests.get(
            f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}",
            headers={
                "Authorization": f"Key {bpy.context.scene.blendermcp_hyper3d_api_key}",
            }
        )
        data_ = response.json()
        temp_file = None

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            prefix=request_id,
            suffix=".glb",
        )

        try:
            # Download the content
            response = requests.get(data_["model_mesh"]["url"], stream=True)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Write the content to the temporary file
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)

            # Close the file
            temp_file.close()

        except Exception as e:
            # Clean up the file if there's an error
            temp_file.close()
            os.unlink(temp_file.name)
            return {"succeed": False, "error": str(e)}

        try:
            obj = self._clean_imported_glb(
                filepath=temp_file.name,
                mesh_name=name
            )
            result = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
                "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            }

            if obj.type == "MESH":
                bounding_box = self._get_aabb(obj)
                result["world_bounding_box"] = bounding_box

            return {
                "succeed": True, **result
            }
        except Exception as e:
            return {"succeed": False, "error": str(e)}

    # endregion

    # region GeometryNodeCreator
    def complete_geometry_node(self, object_name, nodes, links, input_sockets=None):
        """Complete geometry node network creation

        Args:
            object_name: Object name
            nodes: List of node definitions
            links: List of node connections
            input_sockets: Node group input interface definitions [{"name": "Name", "type": "Type", "value": "DefaultValue"}]

        Returns:
            dict: Dictionary containing operation status and related information
        """
        try:
            obj = bpy.data.objects.get(object_name)
            if not obj:
                result = self._create_geometry_nodes_object(object_name)
                if "error" in result:
                    return result
                obj = bpy.data.objects.get(object_name)

            # Find geometry nodes modifier
            geometry_modifier = None
            for modifier in obj.modifiers:
                if modifier.type == 'NODES':
                    geometry_modifier = modifier
                    break

            if geometry_modifier and geometry_modifier.node_group:
                old_node_group_name = geometry_modifier.node_group.name
                geometry_modifier.node_group = None

                # Try to delete the old node group
                old_node_group = bpy.data.node_groups.get(old_node_group_name)
                if old_node_group:
                    bpy.data.node_groups.remove(old_node_group)

            # If there's no geometry nodes modifier, create one
            if not geometry_modifier:
                geometry_modifier = obj.modifiers.new(name="GeometryNodes", type='NODES')

            # Create a new node group
            node_group = bpy.data.node_groups.new(name=f"{object_name}_geometry", type='GeometryNodeTree')
            if IS_BLENDER_4:
                node_group.is_modifier = True

            # Set the node group for the modifier
            geometry_modifier.node_group = node_group

            has_input_node = False
            has_output_node = False
            for node_data in nodes:
                node_type = node_data.get("type", "")
                if node_type in ['NodeGroupInput', 'GroupInput']:
                    has_input_node = True
                elif node_type in ['NodeGroupOutput', 'GroupOutput']:
                    has_output_node = True

            self._setup_node_group_interface(node_group, input_sockets)

            # First create all nodes
            created_nodes = []

            input_node = None
            output_node = None

            if not has_input_node:
                input_node = node_group.nodes.new('NodeGroupInput')
                input_node.location = (-300, 0)

            if not has_output_node:
                output_node = node_group.nodes.new('NodeGroupOutput')
                output_node.location = (500, 0)

            for node_data in nodes:
                try:
                    node_type = node_data["type"]

                    node = node_group.nodes.new(node_type)

                    if "location" in node_data:
                        node.location = node_data["location"]

                    if "label" in node_data:
                        node.label = node_data["label"]

                    if "properties" in node_data:
                        for prop_name, prop_value in node_data["properties"].items():
                            if hasattr(node, prop_name):
                                try:
                                    setattr(node, prop_name, prop_value)
                                except Exception as prop_error:
                                    print(f"Error setting property {prop_name}: {prop_error}")

                    if "inputs" in node_data:
                        for input_name, input_value in node_data["inputs"].items():
                            for input in node.inputs:
                                if input.name == input_name and hasattr(input, 'default_value'):
                                    try:
                                        if hasattr(input.default_value, '__len__'):
                                            for i, val in enumerate(input_value):
                                                if i < len(input.default_value):
                                                    input.default_value[i] = val
                                        else:
                                            input.default_value = input_value
                                    except Exception as input_error:
                                        print(f"Error setting input value: {input_error}")

                    node_info = {
                        "name": node.name,
                        "type": node.type,
                        "location": [node.location.x, node.location.y]
                    }

                    created_nodes.append(node_info)
                except Exception as node_error:
                    return {"error": f"Error creating node {node_data['type']}: {str(node_error)}"}

            # Create links
            created_links = []

            for link_data in links:
                try:
                    # Find nodes by index or name
                    from_node_id = link_data["from_node"]
                    to_node_id = link_data["to_node"]

                    from_node = None
                    to_node = None

                    # Special handling for "input" and "output" identifiers
                    if from_node_id == "input":
                        from_node = input_node
                    elif from_node_id == "output":
                        from_node = output_node
                    elif isinstance(from_node_id, int):
                        # Assume integer index points to created node
                        if 0 <= from_node_id < len(created_nodes):
                            from_node = node_group.nodes.get(created_nodes[from_node_id]["name"])
                    else:
                        # Find by name
                        from_node = node_group.nodes.get(from_node_id)

                    if to_node_id == "input":
                        to_node = input_node
                    elif to_node_id == "output":
                        to_node = output_node
                    elif isinstance(to_node_id, int):
                        # Assume integer index points to created node
                        if 0 <= to_node_id < len(created_nodes):
                            to_node = node_group.nodes.get(created_nodes[to_node_id]["name"])
                    else:
                        # Find by name
                        to_node = node_group.nodes.get(to_node_id)

                    if not from_node:
                        return {"error": f"Could not find source node: {from_node_id}"}

                    if not to_node:
                        return {"error": f"Could not find target node: {to_node_id}"}

                    # Find socket
                    from_socket_id = link_data["from_socket"]
                    to_socket_id = link_data["to_socket"]

                    from_socket = None
                    to_socket = None

                    # Find socket by index or name
                    if isinstance(from_socket_id, int):
                        if 0 <= from_socket_id < len(from_node.outputs):
                            from_socket = from_node.outputs[from_socket_id]
                    else:
                        # Search by name
                        for socket in from_node.outputs:
                            if socket.name == from_socket_id:
                                from_socket = socket
                                break

                    if isinstance(to_socket_id, int):
                        if 0 <= to_socket_id < len(to_node.inputs):
                            to_socket = to_node.inputs[to_socket_id]
                    else:
                        # Search by name
                        for socket in to_node.inputs:
                            if socket.name == to_socket_id:
                                to_socket = socket
                                break

                    if not from_socket:
                        return {"error": f"Could not find source socket: {from_socket_id}"}

                    if not to_socket:
                        return {"error": f"Could not find target socket: {to_socket_id}"}

                    # Create connection
                    link = node_group.links.new(from_socket, to_socket)

                    # Record created link
                    link_info = {
                        "from_node": from_node.name,
                        "from_socket": from_socket.name,
                        "to_node": to_node.name,
                        "to_socket": to_socket.name
                    }

                    created_links.append(link_info)
                except Exception as link_error:
                    return {"error": f"Error creating link: {str(link_error)}"}

            # If input sockets are provided and contain values, set modifier parameters
            if input_sockets:
                try:
                    # Find the NodeGroupInput node
                    group_input_node = None
                    for node in node_group.nodes:
                        if node.type == 'GROUP_INPUT':
                            group_input_node = node
                            break

                    # Create one if not found
                    if not group_input_node:
                        group_input_node = node_group.nodes.new('NodeGroupInput')

                    # Get socket information directly from the NodeGroupInput node
                    socket_dict = {}
                    for i, output in enumerate(group_input_node.outputs):
                        socket_dict[output.name] = i

                    # Output debug information
                    print(f"Sockets from NodeGroupInput: {socket_dict}")

                    # Set modifier parameter values
                    for socket in input_sockets:
                        if "value" in socket and socket.get("type") != "NodeSocketGeometry":
                            socket_name = socket.get("name")

                            if socket_name in socket_dict:
                                socket_index = socket_dict[socket_name]
                                socket_key = f"Socket_{socket_index}"

                                try:
                                    if socket_key in geometry_modifier:
                                        geometry_modifier[socket_key] = socket["value"]
                                        print(
                                            f"Successfully set parameter {socket_name} ({socket_key}) = {socket['value']}")
                                    else:
                                        print(f"Warning: {socket_key} does not exist in modifier")
                                except Exception as e:
                                    print(f"Error when setting modifier parameter {socket_key}: {str(e)}")
                            else:
                                print(f"Warning: Could not find socket named '{socket_name}' in NodeGroupInput")

                    # Output all available Socket keys for debugging
                    available_sockets = [key for key in geometry_modifier.keys() if key.startswith("Socket_")]
                    if available_sockets:
                        print(f"Available Socket keys in modifier: {available_sockets}")

                except Exception as e:
                    print(f"Error setting modifier parameters: {str(e)}")
                    # Fall back to compatibility mode
                    try:
                        # Directly iterate through modifier properties and set values
                        for socket in input_sockets:
                            if "value" in socket and socket.get("type") != "NodeSocketGeometry":
                                socket_name = socket.get("name")
                                # Try to find matching socket keys
                                for key in geometry_modifier.keys():
                                    if key.startswith("Socket_"):
                                        # Try to set directly
                                        try:
                                            geometry_modifier[key] = socket["value"]
                                            print(f"Directly set {key} = {socket['value']}")
                                            break
                                        except:
                                            pass
                    except:
                        pass

            return {
                "status": "success",
                "object_name": object_name,
                "modifier_name": geometry_modifier.name,
                "node_group_name": node_group.name,
                "nodes": created_nodes,
                "links": created_links
            }
        except Exception as e:
            return {"error": f"Error completing geometry node network: {str(e)}"}

    def _create_geometry_nodes_object(self, object_name):
        """Create a base object and add a geometry nodes modifier

        Args:
            object_name: Object name

        Returns:
            dict: Dictionary containing operation status and related information
        """
        try:
            # Create base object
            bpy.ops.mesh.primitive_cube_add()
            obj = bpy.context.active_object
            obj.name = object_name

            # Create node group
            node_group = bpy.data.node_groups.new(name=f"{object_name}_geometry", type='GeometryNodeTree')
            if IS_BLENDER_4:
                node_group.is_modifier = True

            # Create interface
            if IS_BLENDER_4:
                interface = node_group.interface
                interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
                interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
            else:
                node_group.inputs.new("NodeSocketGeometry", "Geometry")
                node_group.outputs.new("NodeSocketGeometry", "Geometry")

            # Add input and output nodes
            group_in = node_group.nodes.new('NodeGroupInput')
            group_in.location = (-200, 0)

            group_out = node_group.nodes.new('NodeGroupOutput')
            group_out.location = (200, 0)

            # Connect geometry flow
            node_group.links.new(group_in.outputs["Geometry"], group_out.inputs["Geometry"])

            # Create geometry nodes modifier and immediately set the node group
            mod = obj.modifiers.new(name="GeometryNodes", type='NODES')

            # Ensure the node group exists
            if node_group.name not in bpy.data.node_groups:
                return {"error": "Failed to create node group"}

            # Set the modifier's node group
            mod.node_group = node_group

            # Verify the setup was successful
            if not mod.node_group:
                return {"error": "Failed to set modifier node group"}

            return {
                "status": "success",
                "object_name": obj.name,
                "modifier_name": mod.name,
                "node_group_name": node_group.name
            }
        except Exception as e:
            return {"error": f"Error creating geometry nodes object: {str(e)}"}

    def _setup_node_group_interface(self, node_group, input_sockets=None, output_sockets=None):
        """Set up input and output interfaces for the node group

        Args:
            node_group: Node group
            input_sockets: Input interface list [{"name": "Name", "type": "Type"}]
            output_sockets: Output interface list [{"name": "Name", "type": "Type"}]
        """
        # Default interfaces
        default_input_sockets = [{"name": "Geometry", "type": "NodeSocketGeometry"}]
        default_output_sockets = [{"name": "Geometry", "type": "NodeSocketGeometry"}]

        # Use provided interfaces or default values
        input_sockets = input_sockets or default_input_sockets
        output_sockets = output_sockets or default_output_sockets

        # Clear existing interfaces
        if IS_BLENDER_4:
            # Blender 4.0+
            interface = node_group.interface

            # Clear existing interfaces
            sockets_to_remove = []
            for socket in interface.items_tree:
                sockets_to_remove.append(socket)

            for socket in sockets_to_remove:
                interface.remove(socket)

            # Create new interfaces
            for socket in input_sockets:
                interface.new_socket(
                    name=socket["name"],
                    in_out='INPUT',
                    socket_type=socket["type"]
                )

            for socket in output_sockets:
                interface.new_socket(
                    name=socket["name"],
                    in_out='OUTPUT',
                    socket_type=socket["type"]
                )
        else:
            # Blender 3.x
            # Clear existing inputs
            for i in range(len(node_group.inputs) - 1, -1, -1):
                node_group.inputs.remove(node_group.inputs[i])

            # Clear existing outputs
            for i in range(len(node_group.outputs) - 1, -1, -1):
                node_group.outputs.remove(node_group.outputs[i])

            # Create new interfaces
            for socket in input_sockets:
                node_group.inputs.new(socket["type"], socket["name"])

            for socket in output_sockets:
                node_group.outputs.new(socket["type"], socket["name"])

    # endregion

    # region GeometryNodeInfo
    def get_node_info(self, output_format='text', include_details=False, node_type_name=None):
        """Get node type information

        Args:
            output_format: Output format ('text', 'json')
            include_details: Whether to include detailed information (properties and sockets)
            node_type_name: Node type name, can be a single string, comma-separated multiple node names, or a list of strings

        Returns:
            str: Returns node information in different formats based on output_format:
            - 'text': String, each line as "TypeName:Description" and detailed information (if include_details is True)
            - 'json': JSON formatted string
        """
        # Handle include_details type conversion
        try:
            if isinstance(include_details, str):
                include_details_lower = include_details.lower()
                include_details = include_details_lower == 'true' or include_details_lower == 'yes' or include_details_lower == '1'

            # Handle node_type_name parameter, ensuring it's a list
            node_type_names = []
            if node_type_name is not None:
                # If it's a string, check if it's a comma-separated list
                if isinstance(node_type_name, str):
                    # Split by comma and strip whitespace
                    node_type_names = [name.strip() for name in node_type_name.split(',') if name.strip()]
                # If it's already a list, use it directly
                elif isinstance(node_type_name, list):
                    node_type_names = node_type_name
                else:
                    raise ValueError(f"node_type_name must be a string or a list, received: {type(node_type_name)}")

                # Ensure all elements in the list are strings
                if not all(isinstance(item, str) for item in node_type_names):
                    raise ValueError(f"All elements in node_type_name list must be strings")

                print(f"Processing node type names: {node_type_names} (from: {node_type_name})")

            # Handle output_format parameter
            if output_format not in ('text', 'json'):
                raise ValueError(f"Unsupported output format: {output_format}, please use 'text' or 'json'")

            self._register_node_info_cache()

            # Get all node information
            node_infos = self._get_nodes_from_cache_or_collect()

            # If specific node type names are specified, return only those nodes' information
            if node_type_names:
                # Find target nodes
                target_nodes = [node for node in node_infos if node.name in node_type_names]

                # If no target nodes are found
                if not target_nodes:
                    if len(node_type_names) == 1:
                        return f"Node {node_type_names[0]} does not exist or cannot be created"
                    else:
                        return f"Specified nodes do not exist or cannot be created: {', '.join(node_type_names)}"

                # Return node information based on output_format
                if output_format == 'text':
                    if len(target_nodes) == 1:
                        return self._format_single_node_text(target_nodes[0], include_details)
                    else:
                        if include_details:
                            return "\n\n".join(self._format_node_text(node, True) for node in target_nodes)
                        else:
                            return '\n'.join(self._format_node_text(node, False) for node in target_nodes)
                else:  # 'json'
                    node_dicts = [self._node_to_dict(node, include_details) for node in target_nodes]
                    if len(node_dicts) == 1:
                        return json.dumps(node_dicts[0], ensure_ascii=False, indent=2, default=str)
                    else:
                        return json.dumps(node_dicts, ensure_ascii=False, indent=2, default=str)

            # Return information about all nodes based on output_format
            if output_format == 'text':
                if include_details:
                    return "\n\n".join(self._format_node_text(node, True) for node in node_infos)
                else:
                    return '\n'.join(self._format_node_text(node, False) for node in node_infos)

            else:  # 'json'
                node_dicts = [self._node_to_dict(node, include_details) for node in node_infos]
                return json.dumps(node_dicts, ensure_ascii=False, indent=2, default=str)

        except Exception as e:
            print(f"Error getting node information: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Error getting node information: {str(e)}"

    def _register_node_info_cache(self):
        """Register custom properties"""
        if not hasattr(bpy.types.WindowManager, "node_info_cache"):
            bpy.types.WindowManager.node_info_cache = bpy.props.StringProperty(
                name="Node Info Cache",
                description="Cache for node information",
                default=""
            )

    def _collect_socket_info(self, node, is_input: bool = True) -> List[SocketInfo]:
        """Collect node socket information

        Args:
            node: Node object
            is_input: Whether the socket is an input socket

        Returns:
            List[SocketInfo]: List of socket information
        """
        sockets = []
        socket_list = node.inputs if is_input else node.outputs

        for socket in socket_list:
            # Default value handling
            default_value = None
            if hasattr(socket, 'default_value'):
                try:
                    # Handling different types of default values
                    if hasattr(socket.default_value, '__len__'):
                        # Vectors, colors, etc.
                        default_value = list(socket.default_value)
                    else:
                        # Scalar values
                        default_value = socket.default_value
                except:
                    default_value = None

            # Create SocketInfo object
            socket_info = SocketInfo(
                name=socket.name,
                type=socket.type,
                description=socket.description,
                identifier='',
                enabled=socket.enabled,
                hide=socket.hide,
                default_value=default_value
            )

            sockets.append(socket_info)

        return sockets

    def _collect_property_info(self, node_type) -> List[PropertyInfo]:
        """Collect node property information

        Args:
            node_type: Node type

        Returns:
            List[PropertyInfo]: List of property information
        """
        properties = []

        # Get parent class identifier, to exclude inherited properties
        parent_props = [prop.identifier for base in node_type.__bases__
                        for prop in base.bl_rna.properties]

        # Iterate over node type's properties
        for prop in node_type.bl_rna.properties:
            # Skip inherited properties and built-in basic properties
            if (prop.identifier in parent_props or
                    prop.identifier in ['rna_type', 'name', 'location', 'width',
                                        'width_hidden', 'height', 'dimensions',
                                        'inputs', 'outputs', 'internal_links']):
                continue

            # Get default value (based on property type)
            default_value = None
            enum_items = []

            # Handling different types of properties
            if prop.type == 'ENUM':
                # Handling enum types
                enum_items = [{'identifier': item.identifier,
                               'name': item.name,
                               'description': item.description}
                              for item in prop.enum_items]
            elif hasattr(prop, 'default'):
                default_value = prop.default

            # Create PropertyInfo object
            prop_info = PropertyInfo(
                identifier=prop.identifier,
                name=prop.name,
                description=prop.description,
                type=prop.type,
                default_value=default_value,
                enum_items=enum_items
            )

            properties.append(prop_info)

        return properties

    def _verify_node_identifier(self, node_type_name: str) -> Tuple[
        bool, List[SocketInfo], List[SocketInfo], List[PropertyInfo]]:
        """Verify node identifier is valid for creating a node and get node information

        Args:
            node_type_name: Node type name

        Returns:
            Tuple: (is_usable, input_sockets, output_sockets, property_info)
        """
        # Create a temporary geometry node tree for testing
        temp_tree = bpy.data.node_groups.new('TempNodeTree', 'GeometryNodeTree')
        inputs = []
        outputs = []
        properties = []

        try:
            # Try to create a node
            node = temp_tree.nodes.new(node_type_name)
            node_type = getattr(bpy.types, node_type_name)

            # Get socket information
            inputs = self._collect_socket_info(node, is_input=True)
            outputs = self._collect_socket_info(node, is_input=False)

            # Get property information
            properties = self._collect_property_info(node_type)

            return True, inputs, outputs, properties
        except Exception as e:
            return False, inputs, outputs, properties
        finally:
            # Clean up
            bpy.data.node_groups.remove(temp_tree)

    def _collect_node_info(self) -> List[NodeInfo]:
        """Collect node information (internal function)"""
        # Exclude list
        denylist = {'filter'}
        class_denylist = {'CompositorNodeMath', 'TextureNodeMath'}

        # Collect node information
        node_infos = []

        for node_type_name in dir(bpy.types):
            # Get type object
            node_type = getattr(bpy.types, node_type_name)

            # Check if it's a node type
            if (isinstance(node_type, type) and
                    issubclass(node_type, bpy.types.Node) and
                    node_type.is_registered_node_type() and
                    node_type.bl_rna.name.lower() not in denylist and
                    node_type.__name__ not in class_denylist):

                # Verify if the node can be created in the geometry node tree and get information
                valid, inputs, outputs, properties = self._verify_node_identifier(node_type.__name__)
                if not valid:
                    continue

                # Get description
                description = node_type.bl_rna.description

                # Get identifier for creating the node
                node_identifier = node_type.__name__

                # Create NodeInfo object
                node_info = NodeInfo(
                    name=node_identifier,
                    description=description or "No description available",
                    inputs=inputs,
                    outputs=outputs,
                    properties=properties
                )

                node_infos.append(node_info)

        # Sort by name
        node_infos.sort(key=lambda x: x.name)
        return node_infos

    def _get_nodes_from_cache_or_collect(self) -> List[NodeInfo]:
        """Get node information from cache or collect new ones"""
        wm = bpy.context.window_manager

        # Try to get data from cache
        if wm.node_info_cache:
            print(f"Using cache..")
            try:
                # Deserialize from cache
                cache_data = json.loads(wm.node_info_cache)
                node_infos = []

                # Rebuild NodeInfo objects
                for item in cache_data:
                    # Rebuild input sockets
                    inputs = [SocketInfo(**s) for s in item.get('inputs', [])]
                    # Rebuild output sockets
                    outputs = [SocketInfo(**s) for s in item.get('outputs', [])]
                    # Rebuild property information
                    properties = []
                    for p in item.get('properties', []):
                        prop = PropertyInfo(
                            identifier=p['identifier'],
                            name=p['name'],
                            description=p['description'],
                            type=p['type'],
                            default_value=p.get('default_value'),
                            enum_items=p.get('enum_items', [])
                        )
                        properties.append(prop)

                    # Create NodeInfo object
                    node_infos.append(NodeInfo(
                        name=item['name'],
                        description=item['description'],
                        inputs=inputs,
                        outputs=outputs,
                        properties=properties
                    ))
                return node_infos
            except Exception as e:
                print(f"Error parsing cache: {e}")

        # Collect node information
        print(f"Collecting node information..")
        node_infos = self._collect_node_info()

        # Update cache
        self._update_cache(node_infos)
        return node_infos

    def _format_socket_info_text(self, socket: SocketInfo, index: int, indent: str = "  ") -> List[str]:
        """Format socket information as a list of text lines"""
        lines = [f"{indent}{index}. {socket.name} ({socket.type})"]
        if socket.description:
            lines.append(f"{indent}   Description: {socket.description}")
        if socket.default_value is not None:
            lines.append(f"{indent}   Default value: {socket.default_value}")
        return lines

    def _format_property_info_text(self, prop: PropertyInfo, index: int, indent: str = "  ") -> List[str]:
        """Format property information as a list of text lines"""
        lines = [f"{indent}{index}. {prop.name} ({prop.type})"]
        if prop.description:
            lines.append(f"{indent}   Description: {prop.description}")

        if prop.default_value is not None:
            lines.append(f"{indent}   Default value: {prop.default_value}")

        if prop.enum_items:
            lines.append(f"{indent}   Options:")
            for i, item in enumerate(prop.enum_items):
                lines.append(f"{indent}    {i}. {item['name']} ('{item['identifier']}')")
                if item['description']:
                    lines.append(f"{indent}       Description: {item['description']}")

        return lines

    def _format_node_text(self, node: NodeInfo, include_details: bool = False) -> str:
        """Format node information as text"""
        if not include_details:
            return f"{node.name}:{node.description}"

        lines = [f"{node.name}:{node.description}"]

        # Add property information
        if node.properties:
            lines.append("   Properties:")
            for i, prop in enumerate(node.properties):
                lines.extend(self._format_property_info_text(prop, i, "    "))

        # Add input socket information
        if node.inputs:
            lines.append("   Input sockets:")
            for i, socket in enumerate(node.inputs):
                lines.extend(self._format_socket_info_text(socket, i, "    "))

        # Add output socket information
        if node.outputs:
            lines.append("   Output sockets:")
            for i, socket in enumerate(node.outputs):
                lines.extend(self._format_socket_info_text(socket, i, "    "))

        return "\n".join(lines)

    def _format_single_node_text(self, node: NodeInfo, include_details: bool = False) -> str:
        """Format single node information as detailed text"""
        lines = [f"Node: {node.name}", f"Description: {node.description}"]

        if include_details:
            # Add property information
            if node.properties:
                lines.append("\nProperties:")
                for i, prop in enumerate(node.properties):
                    lines.append(f"  {i}. {prop.name} ({prop.type})")
                    if prop.description:
                        lines.append(f"      Description: {prop.description}")
                    if prop.default_value is not None:
                        lines.append(f"      Default value: {prop.default_value}")
                    if prop.enum_items:
                        lines.append(f"      Options:")
                        for j, item in enumerate(prop.enum_items):
                            lines.append(f"       {j}. {item['name']} ('{item['identifier']}')")
                            if item['description']:
                                lines.append(f"           Description: {item['description']}")

            # Add input socket information
            if node.inputs:
                lines.append("\nInput sockets:")
                for i, socket in enumerate(node.inputs):
                    lines.append(f"  {i}. {socket.name} ({socket.type})")
                    if socket.description:
                        lines.append(f"      Description: {socket.description}")
                    if socket.default_value is not None:
                        lines.append(f"      Default value: {socket.default_value}")

            # Add output socket information
            if node.outputs:
                lines.append("\nOutput sockets:")
                for i, socket in enumerate(node.outputs):
                    lines.append(f"  {i}. {socket.name} ({socket.type})")
                    if socket.description:
                        lines.append(f"      Description: {socket.description}")

        return '\n'.join(lines)

    def _node_to_dict(self, node: NodeInfo, include_details: bool = False) -> dict:
        """Convert node information to dictionary"""
        if include_details:
            return {
                'name': node.name,
                'description': node.description,
                'properties': [{
                    'identifier': p.identifier,
                    'name': p.name,
                    'description': p.description,
                    'type': p.type,
                    'default_value': p.default_value,
                    'enum_items': p.enum_items
                } for p in node.properties],
                'inputs': [socket.__dict__ for socket in node.inputs],
                'outputs': [socket.__dict__ for socket in node.outputs]
            }
        else:
            return {
                'name': node.name,
                'description': node.description
            }

    def _update_cache(self, node_infos: List[NodeInfo]):
        """Update node information cache

        Args:
            node_infos: List of NodeInfo objects
        """
        wm = bpy.context.window_manager

        # Convert NodeInfo objects to serializable dictionary
        serializable_data = []
        for info in node_infos:
            node_dict = {
                'name': info.name,
                'description': info.description,
                'properties': [{
                    'identifier': p.identifier,
                    'name': p.name,
                    'description': p.description,
                    'type': p.type,
                    'default_value': p.default_value,
                    'enum_items': p.enum_items
                } for p in info.properties],
                'inputs': [socket.__dict__ for socket in info.inputs],
                'outputs': [socket.__dict__ for socket in info.outputs]
            }
            serializable_data.append(node_dict)

        # Update cache
        try:
            wm.node_info_cache = json.dumps(serializable_data, default=str)
        except Exception as e:
            print(f"Error updating cache: {e}")

    # endregion

    def get_geometry_nodes_status(self):
        """Get the status of the geometry nodes feature in Blender.

        Returns:
            dict: A dictionary containing information about the geometry nodes feature status.
        """
        try:
            # Get the geometry nodes setting from Blender preferences
            enabled = bpy.context.scene.blendermcp_use_geometry_nodes
            if enabled:
                return {
                    "status": "success",
                    "enabled": True,
                    "message": "Geometry nodes feature is enabled."
                }
            else:
                return {
                    "status": "warning",
                    "enabled": False,
                    "message": "Geometry nodes feature is disabled. Enable it in the BlenderMCP panel to use geometry node commands."
                }
        except Exception as e:
            # Handle errors when checking status
            return {
                "status": "error",
                "enabled": False,
                "message": f"Error checking geometry nodes status: {str(e)}"
            }


# Blender UI Panel
class BLENDERMCP_PT_Panel(bpy.types.Panel):
    bl_label = "Blender MCP"
    bl_idname = "BLENDERMCP_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BlenderMCP'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "blendermcp_port")
        layout.prop(scene, "blendermcp_use_polyhaven", text="Use assets from Poly Haven")

        layout.prop(scene, "blendermcp_use_hyper3d", text="Use Hyper3D Rodin 3D model generation")
        if scene.blendermcp_use_hyper3d:
            layout.prop(scene, "blendermcp_hyper3d_mode", text="Rodin Mode")
            layout.prop(scene, "blendermcp_hyper3d_api_key", text="API Key")
            layout.operator("blendermcp.set_hyper3d_free_trial_api_key", text="Set Free Trial API Key")

        layout.prop(scene, "blendermcp_use_geometry_nodes", text="Use Geometry Nodes for procedural modeling")

        if not scene.blendermcp_server_running:
            layout.operator("blendermcp.start_server", text="Start MCP Server")
        else:
            layout.operator("blendermcp.stop_server", text="Stop MCP Server")
            layout.label(text=f"Running on port {scene.blendermcp_port}")


# Operator to set Hyper3D API Key
class BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey(bpy.types.Operator):
    bl_idname = "blendermcp.set_hyper3d_free_trial_api_key"
    bl_label = "Set Free Trial API Key"

    def execute(self, context):
        context.scene.blendermcp_hyper3d_api_key = RODIN_FREE_TRIAL_KEY
        context.scene.blendermcp_hyper3d_mode = 'MAIN_SITE'
        self.report({'INFO'}, "API Key set successfully!")
        return {'FINISHED'}


# Operator to start the server
class BLENDERMCP_OT_StartServer(bpy.types.Operator):
    bl_idname = "blendermcp.start_server"
    bl_label = "Connect to Claude"
    bl_description = "Start the BlenderMCP server to connect with Claude"

    def execute(self, context):
        scene = context.scene

        # Create a new server instance
        if not hasattr(bpy.types, "blendermcp_server") or not bpy.types.blendermcp_server:
            bpy.types.blendermcp_server = BlenderMCPServer(port=scene.blendermcp_port)

        # Start the server
        bpy.types.blendermcp_server.start()
        scene.blendermcp_server_running = True

        return {'FINISHED'}


# Operator to stop the server
class BLENDERMCP_OT_StopServer(bpy.types.Operator):
    bl_idname = "blendermcp.stop_server"
    bl_label = "Stop the connection to Claude"
    bl_description = "Stop the connection to Claude"

    def execute(self, context):
        scene = context.scene

        # Stop the server if it exists
        if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server:
            bpy.types.blendermcp_server.stop()
            del bpy.types.blendermcp_server

        scene.blendermcp_server_running = False

        return {'FINISHED'}


# Registration functions
def register():
    bpy.types.Scene.blendermcp_port = IntProperty(
        name="Port",
        description="Port for the BlenderMCP server",
        default=9876,
        min=1024,
        max=65535
    )

    bpy.types.Scene.blendermcp_server_running = bpy.props.BoolProperty(
        name="Server Running",
        default=False
    )

    bpy.types.Scene.blendermcp_use_polyhaven = bpy.props.BoolProperty(
        name="Use Poly Haven",
        description="Enable Poly Haven asset integration",
        default=False
    )

    bpy.types.Scene.blendermcp_use_hyper3d = bpy.props.BoolProperty(
        name="Use Hyper3D Rodin",
        description="Enable Hyper3D Rodin generatino integration",
        default=False
    )

    bpy.types.Scene.blendermcp_use_geometry_nodes = bpy.props.BoolProperty(
        name="Use Geometry Nodes",
        description="Enable Geometry Nodes integration for procedural modeling",
        default=False
    )

    bpy.types.Scene.blendermcp_hyper3d_mode = bpy.props.EnumProperty(
        name="Rodin Mode",
        description="Choose the platform used to call Rodin APIs",
        items=[
            ("MAIN_SITE", "hyper3d.ai", "hyper3d.ai"),
            ("FAL_AI", "fal.ai", "fal.ai"),
        ],
        default="MAIN_SITE"
    )

    bpy.types.Scene.blendermcp_hyper3d_api_key = bpy.props.StringProperty(
        name="Hyper3D API Key",
        subtype="PASSWORD",
        description="API Key provided by Hyper3D",
        default=""
    )

    bpy.utils.register_class(BLENDERMCP_PT_Panel)
    bpy.utils.register_class(BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey)
    bpy.utils.register_class(BLENDERMCP_OT_StartServer)
    bpy.utils.register_class(BLENDERMCP_OT_StopServer)

    print("BlenderMCP addon registered")


def unregister():
    # Stop the server if it's running
    if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server:
        bpy.types.blendermcp_server.stop()
        del bpy.types.blendermcp_server

    bpy.utils.unregister_class(BLENDERMCP_PT_Panel)
    bpy.utils.unregister_class(BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey)
    bpy.utils.unregister_class(BLENDERMCP_OT_StartServer)
    bpy.utils.unregister_class(BLENDERMCP_OT_StopServer)

    del bpy.types.Scene.blendermcp_port
    del bpy.types.Scene.blendermcp_server_running
    del bpy.types.Scene.blendermcp_use_polyhaven
    del bpy.types.Scene.blendermcp_use_hyper3d
    del bpy.types.Scene.blendermcp_use_geometry_nodes
    del bpy.types.Scene.blendermcp_hyper3d_mode
    del bpy.types.Scene.blendermcp_hyper3d_api_key

    print("BlenderMCP addon unregistered")


if __name__ == "__main__":
    register()
