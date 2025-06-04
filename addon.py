# Code created by Siddharth Ahuja: www.github.com/ahujasid © 2025

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
import io
from contextlib import redirect_stdout

bl_info = {
    "name": "Blender MCP",
    "author": "BlenderMCP",
    "version": (1, 2), # Increment if significant features added
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > BlenderMCP",
    "description": "Connect Blender to LLMs via MCP, with asset integration, procedural generation, and scene analysis.",
    "category": "Interface",
}

# Standard library imports
import json
import math
import os
import random
import shutil
import socket
import tempfile
import threading
import time
import traceback
import io
from contextlib import redirect_stdout
from pathlib import Path
from datetime import datetime

# Blender imports
import bpy
import mathutils
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty

# Local imports
from . import addon_utils # For our utility functions
# Ensure llm_handler is imported if MCP_OT_AskLLMAboutScene uses it directly
# For now, assuming it's imported within the execute method as per previous structure.


RODIN_FREE_TRIAL_KEY = (
    "k9TcfFoEhNd9cCPP2guHAHHHkctZHIRhZDywZ1euGUXwihbYLpOjQhofby80NJez"
)

# Note: All utility functions (screenshot helpers, create_... functions, add_detail_shape)
# are now located in addon_utils.py and accessed via addon_utils.function_name


class BlenderMCPServer:
    def __init__(self, host="localhost", port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None

    def start(self):
        if self.running:
            print("BlenderMCP: Server is already running")
            return
        self.running = True
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            self.server_thread = threading.Thread(target=self._server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()
            print(f"BlenderMCP: Server started on {self.host}:{self.port}")
        except Exception as e:
            print(f"BlenderMCP: Failed to start server: {str(e)}")
            self.stop()

    def stop(self):
        self.running = False
        if self.socket:
            try: self.socket.close()
            except Exception as e: print(f"BlenderMCP: Error closing socket: {e}")
            self.socket = None
        if self.server_thread and self.server_thread.is_alive():
            try: self.server_thread.join(timeout=1.0)
            except Exception as e: print(f"BlenderMCP: Error joining server thread: {e}")
        self.server_thread = None
        print("BlenderMCP: Server stopped")

    def _server_loop(self):
        print("BlenderMCP: Server thread started")
        self.socket.settimeout(1.0)
        while self.running:
            try:
                client, address = self.socket.accept()
                print(f"BlenderMCP: Connected to client: {address}")
                client_thread = threading.Thread(target=self._handle_client, args=(client,))
                client_thread.daemon = True
                client_thread.start()
            except socket.timeout: continue
            except Exception as e:
                if self.running: # Avoid error message if stopping
                    print(f"BlenderMCP: Error accepting connection: {str(e)}")
                time.sleep(0.5)
        print("BlenderMCP: Server thread stopped")

    def _handle_client(self, client):
        print(f"BlenderMCP: Client handler started for {client.getpeername()}")
        client.settimeout(None)
        buffer = b""
        try:
            while self.running:
                data = client.recv(8192)
                if not data:
                    print(f"BlenderMCP: Client {client.getpeername()} disconnected")
                    break
                buffer += data
                try:
                    command = json.loads(buffer.decode("utf-8"))
                    buffer = b"" # Clear buffer after successful parse

                    # Schedule execution in Blender's main thread
                    def execute_wrapper():
                        try:
                            response = self.execute_command(command)
                            response_json = json.dumps(response)
                            client.sendall(response_json.encode("utf-8"))
                        except Exception as e:
                            print(f"BlenderMCP: Error executing command or sending response: {str(e)}")
                            traceback.print_exc()
                            try:
                                error_response = {"status": "error", "message": f"Unhandled error: {str(e)}"}
                                client.sendall(json.dumps(error_response).encode("utf-8"))
                            except Exception as e2:
                                print(f"BlenderMCP: Critical error sending error response: {e2}")
                        return None # Timer function should return None or a delay
                    bpy.app.timers.register(execute_wrapper, first_interval=0.0)
                except json.JSONDecodeError: # Incomplete data, continue receiving
                    continue
                except Exception as e: # Catch other errors related to client handling
                    print(f"BlenderMCP: Error processing data from {client.getpeername()}: {str(e)}")
                    break # Stop handling this client
        except Exception as e:
            if self.running: # Avoid error if server is stopping
                 print(f"BlenderMCP: Error in client handler for {client.getpeername()}: {str(e)}")
        finally:
            try: client.close()
            except: pass
            print(f"BlenderMCP: Client handler for {client.getpeername()} stopped")

    def execute_command(self, command):
        try:
            return self._execute_command_internal(command)
        except Exception as e:
            print(f"BlenderMCP: Error executing command_internal: {str(e)}")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def _execute_command_internal(self, command):
        cmd_type = command.get("type")
        params = command.get("params", {})

        handlers = {
            "get_scene_info": self.get_scene_info,
            "get_object_info": self.get_object_info,
            "execute_code": self.execute_code,
            "get_polyhaven_status": self.get_polyhaven_status,
            "get_hyper3d_status": self.get_hyper3d_status,
            "import_model_from_path": self.import_model_from_path,
            "get_mesh_details": self.get_mesh_details,
        }
        if bpy.context.scene.blendermcp_use_polyhaven:
            handlers.update({
                "get_polyhaven_categories": self.get_polyhaven_categories,
                "search_polyhaven_assets": self.search_polyhaven_assets,
                "download_polyhaven_asset": self.download_polyhaven_asset,
                "set_texture": self.set_texture,
            })
        if bpy.context.scene.blendermcp_use_hyper3d:
            handlers.update({
                "create_rodin_job": self.create_rodin_job,
                "poll_rodin_job_status": self.poll_rodin_job_status,
                "import_generated_asset": self.import_generated_asset,
            })

        handler = handlers.get(cmd_type)
        if handler:
            try:
                print(f"BlenderMCP: Executing handler for {cmd_type} with params {params}")
                result = handler(**params)
                print(f"BlenderMCP: Handler {cmd_type} execution complete.")
                return {"status": "success", "result": result}
            except Exception as e:
                print(f"BlenderMCP: Error in handler {cmd_type}: {str(e)}")
                traceback.print_exc()
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"Unknown command type: {cmd_type}"}

    def get_scene_info(self):
        # (Assuming this function's internal logic is correct from previous state)
        scene_info = {"name": bpy.context.scene.name, "object_count": len(bpy.context.scene.objects), "objects": [], "materials_count": len(bpy.data.materials)}
        for i, obj in enumerate(bpy.context.scene.objects):
            if i >= 10: break
            obj_info = {"name": obj.name, "type": obj.type, "location": [round(float(c), 2) for c in obj.location]}
            scene_info["objects"].append(obj_info)
        return scene_info

    @staticmethod
    def _get_aabb(obj):
        # (Assuming this function's internal logic is correct)
        if obj.type != "MESH": raise TypeError("Object must be a mesh")
        local_bbox_corners = [mathutils.Vector(corner) for corner in obj.bound_box]
        world_bbox_corners = [obj.matrix_world @ corner for corner in local_bbox_corners]
        min_corner = mathutils.Vector(map(min, zip(*world_bbox_corners)))
        max_corner = mathutils.Vector(map(max, zip(*world_bbox_corners)))
        return [[*min_corner], [*max_corner]]

    def get_object_info(self, name: str):
        # (Assuming this function's internal logic is correct)
        obj = bpy.data.objects.get(name)
        if not obj: raise ValueError(f"Object not found: {name}")
        obj_info = {"name": obj.name, "type": obj.type, "location": [obj.location.x, obj.location.y, obj.location.z], "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z], "scale": [obj.scale.x, obj.scale.y, obj.scale.z], "visible": obj.visible_get(), "materials": []}
        if obj.type == "MESH": obj_info["world_bounding_box"] = self._get_aabb(obj) # Corrected call
        for slot in obj.material_slots:
            if slot.material: obj_info["materials"].append(slot.material.name)
        if obj.type == "MESH" and obj.data:
            mesh = obj.data
            obj_info["mesh"] = {"vertices": len(mesh.vertices), "edges": len(mesh.edges), "polygons": len(mesh.polygons)}
        return obj_info

    def execute_code(self, code):
        try:
            namespace = {
                "bpy": bpy, "math": math, "random": random, "mathutils": mathutils,
                "create_modified_cube": addon_utils.create_modified_cube,
                "create_voronoi_rock": addon_utils.create_voronoi_rock,
                "create_parametric_gear": addon_utils.create_parametric_gear,
                "create_pipe_joint": addon_utils.create_pipe_joint,
                "create_simple_tree": addon_utils.create_simple_tree,
                "create_chain_link": addon_utils.create_chain_link,
                "add_detail_shape": addon_utils.add_detail_shape
            }
            capture_buffer = io.StringIO()
            with redirect_stdout(capture_buffer): exec(code, namespace)
            return {"executed": True, "result": capture_buffer.getvalue()}
        except Exception as e:
            print(f"BlenderMCP: Code execution error: {str(e)}")
            traceback.print_exc()
            raise Exception(f"Code execution error: {str(e)}")

    def get_polyhaven_categories(self, asset_type): return {} # Placeholder
    def search_polyhaven_assets(self, asset_type=None, categories=None): return {} # Placeholder
    def download_polyhaven_asset(self, asset_id, asset_type, resolution="1k", file_format=None): return {} # Placeholder
    def set_texture(self, object_name, texture_id): return {} # Placeholder
    def get_polyhaven_status(self): return {"enabled": bpy.context.scene.blendermcp_use_polyhaven, "message": "Status"}
    def get_hyper3d_status(self): return {"enabled": bpy.context.scene.blendermcp_use_hyper3d, "message": "Status"}

    def create_rodin_job(self, tier: str = None, mesh_mode: str = None, *args, **kwargs):
        params_to_pass = kwargs.copy()
        if tier is not None: params_to_pass['tier'] = tier
        if mesh_mode is not None: params_to_pass['mesh_mode'] = mesh_mode
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE": return self.create_rodin_job_main_site(*args, **params_to_pass)
            case "FAL_AI": return self.create_rodin_job_fal_ai(*args, **params_to_pass)
            case _: return {"error": f"Unknown Hyper3D Rodin mode!"} # Return dict for errors

    def create_rodin_job_main_site(self, text_prompt: str = None, images: list[tuple[str, str]] = None, bbox_condition=None, tier: str = None, mesh_mode: str = None):
        try:
            if images is None: images = []
            resolved_tier = tier if tier is not None else bpy.context.scene.mcp_hyper3d_tier
            resolved_mesh_mode = mesh_mode if mesh_mode is not None else bpy.context.scene.mcp_hyper3d_mesh_mode
            files = [("images", (f"{i:04d}{img_suffix}", img)) for i, (img_suffix, img) in enumerate(images)]
            files.extend([("tier", (None, resolved_tier)), ("mesh_mode", (None, resolved_mesh_mode))])
            if text_prompt: files.append(("prompt", (None, text_prompt)))
            if bbox_condition: files.append(("bbox_condition", (None, json.dumps(bbox_condition))))
            response = requests.post("https://hyperhuman.deemos.com/api/v2/rodin", headers={"Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}"}, files=files)
            response.raise_for_status() # Raise HTTPError for bad responses (4XX or 5XX)
            return response.json()
        except requests.exceptions.RequestException as e: return {"error": f"API Request failed: {str(e)}"}
        except Exception as e: return {"error": str(e)}

    def create_rodin_job_fal_ai(self, text_prompt: str = None, images: list[tuple[str, str]] = None, bbox_condition=None, tier: str = None):
        try:
            resolved_tier = tier if tier is not None else bpy.context.scene.mcp_hyper3d_tier
            req_data = {"tier": resolved_tier}
            if images: req_data["input_image_urls"] = images # Fal expects URLs
            if text_prompt: req_data["prompt"] = text_prompt
            if bbox_condition: req_data["bbox_condition"] = bbox_condition
            response = requests.post("https://queue.fal.run/fal-ai/hyper3d/rodin", headers={"Authorization": f"Key {bpy.context.scene.blendermcp_hyper3d_api_key}", "Content-Type": "application/json"}, json=req_data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e: return {"error": f"API Request failed: {str(e)}"}
        except Exception as e: return {"error": str(e)}

    def poll_rodin_job_status(self, *args, **kwargs): return {} # Placeholder
    @staticmethod
    def _clean_imported_glb(filepath, mesh_name=None): return None # Placeholder
    def import_generated_asset(self, *args, **kwargs): return {} # Placeholder
    def import_model_from_path(self, path: str): return {} # Placeholder
    def get_mesh_details(self, name: str):
        obj = bpy.data.objects.get(name)
        if not obj: return {"error": f"Object not found: {name}"}
        if obj.type != 'MESH': return {"error": f"Object '{name}' is not a mesh (type: {obj.type})"}
        mesh = obj.data
        return {"name": obj.name, "vertices": len(mesh.vertices), "faces": len(mesh.polygons), "modifiers": [mod.name for mod in obj.modifiers]}

# Blender UI Panel
class BLENDERMCP_PT_Panel(bpy.types.Panel):
    bl_label = "Blender MCP"
    bl_idname = "BLENDERMCP_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderMCP"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene, "blendermcp_port")
        layout.prop(scene, "blendermcp_use_polyhaven", text="Use assets from Poly Haven")
        layout.prop(scene, "blendermcp_use_hyper3d", text="Use Hyper3D Rodin") # Simplified text
        if scene.blendermcp_use_hyper3d:
            layout.prop(scene, "blendermcp_hyper3d_mode", text="Rodin Mode")
            layout.prop(scene, "blendermcp_hyper3d_api_key", text="API Key")
            layout.prop(scene, "mcp_hyper3d_tier")
            layout.prop(scene, "mcp_hyper3d_mesh_mode")
            layout.operator("blendermcp.set_hyper3d_free_trial_api_key", text="Set Free Trial API Key")

        layout.separator()
        layout.label(text="LLM Configuration:")
        layout.prop(context.scene, "mcp_llm_backend", text="LLM Backend")
        if scene.mcp_llm_backend == "claude":
            layout.prop(scene, "mcp_claude_model_name", text="Claude Model")
        elif scene.mcp_llm_backend == "ollama":
            layout.prop(scene, "mcp_ollama_model_name", text="Ollama Model")

        layout.separator()
        layout.label(text="Scene Interaction:")
        layout.prop(scene, "mcp_screenshot_history_limit")
        layout.operator("mcp.ask_llm_about_scene", text="Ask LLM About Scene") # Added button

        layout.separator()
        if not scene.blendermcp_server_running:
            layout.operator("blendermcp.start_server", text="Start MCP Server")
        else:
            layout.operator("blendermcp.stop_server", text="Stop MCP Server")
            layout.label(text=f"Server running on port {scene.blendermcp_port}")

def render_and_save_image():
    history_limit = bpy.context.scene.mcp_screenshot_history_limit
    if history_limit < 1: history_limit = 1

    new_image_path_obj = addon_utils.get_screenshot_filepath()
    new_image_path_str = str(new_image_path_obj)

    print(f"BlenderMCP: Attempting to save screenshot to: {new_image_path_str}")
    bpy.context.scene.render.filepath = new_image_path_str

    render_result = None
    try:
        render_result = bpy.ops.render.opengl(write_still=True)
        print(f"BlenderMCP: bpy.ops.render.opengl() result: {render_result}")
        if render_result == {'CANCELLED'}:
            print(f"BlenderMCP: ERROR - bpy.ops.render.opengl() was cancelled. Screenshot not saved: {new_image_path_str}.")
    except Exception as e:
        print(f"BlenderMCP: EXCEPTION during bpy.ops.render.opengl(): {str(e)}")
        render_result = {'EXCEPTION_RAISED'}

    if new_image_path_obj.exists():
        print(f"BlenderMCP: Screenshot successfully saved: {new_image_path_str}")
    else:
        print(f"BlenderMCP: ERROR - Screenshot file NOT found after render call: {new_image_path_str}")

    try:
        addon_utils._ensure_screenshot_dir_exists()
        screenshots = list(addon_utils.SCREENSHOT_DIR_PATH.glob("*.png"))
        screenshots.sort(key=lambda p: p.name)
        if len(screenshots) > history_limit:
            num_to_delete = len(screenshots) - history_limit
            for i in range(num_to_delete):
                print(f"BlenderMCP: Attempting to delete old screenshot: {screenshots[i]}")
                try:
                    os.remove(screenshots[i])
                    print(f"BlenderMCP: Removed old screenshot: {screenshots[i]}")
                except OSError as e:
                    print(f"BlenderMCP: ERROR deleting screenshot {screenshots[i]}: {e}")
    except Exception as e:
        print(f"BlenderMCP: ERROR during screenshot history management: {e}")
    return new_image_path_str

def extract_scene_summary():
    summary = []
    for obj in bpy.data.objects:
        summary.append(f"{obj.name}: {obj.type}, Location: {obj.location}, Visible: {obj.visible_get()}")
    return "\n".join(summary)

class MCP_OT_AskLLMAboutScene(bpy.types.Operator):
    bl_idname = "mcp.ask_llm_about_scene"
    bl_label = "Ask LLM About Scene"
    def execute(self, context):
        # Ensure llm_handler is imported correctly, typically done at module level
        # but can be function-local if it causes issues during registration
        from .llm_handler import query_llm

        image_path = render_and_save_image()
        metadata = extract_scene_summary()
        backend = context.scene.mcp_llm_backend

        kwargs_to_pass = {"backend": backend, "image_path": image_path, "metadata": metadata}
        if backend == "ollama":
            kwargs_to_pass["ollama_model_name"] = context.scene.mcp_ollama_model_name
        # Add similar logic for claude_model_name if query_llm expects it for claude backend
        # elif backend == "claude":
        #     kwargs_to_pass["claude_model_name"] = context.scene.mcp_claude_model_name

        response = query_llm(**kwargs_to_pass)
        self.report({"INFO"}, response[:400] if isinstance(response, str) else "LLM response format unexpected.")
        print("LLM Response:", response)
        return {"FINISHED"}

class BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey(bpy.types.Operator):
    bl_idname = "blendermcp.set_hyper3d_free_trial_api_key"
    bl_label = "Set Free Trial API Key"
    def execute(self, context):
        context.scene.blendermcp_hyper3d_api_key = RODIN_FREE_TRIAL_KEY
        context.scene.blendermcp_hyper3d_mode = "MAIN_SITE"
        self.report({"INFO"}, "API Key set successfully!")
        return {"FINISHED"}

class BLENDERMCP_OT_StartServer(bpy.types.Operator):
    bl_idname = "blendermcp.start_server"
    bl_label = "Start MCP Server"
    bl_description = "Start the BlenderMCP server."
    def execute(self, context):
        scene = context.scene
        if not hasattr(bpy.types, "blendermcp_server") or bpy.types.blendermcp_server is None:
            bpy.types.blendermcp_server = BlenderMCPServer(port=scene.blendermcp_port)
        if not bpy.types.blendermcp_server.running:
            bpy.types.blendermcp_server.start()
        scene.blendermcp_server_running = bpy.types.blendermcp_server.running
        return {"FINISHED"}

class BLENDERMCP_OT_StopServer(bpy.types.Operator):
    bl_idname = "blendermcp.stop_server"
    bl_label = "Stop MCP Server"
    bl_description = "Stop the BlenderMCP server."
    def execute(self, context):
        scene = context.scene
        if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server is not None:
            if bpy.types.blendermcp_server.running:
                bpy.types.blendermcp_server.stop()
            # Consider del bpy.types.blendermcp_server here if appropriate
        scene.blendermcp_server_running = False
        return {"FINISHED"}

# Registration functions
def register():
    bpy.types.Scene.blendermcp_port = IntProperty(name="Port", description="Port for the BlenderMCP server", default=9876, min=1024, max=65535)
    bpy.types.Scene.mcp_llm_backend = EnumProperty(name="LLM Backend", description="Choose LLM backend", items=[("claude", "Claude", "Use Claude API"),("ollama", "Ollama", "Use Ollama locally")], default="ollama")
    bpy.types.Scene.mcp_claude_model_name = bpy.props.StringProperty(name="Claude Model", description="Claude model name (e.g., claude-3-opus-20240229)", default="claude-3-opus-20240229")
    bpy.types.Scene.mcp_ollama_model_name = bpy.props.StringProperty(name="Ollama Model", description="Ollama model name (e.g., llava:latest, gemma3:4b)", default="llava:latest") # Default changed to llava
    bpy.types.Scene.mcp_screenshot_history_limit = bpy.props.IntProperty(name="Screenshot History", description="Max screenshots. 0 for 1.", default=10, min=0)
    bpy.types.Scene.blendermcp_server_running = bpy.props.BoolProperty(name="Server Running", default=False)
    bpy.types.Scene.blendermcp_use_polyhaven = bpy.props.BoolProperty(name="Use Poly Haven", description="Enable Poly Haven asset integration", default=False)
    bpy.types.Scene.blendermcp_use_hyper3d = bpy.props.BoolProperty(name="Use Hyper3D Rodin", description="Enable Hyper3D Rodin generation", default=False)
    bpy.types.Scene.blendermcp_hyper3d_mode = bpy.props.EnumProperty(name="Rodin Mode", description="Choose Rodin API platform", items=[("MAIN_SITE", "hyper3d.ai", "hyper3d.ai"),("FAL_AI", "fal.ai", "fal.ai")], default="MAIN_SITE")
    bpy.types.Scene.blendermcp_hyper3d_api_key = bpy.props.StringProperty(name="Hyper3D API Key", subtype="PASSWORD", description="API Key for Hyper3D", default="")
    bpy.types.Scene.mcp_hyper3d_tier = bpy.props.StringProperty(name="Hyper3D Tier", description="Default tier for Hyper3D (e.g., Sketch, Detailed)", default="Sketch")
    bpy.types.Scene.mcp_hyper3d_mesh_mode = bpy.props.StringProperty(name="Hyper3D Mesh Mode", description="Default mesh mode for Hyper3D (e.g., Raw, HighPoly)", default="Raw")

    bpy.utils.register_class(BLENDERMCP_PT_Panel)
    bpy.utils.register_class(BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey)
    bpy.utils.register_class(BLENDERMCP_OT_StartServer)
    bpy.utils.register_class(BLENDERMCP_OT_StopServer)
    bpy.utils.register_class(MCP_OT_AskLLMAboutScene)

    print("BlenderMCP addon registered with all features.")

def unregister():
    if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server:
        bpy.types.blendermcp_server.stop()
        del bpy.types.blendermcp_server

    classes_to_unregister = [
        BLENDERMCP_PT_Panel,
        BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey,
        BLENDERMCP_OT_StartServer,
        BLENDERMCP_OT_StopServer,
        MCP_OT_AskLLMAboutScene
    ]
    for cls in classes_to_unregister:
        if hasattr(bpy.types, cls.__name__): # Check if class is registered
             bpy.utils.unregister_class(cls)

    props_to_delete = [
        "blendermcp_port", "mcp_llm_backend", "mcp_claude_model_name",
        "mcp_ollama_model_name", "mcp_screenshot_history_limit",
        "blendermcp_server_running", "blendermcp_use_polyhaven",
        "blendermcp_use_hyper3d", "blendermcp_hyper3d_mode",
        "blendermcp_hyper3d_api_key", "mcp_hyper3d_tier", "mcp_hyper3d_mesh_mode"
    ]
    for prop in props_to_delete:
        if hasattr(bpy.types.Scene, prop):
            delattr(bpy.types.Scene, prop)

    print("BlenderMCP addon unregistered.")

if __name__ == "__main__":
    register()

# Imports for new utilities
from pathlib import Path
from datetime import datetime
import math
import random
from . import addon_utils # For our utility functions

RODIN_FREE_TRIAL_KEY = (
    "k9TcfFoEhNd9cCPP2guHAHHHkctZHIRhZDywZ1euGUXwihbYLpOjQhofby80NJez"
)

# Note: Screenshot helper functions (_ensure_screenshot_dir_exists, get_screenshot_filepath)
# and all create_... functions (create_modified_cube, create_voronoi_rock, etc.)
# and add_detail_shape are now in addon_utils.py

class BlenderMCPServer:
    def __init__(self, host="localhost", port=9876):
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
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            self.server_thread = threading.Thread(target=self._server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()
            print(f"BlenderMCP server started on {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to start server: {str(e)}")
            self.stop()

    def stop(self):
        self.running = False
        if self.socket:
            try: self.socket.close()
            except: pass
            self.socket = None
        if self.server_thread:
            try:
                if self.server_thread.is_alive(): self.server_thread.join(timeout=1.0)
            except: pass
            self.server_thread = None
        print("BlenderMCP server stopped")

    def _server_loop(self):
        print("Server thread started")
        self.socket.settimeout(1.0)
        while self.running:
            try:
                try:
                    client, address = self.socket.accept()
                    print(f"Connected to client: {address}")
                    client_thread = threading.Thread(target=self._handle_client, args=(client,))
                    client_thread.daemon = True
                    client_thread.start()
                except socket.timeout: continue
                except Exception as e:
                    print(f"Error accepting connection: {str(e)}")
                    time.sleep(0.5)
            except Exception as e:
                print(f"Error in server loop: {str(e)}")
                if not self.running: break
                time.sleep(0.5)
        print("Server thread stopped")

    def _handle_client(self, client):
        print("Client handler started")
        client.settimeout(None)
        buffer = b""
        try:
            while self.running:
                try:
                    data = client.recv(8192)
                    if not data:
                        print("Client disconnected")
                        break
                    buffer += data
                    try:
                        command = json.loads(buffer.decode("utf-8"))
                        buffer = b""
                        def execute_wrapper():
                            try:
                                response = self.execute_command(command)
                                response_json = json.dumps(response)
                                try: client.sendall(response_json.encode("utf-8"))
                                except: print("Failed to send response - client disconnected")
                            except Exception as e:
                                print(f"Error executing command: {str(e)}")
                                traceback.print_exc()
                                try:
                                    error_response = {"status": "error", "message": str(e)}
                                    client.sendall(json.dumps(error_response).encode("utf-8"))
                                except: pass
                            return None
                        bpy.app.timers.register(execute_wrapper, first_interval=0.0)
                    except json.JSONDecodeError: pass
                except Exception as e:
                    print(f"Error receiving data: {str(e)}")
                    break
        except Exception as e: print(f"Error in client handler: {str(e)}")
        finally:
            try: client.close()
            except: pass
            print("Client handler stopped")

    def execute_command(self, command):
        try: return self._execute_command_internal(command)
        except Exception as e:
            print(f"Error executing command: {str(e)}")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def _execute_command_internal(self, command):
        cmd_type = command.get("type")
        params = command.get("params", {})
        if cmd_type == "get_polyhaven_status": return {"status": "success", "result": self.get_polyhaven_status()}

        handlers = {
            "get_scene_info": self.get_scene_info,
            "get_object_info": self.get_object_info,
            "execute_code": self.execute_code,
            "get_polyhaven_status": self.get_polyhaven_status,
            "get_hyper3d_status": self.get_hyper3d_status,
            "import_model_from_path": self.import_model_from_path,
            "get_mesh_details": self.get_mesh_details,
        }
        if bpy.context.scene.blendermcp_use_polyhaven:
            polyhaven_handlers = {
                "get_polyhaven_categories": self.get_polyhaven_categories,
                "search_polyhaven_assets": self.search_polyhaven_assets,
                "download_polyhaven_asset": self.download_polyhaven_asset,
                "set_texture": self.set_texture,
            }
            handlers.update(polyhaven_handlers)
        if bpy.context.scene.blendermcp_use_hyper3d:
            hyper3d_handlers = { # Corrected variable name
                "create_rodin_job": self.create_rodin_job,
                "poll_rodin_job_status": self.poll_rodin_job_status,
                "import_generated_asset": self.import_generated_asset,
            }
            handlers.update(hyper3d_handlers) # Corrected variable name

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
        else: return {"status": "error", "message": f"Unknown command type: {cmd_type}"}

    def get_scene_info(self):
        try:
            print("Getting scene info...")
            scene_info = {"name": bpy.context.scene.name, "object_count": len(bpy.context.scene.objects), "objects": [], "materials_count": len(bpy.data.materials)}
            for i, obj in enumerate(bpy.context.scene.objects):
                if i >= 10: break
                obj_info = {"name": obj.name, "type": obj.type, "location": [round(float(obj.location.x),2), round(float(obj.location.y),2), round(float(obj.location.z),2)]}
                scene_info["objects"].append(obj_info)
            print(f"Scene info collected: {len(scene_info['objects'])} objects")
            return scene_info
        except Exception as e:
            print(f"Error in get_scene_info: {str(e)}")
            traceback.print_exc()
            return {"error": str(e)}

    @staticmethod
    def _get_aabb(obj):
        if obj.type != "MESH": raise TypeError("Object must be a mesh")
        local_bbox_corners = [mathutils.Vector(corner) for corner in obj.bound_box]
        world_bbox_corners = [obj.matrix_world @ corner for corner in local_bbox_corners]
        min_corner = mathutils.Vector(map(min, zip(*world_bbox_corners)))
        max_corner = mathutils.Vector(map(max, zip(*world_bbox_corners)))
        return [[*min_corner], [*max_corner]]

    def get_object_info(self, name):
        obj = bpy.data.objects.get(name)
        if not obj: raise ValueError(f"Object not found: {name}")
        obj_info = {"name": obj.name, "type": obj.type, "location": [obj.location.x, obj.location.y, obj.location.z], "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z], "scale": [obj.scale.x, obj.scale.y, obj.scale.z], "visible": obj.visible_get(), "materials": []}
        if obj.type == "MESH": obj_info["world_bounding_box"] = self._get_aabb(obj)
        for slot in obj.material_slots:
            if slot.material: obj_info["materials"].append(slot.material.name)
        if obj.type == "MESH" and obj.data:
            mesh = obj.data
            obj_info["mesh"] = {"vertices": len(mesh.vertices), "edges": len(mesh.edges), "polygons": len(mesh.polygons)}
        return obj_info

    def execute_code(self, code):
        try:
            namespace = {
                "bpy": bpy,
                "create_modified_cube": addon_utils.create_modified_cube,
                "create_voronoi_rock": addon_utils.create_voronoi_rock,
                "create_parametric_gear": addon_utils.create_parametric_gear,
                "create_pipe_joint": addon_utils.create_pipe_joint,
                "create_simple_tree": addon_utils.create_simple_tree,
                "create_chain_link": addon_utils.create_chain_link,
                "add_detail_shape": addon_utils.add_detail_shape
            }
            capture_buffer = io.StringIO()
            with redirect_stdout(capture_buffer): exec(code, namespace)
            return {"executed": True, "result": capture_buffer.getvalue()}
        except Exception as e: raise Exception(f"Code execution error: {str(e)}")

    def get_polyhaven_categories(self, asset_type):
        # (Code for this method - assumed to be correct from previous state)
        # ...
        return {} # Placeholder

    def search_polyhaven_assets(self, asset_type=None, categories=None):
        # (Code for this method - assumed to be correct from previous state)
        # ...
        return {} # Placeholder

    def download_polyhaven_asset(self, asset_id, asset_type, resolution="1k", file_format=None):
        # (Code for this method - assumed to be correct from previous state)
        # ...
        return {} # Placeholder

    def set_texture(self, object_name, texture_id):
        # (Code for this method - assumed to be correct from previous state)
        # ...
        return {} # Placeholder

    def get_polyhaven_status(self):
        enabled = bpy.context.scene.blendermcp_use_polyhaven
        if enabled: return {"enabled": True, "message": "PolyHaven integration is enabled."}
        else: return {"enabled": False, "message": "PolyHaven integration disabled."}

    def get_hyper3d_status(self):
        enabled = bpy.context.scene.blendermcp_use_hyper3d
        # (Code for this method - assumed to be correct from previous state)
        # ...
        if enabled: return {"enabled": True, "message": "Hyper3D enabled."}
        else: return {"enabled": False, "message": "Hyper3D disabled."}


    def create_rodin_job(self, tier: str = None, mesh_mode: str = None, *args, **kwargs):
        params_to_pass = kwargs.copy()
        if tier is not None: params_to_pass['tier'] = tier
        if mesh_mode is not None: params_to_pass['mesh_mode'] = mesh_mode
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE": return self.create_rodin_job_main_site(*args, **params_to_pass)
            case "FAL_AI": return self.create_rodin_job_fal_ai(*args, **params_to_pass)
            case _: return f"Error: Unknown Hyper3D Rodin mode!"

    def create_rodin_job_main_site(self, text_prompt: str = None, images: list[tuple[str, str]] = None, bbox_condition=None, tier: str = None, mesh_mode: str = None):
        try:
            if images is None: images = []
            resolved_tier = tier if tier is not None else bpy.context.scene.mcp_hyper3d_tier
            resolved_mesh_mode = mesh_mode if mesh_mode is not None else bpy.context.scene.mcp_hyper3d_mesh_mode
            files = [("images", (f"{i:04d}{img_suffix}", img)) for i, (img_suffix, img) in enumerate(images)]
            files.extend([("tier", (None, resolved_tier)), ("mesh_mode", (None, resolved_mesh_mode))])
            if text_prompt: files.append(("prompt", (None, text_prompt)))
            if bbox_condition: files.append(("bbox_condition", (None, json.dumps(bbox_condition))))
            response = requests.post("https://hyperhuman.deemos.com/api/v2/rodin", headers={"Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}"}, files=files)
            return response.json()
        except Exception as e: return {"error": str(e)}

    def create_rodin_job_fal_ai(self, text_prompt: str = None, images: list[tuple[str, str]] = None, bbox_condition=None, tier: str = None):
        try:
            resolved_tier = tier if tier is not None else bpy.context.scene.mcp_hyper3d_tier
            req_data = {"tier": resolved_tier}
            if images: req_data["input_image_urls"] = images
            if text_prompt: req_data["prompt"] = text_prompt
            if bbox_condition: req_data["bbox_condition"] = bbox_condition
            response = requests.post("https://queue.fal.run/fal-ai/hyper3d/rodin", headers={"Authorization": f"Key {bpy.context.scene.blendermcp_hyper3d_api_key}", "Content-Type": "application/json"}, json=req_data)
            return response.json()
        except Exception as e: return {"error": str(e)}

    def poll_rodin_job_status(self, *args, **kwargs):
        # (Code for this method - assumed to be correct from previous state)
        # ...
        return {} # Placeholder

    @staticmethod
    def _clean_imported_glb(filepath, mesh_name=None):
        # (Code for this method - assumed to be correct from previous state)
        # ...
        return None # Placeholder

    def import_generated_asset(self, *args, **kwargs):
        # (Code for this method - assumed to be correct from previous state)
        # ...
        return {} # Placeholder

    def import_model_from_path(self, path: str):
        # (Code for this method - assumed to be correct from previous state)
        # ...
        return {} # Placeholder

    def get_mesh_details(self, name: str):
        obj = bpy.data.objects.get(name)
        if not obj: return {"error": f"Object not found: {name}"}
        if obj.type != 'MESH': return {"error": f"Object '{name}' is not a mesh (type: {obj.type})"}
        mesh = obj.data
        return {"name": obj.name, "vertices": len(mesh.vertices), "faces": len(mesh.polygons), "modifiers": [mod.name for mod in obj.modifiers]}

# Blender UI Panel
class BLENDERMCP_PT_Panel(bpy.types.Panel):
    bl_label = "Blender MCP"
    bl_idname = "BLENDERMCP_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderMCP"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene, "blendermcp_port")
        layout.prop(scene, "blendermcp_use_polyhaven", text="Use assets from Poly Haven")
        layout.prop(scene, "blendermcp_use_hyper3d", text="Use Hyper3D Rodin 3D model generation")
        if scene.blendermcp_use_hyper3d:
            layout.prop(scene, "blendermcp_hyper3d_mode", text="Rodin Mode")
            layout.prop(scene, "blendermcp_hyper3d_api_key", text="API Key")
            layout.prop(scene, "mcp_hyper3d_tier") # New UI
            layout.prop(scene, "mcp_hyper3d_mesh_mode") # New UI
            layout.operator("blendermcp.set_hyper3d_free_trial_api_key", text="Set Free Trial API Key")
        layout.prop(context.scene, "mcp_llm_backend", text="LLM Backend")
        if scene.mcp_llm_backend == "claude":
            layout.prop(scene, "mcp_claude_model_name", text="Claude Model")
        elif scene.mcp_llm_backend == "ollama":
            layout.prop(scene, "mcp_ollama_model_name", text="Ollama Model")
        layout.prop(scene, "mcp_screenshot_history_limit") # New UI
        if not scene.blendermcp_server_running:
            layout.operator("blendermcp.start_server", text="Connect to MCP server")
        else:
            layout.operator("blendermcp.stop_server", text="Disconnect from MCP server")
            layout.label(text=f"Running on port {scene.blendermcp_port}")

def render_and_save_image():
    history_limit = bpy.context.scene.mcp_screenshot_history_limit
    if history_limit < 1: history_limit = 1
    new_image_path_obj = addon_utils.get_screenshot_filepath()
    new_image_path_str = str(new_image_path_obj)
    print(f"BlenderMCP: Attempting to save screenshot to: {new_image_path_str}")
    bpy.context.scene.render.filepath = new_image_path_str
    render_result = None
    try:
        render_result = bpy.ops.render.opengl(write_still=True)
        print(f"BlenderMCP: bpy.ops.render.opengl() result: {render_result}")
        if render_result == {'CANCELLED'}:
            print(f"BlenderMCP: ERROR - bpy.ops.render.opengl() was cancelled. Screenshot not saved to {new_image_path_str}.")
    except Exception as e:
        print(f"BlenderMCP: EXCEPTION during bpy.ops.render.opengl(): {str(e)}")
        render_result = {'EXCEPTION_RAISED'}
    if new_image_path_obj.exists(): print(f"BlenderMCP: Screenshot successfully saved: {new_image_path_str}")
    else: print(f"BlenderMCP: ERROR - Screenshot file NOT found after render call: {new_image_path_str}")
    try:
        addon_utils._ensure_screenshot_dir_exists()
        screenshots = list(addon_utils.SCREENSHOT_DIR_PATH.glob("*.png"))
        screenshots.sort(key=lambda p: p.name)
        if len(screenshots) > history_limit:
            for i in range(len(screenshots) - history_limit):
                print(f"BlenderMCP: Attempting to delete old screenshot: {screenshots[i]}")
                try:
                    os.remove(screenshots[i])
                    print(f"BlenderMCP: Removed old screenshot: {screenshots[i]}")
                except OSError as e: print(f"BlenderMCP: ERROR deleting screenshot {screenshots[i]}: {e}")
    except Exception as e: print(f"BlenderMCP: ERROR during screenshot history management: {e}")
    return new_image_path_str

def extract_scene_summary():
    summary = []
    for obj in bpy.data.objects:
        summary.append(f"{obj.name}: {obj.type}, Location: {obj.location}, Visible: {obj.visible_get()}")
    return "\n".join(summary)

class MCP_OT_AskLLMAboutScene(bpy.types.Operator):
    bl_idname = "mcp.ask_llm_about_scene"
    bl_label = "Ask LLM About Scene"
    def execute(self, context):
        from .llm_handler import query_llm # Local import
        image_path = render_and_save_image()
        metadata = extract_scene_summary()
        backend = context.scene.mcp_llm_backend
        ollama_model_name = None
        if backend == "ollama": ollama_model_name = context.scene.mcp_ollama_model_name
        response = query_llm(backend=backend, image_path=image_path, metadata=metadata, ollama_model_name=ollama_model_name)
        self.report({"INFO"}, response[:400])
        print("LLM Response:", response)
        return {"FINISHED"}

class BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey(bpy.types.Operator):
    bl_idname = "blendermcp.set_hyper3d_free_trial_api_key"
    bl_label = "Set Free Trial API Key"
    def execute(self, context):
        context.scene.blendermcp_hyper3d_api_key = RODIN_FREE_TRIAL_KEY
        context.scene.blendermcp_hyper3d_mode = "MAIN_SITE"
        self.report({"INFO"}, "API Key set successfully!")
        return {"FINISHED"}

class BLENDERMCP_OT_StartServer(bpy.types.Operator):
    bl_idname = "blendermcp.start_server"
    bl_label = "Connect to MCP server" # Updated label
    bl_description = "Start the BlenderMCP server" # Updated description
    def execute(self, context):
        scene = context.scene
        if not hasattr(bpy.types, "blendermcp_server") or not bpy.types.blendermcp_server:
            bpy.types.blendermcp_server = BlenderMCPServer(port=scene.blendermcp_port)
        bpy.types.blendermcp_server.start()
        scene.blendermcp_server_running = True
        return {"FINISHED"}

class BLENDERMCP_OT_StopServer(bpy.types.Operator):
    bl_idname = "blendermcp.stop_server"
    bl_label = "Stop the MCP server" # Updated label
    bl_description = "Stop the BlenderMCP server" # Updated description
    def execute(self, context):
        scene = context.scene
        if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server:
            bpy.types.blendermcp_server.stop()
            del bpy.types.blendermcp_server
        scene.blendermcp_server_running = False
        return {"FINISHED"}

def unregister_backend_setting(): # This function seems unused, might be legacy
    del bpy.types.Scene.mcp_llm_backend

# Registration functions
def register():
    bpy.types.Scene.blendermcp_port = IntProperty(name="Port", description="Port for the BlenderMCP server", default=9876, min=1024, max=65535)
    bpy.types.Scene.mcp_llm_backend = EnumProperty(name="LLM Backend", description="Choose LLM backend", items=[("claude", "Claude", "Use Claude API"),("ollama", "Ollama", "Use Ollama locally")], default="ollama")
    bpy.types.Scene.mcp_claude_model_name = bpy.props.StringProperty(name="Claude Model", description="Name of Claude model to use", default="claude-3-opus-20240229")
    bpy.types.Scene.mcp_ollama_model_name = bpy.props.StringProperty(name="Ollama Model", description="Name of Ollama model to use", default="gemma3:4b")
    bpy.types.Scene.mcp_screenshot_history_limit = bpy.props.IntProperty(name="Screenshot History Limit", description="Max screenshots to keep. 0 for 1.", default=10, min=0)
    bpy.types.Scene.blendermcp_server_running = bpy.props.BoolProperty(name="Server Running", default=False)
    bpy.types.Scene.blendermcp_use_polyhaven = bpy.props.BoolProperty(name="Use Poly Haven", description="Enable Poly Haven asset integration", default=False)
    bpy.types.Scene.blendermcp_use_hyper3d = bpy.props.BoolProperty(name="Use Hyper3D Rodin", description="Enable Hyper3D Rodin generation", default=False)
    bpy.types.Scene.blendermcp_hyper3d_mode = bpy.props.EnumProperty(name="Rodin Mode", description="Choose Rodin API platform", items=[("MAIN_SITE", "hyper3d.ai", "hyper3d.ai"),("FAL_AI", "fal.ai", "fal.ai")], default="MAIN_SITE")
    bpy.types.Scene.blendermcp_hyper3d_api_key = bpy.props.StringProperty(name="Hyper3D API Key", subtype="PASSWORD", description="API Key for Hyper3D", default="")
    bpy.types.Scene.mcp_hyper3d_tier = bpy.props.StringProperty(name="Hyper3D Tier", description="Generation tier (e.g., Sketch, Detailed)", default="Sketch")
    bpy.types.Scene.mcp_hyper3d_mesh_mode = bpy.props.StringProperty(name="Hyper3D Mesh Mode", description="Mesh mode (e.g., Raw, HighPoly)", default="Raw")

    bpy.utils.register_class(BLENDERMCP_PT_Panel)
    bpy.utils.register_class(BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey)
    bpy.utils.register_class(BLENDERMCP_OT_StartServer)
    bpy.utils.register_class(BLENDERMCP_OT_StopServer)
    bpy.utils.register_class(MCP_OT_AskLLMAboutScene) # Register the operator

    print("BlenderMCP addon registered")

def unregister():
    if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server:
        bpy.types.blendermcp_server.stop()
        del bpy.types.blendermcp_server
    bpy.utils.unregister_class(BLENDERMCP_PT_Panel)
    bpy.utils.unregister_class(BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey)
    bpy.utils.unregister_class(BLENDERMCP_OT_StartServer)
    bpy.utils.unregister_class(BLENDERMCP_OT_StopServer)
    bpy.utils.unregister_class(MCP_OT_AskLLMAboutScene) # Unregister the operator

    del bpy.types.Scene.blendermcp_port
    del bpy.types.Scene.blendermcp_server_running
    del bpy.types.Scene.blendermcp_use_polyhaven
    del bpy.types.Scene.blendermcp_use_hyper3d
    del bpy.types.Scene.blendermcp_hyper3d_mode
    del bpy.types.Scene.blendermcp_hyper3d_api_key
    del bpy.types.Scene.mcp_hyper3d_tier
    del bpy.types.Scene.mcp_hyper3d_mesh_mode
    del bpy.types.Scene.mcp_llm_backend
    del bpy.types.Scene.mcp_claude_model_name
    del bpy.types.Scene.mcp_ollama_model_name
    del bpy.types.Scene.mcp_screenshot_history_limit

    print("BlenderMCP addon unregistered")

if __name__ == "__main__":
    register()

RODIN_FREE_TRIAL_KEY = (
    "k9TcfFoEhNd9cCPP2guHAHHHkctZHIRhZDywZ1euGUXwihbYLpOjQhofby80NJez"
)

# --- Screenshot Configuration ---
# Screenshots for history are stored in the user's Blender datafiles directory,
# typically found under: .../Blender/[version]/datafiles/blender_mcp_screenshots/
SCREENSHOT_DIR_PATH = Path(bpy.utils.user_resource('DATAFILES', path="blender_mcp_screenshots"))

def _ensure_screenshot_dir_exists():
    """Ensures the screenshot directory exists."""
    print(f"BlenderMCP: Target screenshot directory: {SCREENSHOT_DIR_PATH}")
    if not SCREENSHOT_DIR_PATH.exists():
        print(f"BlenderMCP: Directory does not exist, attempting to create.")
        os.makedirs(SCREENSHOT_DIR_PATH, exist_ok=True) # exist_ok=True is important
    if SCREENSHOT_DIR_PATH.exists():
        print(f"BlenderMCP: Screenshot directory is accessible.")
    else:
        print(f"BlenderMCP: ERROR - Screenshot directory still does not exist after attempting creation.")

def get_screenshot_filepath():
    """Generates a unique filepath for a new screenshot."""
    _ensure_screenshot_dir_exists()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return SCREENSHOT_DIR_PATH / f"capture_{timestamp}.png"
# --- End Screenshot Configuration ---

# --- Utility Functions for Complex Object Creation ---
# These functions are intended to be callable via the 'execute_code' MCP command,
# allowing an LLM to request the creation of these procedurally generated objects.

def create_modified_cube(name="ModifiedCube", size=2, subdiv_levels=2, bevel_width=0.05, bevel_segments=2, solidify_thickness=0.1, displace_strength=0.2, displace_midlevel=0.5, base_location=(0,0,0)):
    """
    Creates a cube with several modifiers applied for a more complex shape.
    Intended for use by an LLM via the 'execute_code' command.
    Parameters: (Full list in actual code)
    Returns: bpy.types.Object: The created and modified cube object.
    """
    bpy.ops.mesh.primitive_cube_add(size=size, location=base_location)
    obj = bpy.context.object
    obj.name = name
    subdiv_mod = obj.modifiers.new(name="Subdivision", type='SUBSURF')
    subdiv_mod.levels = subdiv_levels
    subdiv_mod.render_levels = subdiv_levels
    bevel_mod = obj.modifiers.new(name="Bevel", type='BEVEL')
    bevel_mod.width = bevel_width
    bevel_mod.segments = bevel_segments
    solidify_mod = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
    solidify_mod.thickness = solidify_thickness
    displace_mod = obj.modifiers.new(name="Displace", type='DISPLACE')
    tex_name = f"{name}_DisplaceTex"
    if tex_name in bpy.data.textures: displace_tex = bpy.data.textures[tex_name]
    else: displace_tex = bpy.data.textures.new(name=tex_name, type='CLOUDS')
    displace_mod.texture = displace_tex
    displace_mod.strength = displace_strength
    displace_mod.mid_level = displace_midlevel
    return obj

def create_voronoi_rock(name="Rock", size=1.0, voronoi_scale=1.0, voronoi_randomness=1.0, subdiv_levels=2, smooth_iterations=5, base_location=(0,0,0)):
    """
    Creates a rock-like object using an IcoSphere and Voronoi displacement.
    Intended for use by an LLM via the 'execute_code' command.
    Parameters: (Full list in actual code)
    Returns: bpy.types.Object: The created rock object.
    """
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=size/2, location=base_location)
    obj = bpy.context.object
    obj.name = name
    displace_mod = obj.modifiers.new(name="Displace", type='DISPLACE')
    tex_name = f"{name}_VoronoiTex"
    if tex_name in bpy.data.textures: voronoi_tex = bpy.data.textures[tex_name]
    else: voronoi_tex = bpy.data.textures.new(name=tex_name, type='VORONOI')
    voronoi_tex.noise_scale = voronoi_scale
    voronoi_tex.intensity = voronoi_randomness
    displace_mod.texture = voronoi_tex
    displace_mod.strength = 1.0
    subdiv_mod = obj.modifiers.new(name="Subdivision", type='SUBSURF')
    subdiv_mod.levels = subdiv_levels
    subdiv_mod.render_levels = subdiv_levels
    smooth_mod = obj.modifiers.new(name="Smooth", type='SMOOTH')
    smooth_mod.iterations = smooth_iterations
    return obj

def create_parametric_gear(name="Gear", teeth=12, radius=1.0, addendum=0.1, dedendum=0.125, bevel_width=0.02, bevel_segments=2, solidify_thickness=0.2, base_location=(0,0,0)):
    """
    Creates a gear-like object. Attempts 'Add Mesh: Extra Objects' addon's gear.
    Falls back to a cylinder placeholder if unavailable/fails.
    Intended for use by an LLM via the 'execute_code' command.
    Parameters: (Full list in actual code)
    Returns: bpy.types.Object: The created gear object or placeholder.
    """
    obj = None
    text_obj = None
    if hasattr(bpy.ops.mesh, 'primitive_gear_add'):
        try:
            bpy.ops.mesh.primitive_gear_add(num_teeth=teeth, radius=radius, addendum=addendum, dedendum=dedendum, base_radius=radius-addendum-dedendum, location=base_location, align='WORLD')
            obj = bpy.context.object
            obj.name = name
        except TypeError as e:
            print(f"Error calling primitive_gear_add: {e}")
            obj = None
    if obj is None:
        print("Add Mesh: Extra Objects (primitive_gear_add) not available/failed. Creating cylinder placeholder.")
        bpy.ops.mesh.primitive_cylinder_add(vertices=teeth*2, radius=radius, depth=solidify_thickness, location=base_location, end_fill_type='NGON')
        obj = bpy.context.object
        obj.name = name
        text_loc = (base_location[0], base_location[1], base_location[2] + radius + 0.2)
        bpy.ops.object.text_add(location=text_loc)
        text_obj = bpy.context.object
        text_obj.data.body = "Gear Placeholder (Extra Objects addon disabled or failed)"
        text_obj.scale = (0.3,0.3,0.3)
        text_obj.parent = obj
    if obj:
        bevel_mod = obj.modifiers.new(name="Bevel", type='BEVEL')
        bevel_mod.width = bevel_width
        bevel_mod.segments = bevel_segments
        bevel_mod.limit_method = 'ANGLE'
        is_2d_profile = True
        if obj.type == 'MESH' and len(obj.data.polygons) > 0:
            verts = [v.co.z for v in obj.data.vertices]
            if verts and (max(verts) - min(verts)) > 0.001: is_2d_profile = False
        if is_2d_profile:
             solidify_mod = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
             solidify_mod.thickness = solidify_thickness
        elif not hasattr(bpy.ops.mesh, 'primitive_gear_add') or text_obj: pass
        else: print(f"Gear '{name}' might have its own thickness. Solidify modifier skipped.")
    return obj

def create_pipe_joint(name="PipeJoint", main_pipe_radius=0.5, main_pipe_length=2.0, branch_pipe_radius=0.3, branch_pipe_length=1.5, branch_angle_degrees=90.0, segments=32, bevel_width=0.05, bevel_segments=3, base_location=(0,0,0)):
    """
    Creates a pipe joint using two cylinders and a boolean union. Main pipe Y-aligned.
    Branch angle 0 for T, 90 for L-junction.
    Intended for use by an LLM via the 'execute_code' command.
    Parameters: (Full list in actual code)
    Returns: bpy.types.Object: The created pipe joint object.
    """
    bpy.ops.mesh.primitive_cylinder_add(vertices=segments, radius=main_pipe_radius, depth=main_pipe_length, location=(base_location[0], base_location[1] + main_pipe_length / 2, base_location[2]), rotation=(math.pi/2, 0, 0))
    main_cyl = bpy.context.object
    main_cyl.name = f"{name}_Main"
    bpy.ops.mesh.primitive_cylinder_add(vertices=segments, radius=branch_pipe_radius, depth=branch_pipe_length, location=(base_location[0], base_location[1] + main_pipe_length / 2, base_location[2] + branch_pipe_length / 2))
    branch_cyl = bpy.context.object
    branch_cyl.name = f"{name}_Branch"
    if math.isclose(branch_angle_degrees, 90.0):
        branch_cyl.location = (base_location[0], base_location[1] + main_pipe_length, base_location[2] + branch_pipe_length / 2)
    elif math.isclose(branch_angle_degrees, 0.0):
        branch_cyl.location = (base_location[0], base_location[1] + main_pipe_length / 2, base_location[2] + main_pipe_radius + branch_pipe_length / 2)
    else:
        branch_cyl.location = (base_location[0], base_location[1] + main_pipe_length / 2, base_location[2] + main_pipe_radius + branch_pipe_length / 2)
        branch_cyl.rotation_euler.rotate_axis('X', math.radians(branch_angle_degrees))
    bpy.context.view_layer.objects.active = main_cyl
    main_cyl.select_set(True)
    branch_cyl.select_set(True)
    bool_mod = main_cyl.modifiers.new(name="BranchUnion", type='BOOLEAN')
    bool_mod.object = branch_cyl
    bool_mod.operation = 'UNION'
    bool_mod.solver = 'FAST'
    try: bpy.ops.object.modifier_apply({'object': main_cyl}, modifier=bool_mod.name)
    except RuntimeError as e:
        print(f"Error applying boolean for {name}: {e}.")
        return main_cyl # Return main object even if boolean fails
    if branch_cyl.name in bpy.data.objects: bpy.data.objects.remove(branch_cyl, do_unlink=True)
    main_cyl.name = name
    bevel_mod = main_cyl.modifiers.new(name="Bevel", type='BEVEL')
    bevel_mod.width = bevel_width
    bevel_mod.segments = bevel_segments
    bevel_mod.limit_method = 'ANGLE'
    return main_cyl

def create_simple_tree(name="SimpleTree", trunk_height=3.0, trunk_radius_bottom=0.3, trunk_radius_top=0.2, canopy_type='sphere', canopy_radius=1.5, canopy_elements=5, canopy_subdivisions=2, base_location=(0,0,0)):
    """
    Creates a simple tree with a tapered trunk and choice of canopy.
    Intended for use by an LLM via the 'execute_code' command.
    Parameters: (Full list in actual code)
    Returns: bpy.types.Object: The main parent object of the tree.
    """
    trunk_location = (base_location[0], base_location[1], base_location[2] + trunk_height / 2)
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=trunk_radius_bottom, radius2=trunk_radius_top, depth=trunk_height, location=trunk_location, end_fill_type='NGON')
    trunk = bpy.context.object
    trunk.name = f"{name}_Trunk"
    canopy_base_z = base_location[2] + trunk_height
    if canopy_type == 'sphere':
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(base_location[0], base_location[1], canopy_base_z))
        canopy_parent = bpy.context.object
        canopy_parent.name = f"{name}_CanopyParent"
        for i in range(canopy_elements):
            offset_radius = canopy_radius * 0.6
            rand_x = base_location[0] + random.uniform(-offset_radius, offset_radius)
            rand_y = base_location[1] + random.uniform(-offset_radius, offset_radius)
            rand_z = canopy_base_z + random.uniform(0, canopy_radius * 0.5)
            current_radius = canopy_radius * random.uniform(0.7, 1.2)
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=canopy_subdivisions, radius=current_radius, location=(rand_x, rand_y, rand_z))
            sphere = bpy.context.object
            sphere.name = f"{name}_CanopySphere_{i+1}"
            displace_mod = sphere.modifiers.new(name="DisplaceCanopy", type='DISPLACE')
            tex_name = f"{name}_CanopyDisplaceTex_{i+1}"
            if tex_name in bpy.data.textures: canopy_displace_tex = bpy.data.textures[tex_name]
            else:
                canopy_displace_tex = bpy.data.textures.new(name=tex_name, type='CLOUDS')
                canopy_displace_tex.noise_scale = current_radius * 0.8
            displace_mod.texture = canopy_displace_tex
            displace_mod.strength = current_radius * 0.2
            sphere.parent = canopy_parent
        canopy_parent.parent = trunk
    elif canopy_type == 'cone_cluster':
        cone_canopy_loc_z = canopy_base_z + canopy_radius * 0.75
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=canopy_radius, radius2=0, depth=canopy_radius*1.5, location=(base_location[0], base_location[1], cone_canopy_loc_z), end_fill_type='NGON')
        cone_canopy = bpy.context.object
        cone_canopy.name = f"{name}_Canopy_Cone"
        cone_canopy.parent = trunk
    trunk.name = name
    bpy.context.view_layer.objects.active = trunk
    trunk.select_set(True)
    return trunk

def create_chain_link(name="ChainLink", link_overall_radius=0.5, link_torus_radius=0.1, main_segments=48, minor_segments=24, base_location=(0,0,0), elongated_scale=(1.5, 1.0, 1.0)):
    """
    Creates a single chain link, potentially elongated, from a torus primitive.
    Intended for use by an LLM via the 'execute_code' command.
    Parameters: (Full list in actual code)
    Returns: bpy.types.Object: The created chain link object.
    """
    bpy.ops.mesh.primitive_torus_add(major_radius=link_overall_radius, minor_radius=link_torus_radius, major_segments=main_segments, minor_segments=minor_segments, location=base_location, align='WORLD')
    link = bpy.context.object
    link.name = name
    link.scale[0] *= elongated_scale[0]
    link.scale[1] *= elongated_scale[1]
    link.scale[2] *= elongated_scale[2]
    if bpy.context.view_layer.objects.active != link:
        bpy.ops.object.select_all(action='DESELECT')
        link.select_set(True)
        bpy.context.view_layer.objects.active = link
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return link

def add_detail_shape(
    target_object_name: str,
    shape_type: str = 'SPHERE',
    operation: str = 'DIFFERENCE',
    shape_size: tuple = (0.2,),
    location: tuple = (0,0,0),
    orientation_euler_degrees: tuple = (0,0,0),
    segments: int = 32
):
    """
    Adds a detail to a target object by creating a primitive shape and
    performing a boolean operation. Intended for use by an LLM via 'execute_code'.
    Parameters: (Full list in actual code)
    Returns: dict: Status dictionary.
    """
    target_obj = bpy.data.objects.get(target_object_name)
    if not target_obj: return {"status": "error", "message": f"Target object '{target_object_name}' not found."}
    if target_obj.type != 'MESH': return {"status": "error", "message": f"Target object '{target_object_name}' is not a mesh."}
    orientation_radians = tuple(math.radians(angle) for angle in orientation_euler_degrees)
    detail_obj = None
    if bpy.context.object_mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    try:
        if shape_type == 'SPHERE':
            if not shape_size or len(shape_size) < 1: return {"status": "error", "message": "shape_size must provide (radius,) for SPHERE."}
            bpy.ops.mesh.primitive_uv_sphere_add(radius=shape_size[0], segments=segments, ring_count=segments // 2, location=location, rotation=orientation_radians)
        elif shape_type == 'CUBE':
            if not shape_size or len(shape_size) < 1: return {"status": "error", "message": "shape_size must provide (size,) for CUBE."}
            bpy.ops.mesh.primitive_cube_add(size=shape_size[0], location=location, rotation=orientation_radians)
        elif shape_type == 'CYLINDER':
            if not shape_size or len(shape_size) < 2: return {"status": "error", "message": "shape_size must provide (radius, depth) for CYLINDER."}
            bpy.ops.mesh.primitive_cylinder_add(radius=shape_size[0], depth=shape_size[1], vertices=segments, location=location, rotation=orientation_radians)
        else: return {"status": "error", "message": f"Unsupported shape_type: '{shape_type}'. Supported: SPHERE, CUBE, CYLINDER."}
        detail_obj = bpy.context.object
        if detail_obj is None: return {"status": "error", "message": "Failed to create detail shape primitive."}
        detail_obj.name = f"{target_object_name}_detail_shape_temp"
    except Exception as e:
        if detail_obj and detail_obj.name in bpy.data.objects: bpy.data.objects.remove(detail_obj, do_unlink=True)
        return {"status": "error", "message": f"Error creating primitive '{shape_type}': {str(e)}"}
    try:
        bpy.ops.object.select_all(action='DESELECT')
        target_obj.select_set(True)
        bpy.context.view_layer.objects.active = target_obj
        bool_mod = target_obj.modifiers.new(name="DetailBoolean", type='BOOLEAN')
        bool_mod.object = detail_obj
        bool_mod.operation = operation
        bool_mod.solver = 'FAST'
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        if detail_obj.name in bpy.data.objects: bpy.data.objects.remove(detail_obj, do_unlink=True)
        return {"status": "success", "message": f"Boolean '{operation}' with shape '{shape_type}' completed on '{target_object_name}'."}
    except Exception as e:
        if detail_obj and detail_obj.name in bpy.data.objects: bpy.data.objects.remove(detail_obj, do_unlink=True)
        return {"status": "error", "message": f"Boolean operation failed: {str(e)}"}
# --- End Utility Functions ---


class BlenderMCPServer:


class BlenderMCPServer:
    def __init__(self, host="localhost", port=9876):
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
                        target=self._handle_client, args=(client,)
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
        buffer = b""

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
                        command = json.loads(buffer.decode("utf-8"))
                        buffer = b""

                        # Execute command in Blender's main thread
                        def execute_wrapper():
                            try:
                                response = self.execute_command(command)
                                response_json = json.dumps(response)
                                try:
                                    client.sendall(response_json.encode("utf-8"))
                                except:
                                    print(
                                        "Failed to send response - client disconnected"
                                    )
                            except Exception as e:
                                print(f"Error executing command: {str(e)}")
                                traceback.print_exc()
                                try:
                                    error_response = {
                                        "status": "error",
                                        "message": str(e),
                                    }
                                    client.sendall(
                                        json.dumps(error_response).encode("utf-8")
                                    )
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

        # Base handlers that are always available
        handlers = {
            "get_scene_info": self.get_scene_info,
            "get_object_info": self.get_object_info,
            "execute_code": self.execute_code,
            "get_polyhaven_status": self.get_polyhaven_status,
            "get_hyper3d_status": self.get_hyper3d_status,
            "import_model_from_path": self.import_model_from_path,
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
            polyhaven_handlers = {
                "create_rodin_job": self.create_rodin_job,
                "poll_rodin_job_status": self.poll_rodin_job_status,
                "import_generated_asset": self.import_generated_asset,
            }
            handlers.update(polyhaven_handlers)

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
                    "location": [
                        round(float(obj.location.x), 2),
                        round(float(obj.location.y), 2),
                        round(float(obj.location.z), 2),
                    ],
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
        """Returns the world-space axis-aligned bounding box (AABB) of an object."""
        if obj.type != "MESH":
            raise TypeError("Object must be a mesh")

        # Get the bounding box corners in local space
        local_bbox_corners = [mathutils.Vector(corner) for corner in obj.bound_box]

        # Convert to world coordinates
        world_bbox_corners = [
            obj.matrix_world @ corner for corner in local_bbox_corners
        ]

        # Compute axis-aligned min/max coordinates
        min_corner = mathutils.Vector(map(min, zip(*world_bbox_corners)))
        max_corner = mathutils.Vector(map(max, zip(*world_bbox_corners)))

        return [[*min_corner], [*max_corner]]

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
            "rotation": [
                obj.rotation_euler.x,
                obj.rotation_euler.y,
                obj.rotation_euler.z,
            ],
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
        if obj.type == "MESH" and obj.data:
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
            namespace = {
                "bpy": bpy,
                "create_modified_cube": create_modified_cube,
                "create_voronoi_rock": create_voronoi_rock,
                "create_parametric_gear": create_parametric_gear,
                "create_pipe_joint": create_pipe_joint,
                "create_simple_tree": create_simple_tree,
                "create_chain_link": create_chain_link,
                "add_detail_shape": add_detail_shape
            }

            # Capture stdout during execution, and return it as result
            capture_buffer = io.StringIO()
            with redirect_stdout(capture_buffer):
                exec(code, namespace)

            captured_output = capture_buffer.getvalue()
            return {"executed": True, "result": captured_output}
        except Exception as e:
            raise Exception(f"Code execution error: {str(e)}")

    def get_polyhaven_categories(self, asset_type):
        """Get categories for a specific asset type from Polyhaven"""
        try:
            if asset_type not in ["hdris", "textures", "models", "all"]:
                return {
                    "error": f"Invalid asset type: {asset_type}. Must be one of: hdris, textures, models, all"
                }

            response = requests.get(
                f"https://api.polyhaven.com/categories/{asset_type}"
            )
            if response.status_code == 200:
                return {"categories": response.json()}
            else:
                return {
                    "error": f"API request failed with status code {response.status_code}"
                }
        except Exception as e:
            return {"error": str(e)}

    def search_polyhaven_assets(self, asset_type=None, categories=None):
        """Search for assets from Polyhaven with optional filtering"""
        try:
            url = "https://api.polyhaven.com/assets"
            params = {}

            if asset_type and asset_type != "all":
                if asset_type not in ["hdris", "textures", "models"]:
                    return {
                        "error": f"Invalid asset type: {asset_type}. Must be one of: hdris, textures, models, all"
                    }
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

                return {
                    "assets": limited_assets,
                    "total_count": len(assets),
                    "returned_count": len(limited_assets),
                }
            else:
                return {
                    "error": f"API request failed with status code {response.status_code}"
                }
        except Exception as e:
            return {"error": str(e)}

    def download_polyhaven_asset(
        self, asset_id, asset_type, resolution="1k", file_format=None
    ):
        try:
            # First get the files information
            files_response = requests.get(f"https://api.polyhaven.com/files/{asset_id}")
            if files_response.status_code != 200:
                return {
                    "error": f"Failed to get asset files: {files_response.status_code}"
                }

            files_data = files_response.json()

            # Handle different asset types
            if asset_type == "hdris":
                # For HDRIs, download the .hdr or .exr file
                if not file_format:
                    file_format = "hdr"  # Default format for HDRIs

                if (
                    "hdri" in files_data
                    and resolution in files_data["hdri"]
                    and file_format in files_data["hdri"][resolution]
                ):
                    file_info = files_data["hdri"][resolution][file_format]
                    file_url = file_info["url"]

                    # For HDRIs, we need to save to a temporary file first
                    # since Blender can't properly load HDR data directly from memory
                    with tempfile.NamedTemporaryFile(
                        suffix=f".{file_format}", delete=False
                    ) as tmp_file:
                        # Download the file
                        response = requests.get(file_url)
                        if response.status_code != 200:
                            return {
                                "error": f"Failed to download HDRI: {response.status_code}"
                            }

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
                        tex_coord = node_tree.nodes.new(type="ShaderNodeTexCoord")
                        tex_coord.location = (-800, 0)

                        mapping = node_tree.nodes.new(type="ShaderNodeMapping")
                        mapping.location = (-600, 0)

                        # Load the image from the temporary file
                        env_tex = node_tree.nodes.new(type="ShaderNodeTexEnvironment")
                        env_tex.location = (-400, 0)
                        env_tex.image = bpy.data.images.load(tmp_path)

                        # Use a color space that exists in all Blender versions
                        if file_format.lower() == "exr":
                            # Try to use Linear color space for EXR files
                            try:
                                env_tex.image.colorspace_settings.name = "Linear"
                            except:
                                # Fallback to Non-Color if Linear isn't available
                                env_tex.image.colorspace_settings.name = "Non-Color"
                        else:  # hdr
                            # For HDR files, try these options in order
                            for color_space in [
                                "Linear",
                                "Linear Rec.709",
                                "Non-Color",
                            ]:
                                try:
                                    env_tex.image.colorspace_settings.name = color_space
                                    break  # Stop if we successfully set a color space
                                except:
                                    continue

                        background = node_tree.nodes.new(type="ShaderNodeBackground")
                        background.location = (-200, 0)

                        output = node_tree.nodes.new(type="ShaderNodeOutputWorld")
                        output.location = (0, 0)

                        # Connect nodes
                        node_tree.links.new(
                            tex_coord.outputs["Generated"], mapping.inputs["Vector"]
                        )
                        node_tree.links.new(
                            mapping.outputs["Vector"], env_tex.inputs["Vector"]
                        )
                        node_tree.links.new(
                            env_tex.outputs["Color"], background.inputs["Color"]
                        )
                        node_tree.links.new(
                            background.outputs["Background"], output.inputs["Surface"]
                        )

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
                            "image_name": env_tex.image.name,
                        }
                    except Exception as e:
                        return {"error": f"Failed to set up HDRI in Blender: {str(e)}"}
                else:
                    return {
                        "error": f"Requested resolution or format not available for this HDRI"
                    }

            elif asset_type == "textures":
                if not file_format:
                    file_format = "jpg"  # Default format for textures

                downloaded_maps = {}

                try:
                    for map_type in files_data:
                        if map_type not in ["blend", "gltf"]:  # Skip non-texture files
                            if (
                                resolution in files_data[map_type]
                                and file_format in files_data[map_type][resolution]
                            ):
                                file_info = files_data[map_type][resolution][
                                    file_format
                                ]
                                file_url = file_info["url"]

                                # Use NamedTemporaryFile like we do for HDRIs
                                with tempfile.NamedTemporaryFile(
                                    suffix=f".{file_format}", delete=False
                                ) as tmp_file:
                                    # Download the file
                                    response = requests.get(file_url)
                                    if response.status_code == 200:
                                        tmp_file.write(response.content)
                                        tmp_path = tmp_file.name

                                        # Load image from temporary file
                                        image = bpy.data.images.load(tmp_path)
                                        image.name = (
                                            f"{asset_id}_{map_type}.{file_format}"
                                        )

                                        # Pack the image into .blend file
                                        image.pack()

                                        # Set color space based on map type
                                        if map_type in ["color", "diffuse", "albedo"]:
                                            try:
                                                image.colorspace_settings.name = "sRGB"
                                            except:
                                                pass
                                        else:
                                            try:
                                                image.colorspace_settings.name = (
                                                    "Non-Color"
                                                )
                                            except:
                                                pass

                                        downloaded_maps[map_type] = image

                                        # Clean up temporary file
                                        try:
                                            os.unlink(tmp_path)
                                        except:
                                            pass

                    if not downloaded_maps:
                        return {
                            "error": f"No texture maps found for the requested resolution and format"
                        }

                    # Create a new material with the downloaded textures
                    mat = bpy.data.materials.new(name=asset_id)
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes
                    links = mat.node_tree.links

                    # Clear default nodes
                    for node in nodes:
                        nodes.remove(node)

                    # Create output node
                    output = nodes.new(type="ShaderNodeOutputMaterial")
                    output.location = (300, 0)

                    # Create principled BSDF node
                    principled = nodes.new(type="ShaderNodeBsdfPrincipled")
                    principled.location = (0, 0)
                    links.new(principled.outputs[0], output.inputs[0])

                    # Add texture nodes based on available maps
                    tex_coord = nodes.new(type="ShaderNodeTexCoord")
                    tex_coord.location = (-800, 0)

                    mapping = nodes.new(type="ShaderNodeMapping")
                    mapping.location = (-600, 0)
                    mapping.vector_type = (
                        "TEXTURE"  # Changed from default 'POINT' to 'TEXTURE'
                    )
                    links.new(tex_coord.outputs["UV"], mapping.inputs["Vector"])

                    # Position offset for texture nodes
                    x_pos = -400
                    y_pos = 300

                    # Connect different texture maps
                    for map_type, image in downloaded_maps.items():
                        tex_node = nodes.new(type="ShaderNodeTexImage")
                        tex_node.location = (x_pos, y_pos)
                        tex_node.image = image

                        # Set color space based on map type
                        if map_type.lower() in ["color", "diffuse", "albedo"]:
                            try:
                                tex_node.image.colorspace_settings.name = "sRGB"
                            except:
                                pass  # Use default if sRGB not available
                        else:
                            try:
                                tex_node.image.colorspace_settings.name = "Non-Color"
                            except:
                                pass  # Use default if Non-Color not available

                        links.new(mapping.outputs["Vector"], tex_node.inputs["Vector"])

                        # Connect to appropriate input on Principled BSDF
                        if map_type.lower() in ["color", "diffuse", "albedo"]:
                            links.new(
                                tex_node.outputs["Color"],
                                principled.inputs["Base Color"],
                            )
                        elif map_type.lower() in ["roughness", "rough"]:
                            links.new(
                                tex_node.outputs["Color"],
                                principled.inputs["Roughness"],
                            )
                        elif map_type.lower() in ["metallic", "metalness", "metal"]:
                            links.new(
                                tex_node.outputs["Color"], principled.inputs["Metallic"]
                            )
                        elif map_type.lower() in ["normal", "nor"]:
                            # Add normal map node
                            normal_map = nodes.new(type="ShaderNodeNormalMap")
                            normal_map.location = (x_pos + 200, y_pos)
                            links.new(
                                tex_node.outputs["Color"], normal_map.inputs["Color"]
                            )
                            links.new(
                                normal_map.outputs["Normal"],
                                principled.inputs["Normal"],
                            )
                        elif map_type in ["displacement", "disp", "height"]:
                            # Add displacement node
                            disp_node = nodes.new(type="ShaderNodeDisplacement")
                            disp_node.location = (x_pos + 200, y_pos - 200)
                            links.new(
                                tex_node.outputs["Color"], disp_node.inputs["Height"]
                            )
                            links.new(
                                disp_node.outputs["Displacement"],
                                output.inputs["Displacement"],
                            )

                        y_pos -= 250

                    return {
                        "success": True,
                        "message": f"Texture {asset_id} imported as material",
                        "material": mat.name,
                        "maps": list(downloaded_maps.keys()),
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
                            return {
                                "error": f"Failed to download model: {response.status_code}"
                            }

                        with open(main_file_path, "wb") as f:
                            f.write(response.content)

                        # Check for included files and download them
                        if "include" in file_info and file_info["include"]:
                            for include_path, include_info in file_info[
                                "include"
                            ].items():
                                # Get the URL for the included file - this is the fix
                                include_url = include_info["url"]

                                # Create the directory structure for the included file
                                include_file_path = os.path.join(temp_dir, include_path)
                                os.makedirs(
                                    os.path.dirname(include_file_path), exist_ok=True
                                )

                                # Download the included file
                                include_response = requests.get(include_url)
                                if include_response.status_code == 200:
                                    with open(include_file_path, "wb") as f:
                                        f.write(include_response.content)
                                else:
                                    print(
                                        f"Failed to download included file: {include_path}"
                                    )

                        # Import the model into Blender
                        if file_format == "gltf" or file_format == "glb":
                            bpy.ops.import_scene.gltf(filepath=main_file_path)
                        elif file_format == "fbx":
                            bpy.ops.import_scene.fbx(filepath=main_file_path)
                        elif file_format == "obj":
                            bpy.ops.import_scene.obj(filepath=main_file_path)
                        elif file_format == "blend":
                            # For blend files, we need to append or link
                            with bpy.data.libraries.load(
                                main_file_path, link=False
                            ) as (data_from, data_to):
                                data_to.objects = data_from.objects

                            # Link the objects to the scene
                            for obj in data_to.objects:
                                if obj is not None:
                                    bpy.context.collection.objects.link(obj)
                        else:
                            return {"error": f"Unsupported model format: {file_format}"}

                        # Get the names of imported objects
                        imported_objects = [
                            obj.name for obj in bpy.context.selected_objects
                        ]

                        return {
                            "success": True,
                            "message": f"Model {asset_id} imported successfully",
                            "imported_objects": imported_objects,
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
                    return {
                        "error": f"Requested format or resolution not available for this model"
                    }

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
            if not hasattr(obj, "data") or not hasattr(obj.data, "materials"):
                return {"error": f"Object {object_name} cannot accept materials"}

            # Find all images related to this texture and ensure they're properly loaded
            texture_images = {}
            for img in bpy.data.images:
                if img.name.startswith(texture_id + "_"):
                    # Extract the map type from the image name
                    map_type = img.name.split("_")[-1].split(".")[0]

                    # Force a reload of the image
                    img.reload()

                    # Ensure proper color space
                    if map_type.lower() in ["color", "diffuse", "albedo"]:
                        try:
                            img.colorspace_settings.name = "sRGB"
                        except:
                            pass
                    else:
                        try:
                            img.colorspace_settings.name = "Non-Color"
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
                return {
                    "error": f"No texture images found for: {texture_id}. Please download the texture first."
                }

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
            output = nodes.new(type="ShaderNodeOutputMaterial")
            output.location = (600, 0)

            # Create principled BSDF node
            principled = nodes.new(type="ShaderNodeBsdfPrincipled")
            principled.location = (300, 0)
            links.new(principled.outputs[0], output.inputs[0])

            # Add texture nodes based on available maps
            tex_coord = nodes.new(type="ShaderNodeTexCoord")
            tex_coord.location = (-800, 0)

            mapping = nodes.new(type="ShaderNodeMapping")
            mapping.location = (-600, 0)
            mapping.vector_type = "TEXTURE"  # Changed from default 'POINT' to 'TEXTURE'
            links.new(tex_coord.outputs["UV"], mapping.inputs["Vector"])

            # Position offset for texture nodes
            x_pos = -400
            y_pos = 300

            # Connect different texture maps
            for map_type, image in texture_images.items():
                tex_node = nodes.new(type="ShaderNodeTexImage")
                tex_node.location = (x_pos, y_pos)
                tex_node.image = image

                # Set color space based on map type
                if map_type.lower() in ["color", "diffuse", "albedo"]:
                    try:
                        tex_node.image.colorspace_settings.name = "sRGB"
                    except:
                        pass  # Use default if sRGB not available
                else:
                    try:
                        tex_node.image.colorspace_settings.name = "Non-Color"
                    except:
                        pass  # Use default if Non-Color not available

                links.new(mapping.outputs["Vector"], tex_node.inputs["Vector"])

                # Connect to appropriate input on Principled BSDF
                if map_type.lower() in ["color", "diffuse", "albedo"]:
                    links.new(
                        tex_node.outputs["Color"], principled.inputs["Base Color"]
                    )
                elif map_type.lower() in ["roughness", "rough"]:
                    links.new(tex_node.outputs["Color"], principled.inputs["Roughness"])
                elif map_type.lower() in ["metallic", "metalness", "metal"]:
                    links.new(tex_node.outputs["Color"], principled.inputs["Metallic"])
                elif map_type.lower() in ["normal", "nor", "dx", "gl"]:
                    # Add normal map node
                    normal_map = nodes.new(type="ShaderNodeNormalMap")
                    normal_map.location = (x_pos + 200, y_pos)
                    links.new(tex_node.outputs["Color"], normal_map.inputs["Color"])
                    links.new(normal_map.outputs["Normal"], principled.inputs["Normal"])
                elif map_type.lower() in ["displacement", "disp", "height"]:
                    # Add displacement node
                    disp_node = nodes.new(type="ShaderNodeDisplacement")
                    disp_node.location = (x_pos + 200, y_pos - 200)
                    disp_node.inputs["Scale"].default_value = (
                        0.1  # Reduce displacement strength
                    )
                    links.new(tex_node.outputs["Color"], disp_node.inputs["Height"])
                    links.new(
                        disp_node.outputs["Displacement"], output.inputs["Displacement"]
                    )

                y_pos -= 250

            # Second pass: Connect nodes with proper handling for special cases
            texture_nodes = {}

            # First find all texture nodes and store them by map type
            for node in nodes:
                if node.type == "TEX_IMAGE" and node.image:
                    for map_type, image in texture_images.items():
                        if node.image == image:
                            texture_nodes[map_type] = node
                            break

            # Now connect everything using the nodes instead of images
            # Handle base color (diffuse)
            for map_name in ["color", "diffuse", "albedo"]:
                if map_name in texture_nodes:
                    links.new(
                        texture_nodes[map_name].outputs["Color"],
                        principled.inputs["Base Color"],
                    )
                    print(f"Connected {map_name} to Base Color")
                    break

            # Handle roughness
            for map_name in ["roughness", "rough"]:
                if map_name in texture_nodes:
                    links.new(
                        texture_nodes[map_name].outputs["Color"],
                        principled.inputs["Roughness"],
                    )
                    print(f"Connected {map_name} to Roughness")
                    break

            # Handle metallic
            for map_name in ["metallic", "metalness", "metal"]:
                if map_name in texture_nodes:
                    links.new(
                        texture_nodes[map_name].outputs["Color"],
                        principled.inputs["Metallic"],
                    )
                    print(f"Connected {map_name} to Metallic")
                    break

            # Handle normal maps
            for map_name in ["gl", "dx", "nor"]:
                if map_name in texture_nodes:
                    normal_map_node = nodes.new(type="ShaderNodeNormalMap")
                    normal_map_node.location = (100, 100)
                    links.new(
                        texture_nodes[map_name].outputs["Color"],
                        normal_map_node.inputs["Color"],
                    )
                    links.new(
                        normal_map_node.outputs["Normal"], principled.inputs["Normal"]
                    )
                    print(f"Connected {map_name} to Normal")
                    break

            # Handle displacement
            for map_name in ["displacement", "disp", "height"]:
                if map_name in texture_nodes:
                    disp_node = nodes.new(type="ShaderNodeDisplacement")
                    disp_node.location = (300, -200)
                    disp_node.inputs["Scale"].default_value = (
                        0.1  # Reduce displacement strength
                    )
                    links.new(
                        texture_nodes[map_name].outputs["Color"],
                        disp_node.inputs["Height"],
                    )
                    links.new(
                        disp_node.outputs["Displacement"], output.inputs["Displacement"]
                    )
                    print(f"Connected {map_name} to Displacement")
                    break

            # Handle ARM texture (Ambient Occlusion, Roughness, Metallic)
            if "arm" in texture_nodes:
                separate_rgb = nodes.new(type="ShaderNodeSeparateRGB")
                separate_rgb.location = (-200, -100)
                links.new(
                    texture_nodes["arm"].outputs["Color"], separate_rgb.inputs["Image"]
                )

                # Connect Roughness (G) if no dedicated roughness map
                if not any(
                    map_name in texture_nodes for map_name in ["roughness", "rough"]
                ):
                    links.new(separate_rgb.outputs["G"], principled.inputs["Roughness"])
                    print("Connected ARM.G to Roughness")

                # Connect Metallic (B) if no dedicated metallic map
                if not any(
                    map_name in texture_nodes
                    for map_name in ["metallic", "metalness", "metal"]
                ):
                    links.new(separate_rgb.outputs["B"], principled.inputs["Metallic"])
                    print("Connected ARM.B to Metallic")

                # For AO (R channel), multiply with base color if we have one
                base_color_node = None
                for map_name in ["color", "diffuse", "albedo"]:
                    if map_name in texture_nodes:
                        base_color_node = texture_nodes[map_name]
                        break

                if base_color_node:
                    mix_node = nodes.new(type="ShaderNodeMixRGB")
                    mix_node.location = (100, 200)
                    mix_node.blend_type = "MULTIPLY"
                    mix_node.inputs["Fac"].default_value = 0.8  # 80% influence

                    # Disconnect direct connection to base color
                    for link in base_color_node.outputs["Color"].links:
                        if link.to_socket == principled.inputs["Base Color"]:
                            links.remove(link)

                    # Connect through the mix node
                    links.new(base_color_node.outputs["Color"], mix_node.inputs[1])
                    links.new(separate_rgb.outputs["R"], mix_node.inputs[2])
                    links.new(
                        mix_node.outputs["Color"], principled.inputs["Base Color"]
                    )
                    print("Connected ARM.R to AO mix with Base Color")

            # Handle AO (Ambient Occlusion) if separate
            if "ao" in texture_nodes:
                base_color_node = None
                for map_name in ["color", "diffuse", "albedo"]:
                    if map_name in texture_nodes:
                        base_color_node = texture_nodes[map_name]
                        break

                if base_color_node:
                    mix_node = nodes.new(type="ShaderNodeMixRGB")
                    mix_node.location = (100, 200)
                    mix_node.blend_type = "MULTIPLY"
                    mix_node.inputs["Fac"].default_value = 0.8  # 80% influence

                    # Disconnect direct connection to base color
                    for link in base_color_node.outputs["Color"].links:
                        if link.to_socket == principled.inputs["Base Color"]:
                            links.remove(link)

                    # Connect through the mix node
                    links.new(base_color_node.outputs["Color"], mix_node.inputs[1])
                    links.new(texture_nodes["ao"].outputs["Color"], mix_node.inputs[2])
                    links.new(
                        mix_node.outputs["Color"], principled.inputs["Base Color"]
                    )
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
                "texture_nodes": [],
            }

            for node in new_mat.node_tree.nodes:
                if node.type == "TEX_IMAGE" and node.image:
                    connections = []
                    for output in node.outputs:
                        for link in output.links:
                            connections.append(
                                f"{output.name} → {link.to_node.name}.{link.to_socket.name}"
                            )

                    material_info["texture_nodes"].append(
                        {
                            "name": node.name,
                            "image": node.image.name,
                            "colorspace": node.image.colorspace_settings.name,
                            "connections": connections,
                        }
                    )

            return {
                "success": True,
                "message": f"Created new material and applied texture {texture_id} to {object_name}",
                "material": new_mat.name,
                "maps": texture_maps,
                "material_info": material_info,
            }

        except Exception as e:
            print(f"Error in set_texture: {str(e)}")
            traceback.print_exc()
            return {"error": f"Failed to apply texture: {str(e)}"}

    def get_polyhaven_status(self):
        """Get the current status of PolyHaven integration"""
        enabled = bpy.context.scene.blendermcp_use_polyhaven
        if enabled:
            return {
                "enabled": True,
                "message": "PolyHaven integration is enabled and ready to use.",
            }
        else:
            return {
                "enabled": False,
                "message": """PolyHaven integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the BlenderMCP panel in the sidebar (press N if hidden)
                            2. Check the 'Use assets from Poly Haven' checkbox
                            3. Restart the connection to Claude""",
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
                                4. Restart the connection to Claude""",
                }
            mode = bpy.context.scene.blendermcp_hyper3d_mode
            message = (
                f"Hyper3D Rodin integration is enabled and ready to use. Mode: {mode}. "
                + f"Key type: {'private' if bpy.context.scene.blendermcp_hyper3d_api_key != RODIN_FREE_TRIAL_KEY else 'free_trial'}"
            )
            return {"enabled": True, "message": message}
        else:
            return {
                "enabled": False,
                "message": """Hyper3D Rodin integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the BlenderMCP panel in the sidebar (press N if hidden)
                            2. Check the 'Use Hyper3D Rodin 3D model generation' checkbox
                            3. Restart the connection to Claude""",
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
        bbox_condition=None,
    ):
        try:
            if images is None:
                images = []
            """Call Rodin API, get the job uuid and subscription key"""
            files = [
                *[
                    ("images", (f"{i:04d}{img_suffix}", img))
                    for i, (img_suffix, img) in enumerate(images)
                ],
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
                files=files,
            )
            data = response.json()
            return data
        except Exception as e:
            return {"error": str(e)}

    def create_rodin_job_fal_ai(
        self,
        text_prompt: str = None,
        images: list[tuple[str, str]] = None,
        bbox_condition=None,
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
                json=req_data,
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
        return {"status_list": [i["status"] for i in data["jobs"]]}

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

        if len(imported_objects) == 1 and imported_objects[0].type == "MESH":
            mesh_obj = imported_objects[0]
            print("Single mesh imported, no cleanup needed.")
        else:
            if len(imported_objects) == 2:
                empty_objs = [i for i in imported_objects if i.type == "EMPTY"]
                if len(empty_objs) != 1:
                    print(
                        "Error: Expected an empty node with one mesh child or a single mesh object."
                    )
                    return
                parent_obj = empty_objs.pop()
                if len(parent_obj.children) == 1:
                    potential_mesh = parent_obj.children[0]
                    if potential_mesh.type == "MESH":
                        print(
                            "GLB structure confirmed: Empty node with one mesh child."
                        )

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
                    print(
                        "Error: Expected an empty node with one mesh child or a single mesh object."
                    )
                    return
            else:
                print(
                    "Error: Expected an empty node with one mesh child or a single mesh object."
                )
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
            json={"task_uuid": task_uuid},
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
        else:
            return {
                "succeed": False,
                "error": "Generation failed. Please first make sure that all jobs of the task are done and then try again later.",
            }

        try:
            obj = self._clean_imported_glb(filepath=temp_file.name, mesh_name=name)
            result = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "rotation": [
                    obj.rotation_euler.x,
                    obj.rotation_euler.y,
                    obj.rotation_euler.z,
                ],
                "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            }

            if obj.type == "MESH":
                bounding_box = self._get_aabb(obj)
                result["world_bounding_box"] = bounding_box

            return {"succeed": True, **result}
        except Exception as e:
            return {"succeed": False, "error": str(e)}

    def import_generated_asset_fal_ai(self, request_id: str, name: str):
        """Fetch the generated asset, import into blender"""
        response = requests.get(
            f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}",
            headers={
                "Authorization": f"Key {bpy.context.scene.blendermcp_hyper3d_api_key}",
            },
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
            obj = self._clean_imported_glb(filepath=temp_file.name, mesh_name=name)
            result = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "rotation": [
                    obj.rotation_euler.x,
                    obj.rotation_euler.y,
                    obj.rotation_euler.z,
                ],
                "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            }

            if obj.type == "MESH":
                bounding_box = self._get_aabb(obj)
                result["world_bounding_box"] = bounding_box

            return {"succeed": True, **result}
        except Exception as e:
            return {"succeed": False, "error": str(e)}

    def import_model_from_path(self, path: str):

        if not os.path.exists(path):
            raise FileNotFoundError(f"File does not exist: {path}")

        ext = os.path.splitext(path)[1].lower()
        supported = [".obj", ".fbx", ".glb", ".gltf", ".blend"]
        if ext not in supported:
            raise ValueError(f"Unsupported file extension: {ext}")

        # Import based on file type
        if ext == ".obj":
            bpy.ops.import_scene.obj(filepath=path)
        elif ext == ".fbx":
            bpy.ops.import_scene.fbx(filepath=path)
        elif ext in [".glb", ".gltf"]:
            bpy.ops.import_scene.gltf(filepath=path)
        elif ext == ".blend":
            with bpy.data.libraries.load(path, link=False) as (data_from, data_to):
                data_to.objects = data_from.objects

            for obj in data_to.objects:
                if obj is not None:
                    bpy.context.collection.objects.link(obj)

        return {"imported_file": path, "type": ext}

    # endregion


# Blender UI Panel
class BLENDERMCP_PT_Panel(bpy.types.Panel):
    bl_label = "Blender MCP"
    bl_idname = "BLENDERMCP_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderMCP"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "blendermcp_port")
        layout.prop(
            scene, "blendermcp_use_polyhaven", text="Use assets from Poly Haven"
        )

        layout.prop(
            scene,
            "blendermcp_use_hyper3d",
            text="Use Hyper3D Rodin 3D model generation",
        )
        if scene.blendermcp_use_hyper3d:
            layout.prop(scene, "blendermcp_hyper3d_mode", text="Rodin Mode")
            layout.prop(scene, "blendermcp_hyper3d_api_key", text="API Key")
            layout.operator(
                "blendermcp.set_hyper3d_free_trial_api_key",
                text="Set Free Trial API Key",
            )

        layout.prop(context.scene, "mcp_llm_backend", text="LLM Backend")

        if scene.mcp_llm_backend == "claude":
            layout.prop(scene, "mcp_claude_model_name", text="Claude Model")
        elif scene.mcp_llm_backend == "ollama":
            layout.prop(scene, "mcp_ollama_model_name", text="Ollama Model")

        layout.separator()
        layout.operator("mcp.ask_llm_about_scene", text="Ask LLM About Scene")
        layout.separator()

        if not scene.blendermcp_server_running:
            layout.operator("blendermcp.start_server", text="Connect to MCP server")
        else:
            layout.operator("blendermcp.stop_server", text="Disconnect from MCP server")
            layout.label(text=f"Running on port {scene.blendermcp_port}")


def render_and_save_image(filepath="/tmp/blender_mcp_view.png"):
    bpy.context.scene.render.filepath = filepath
    bpy.ops.render.opengl(write_still=True)
    return filepath


def extract_scene_summary():
    summary = []
    for obj in bpy.data.objects:
        summary.append(
            f"{obj.name}: {obj.type}, Location: {obj.location}, Visible: {obj.visible_get()}"
        )
    return "\n".join(summary)


class MCP_OT_AskLLMAboutScene(bpy.types.Operator):
    bl_idname = "mcp.ask_llm_about_scene"
    bl_label = "Ask LLM About Scene"

    def execute(self, context):
        from .llm_handler import query_llm

        image_path = render_and_save_image()
        metadata = extract_scene_summary()
        backend = context.scene.mcp_llm_backend

        response = query_llm(backend=backend, image_path=image_path, metadata=metadata)

        self.report({"INFO"}, response[:400])
        print("LLM Response:", response)
        return {"FINISHED"}


# Operator to set Hyper3D API Key
class BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey(bpy.types.Operator):
    bl_idname = "blendermcp.set_hyper3d_free_trial_api_key"
    bl_label = "Set Free Trial API Key"

    def execute(self, context):
        context.scene.blendermcp_hyper3d_api_key = RODIN_FREE_TRIAL_KEY
        context.scene.blendermcp_hyper3d_mode = "MAIN_SITE"
        self.report({"INFO"}, "API Key set successfully!")
        return {"FINISHED"}


# Operator to start the server
class BLENDERMCP_OT_StartServer(bpy.types.Operator):
    bl_idname = "blendermcp.start_server"
    bl_label = "Connect to Claude"
    bl_description = "Start the BlenderMCP server to connect with Claude"

    def execute(self, context):
        scene = context.scene

        # Create a new server instance
        if (
            not hasattr(bpy.types, "blendermcp_server")
            or not bpy.types.blendermcp_server
        ):
            bpy.types.blendermcp_server = BlenderMCPServer(port=scene.blendermcp_port)

        # Start the server
        bpy.types.blendermcp_server.start()
        scene.blendermcp_server_running = True

        return {"FINISHED"}


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

        return {"FINISHED"}


def unregister_backend_setting():
    del bpy.types.Scene.mcp_llm_backend


# Registration functions
def register():
    bpy.types.Scene.blendermcp_port = IntProperty(
        name="Port",
        description="Port for the BlenderMCP server",
        default=9876,
        min=1024,
        max=65535,
    )

    bpy.types.Scene.mcp_llm_backend = EnumProperty(
        name="LLM Backend",
        description="Choose LLM backend",
        items=[
            ("claude", "Claude", "Use Claude API"),
            ("ollama", "Ollama", "Use Ollama locally"),
        ],
        default="ollama",
    )

    bpy.types.Scene.mcp_claude_model_name = bpy.props.StringProperty(
        name="Claude Model",
        description="Name of Claude model to use (e.g., claude-3-opus-20240229)",
        default="claude-3-opus-20240229",
    )

    bpy.types.Scene.mcp_ollama_model_name = bpy.props.StringProperty(
        name="Ollama Model",
        description="Name of Ollama model to use (e.g., llama3, stablelm-zephyr)",
        default="gemma3:4b",
    )

    bpy.types.Scene.blendermcp_server_running = bpy.props.BoolProperty(
        name="Server Running", default=False
    )

    bpy.types.Scene.blendermcp_use_polyhaven = bpy.props.BoolProperty(
        name="Use Poly Haven",
        description="Enable Poly Haven asset integration",
        default=False,
    )

    bpy.types.Scene.blendermcp_use_hyper3d = bpy.props.BoolProperty(
        name="Use Hyper3D Rodin",
        description="Enable Hyper3D Rodin generatino integration",
        default=False,
    )

    bpy.types.Scene.blendermcp_hyper3d_mode = bpy.props.EnumProperty(
        name="Rodin Mode",
        description="Choose the platform used to call Rodin APIs",
        items=[
            ("MAIN_SITE", "hyper3d.ai", "hyper3d.ai"),
            ("FAL_AI", "fal.ai", "fal.ai"),
        ],
        default="MAIN_SITE",
    )

    bpy.types.Scene.blendermcp_hyper3d_api_key = bpy.props.StringProperty(
        name="Hyper3D API Key",
        subtype="PASSWORD",
        description="API Key provided by Hyper3D",
        default="",
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
    del bpy.types.Scene.blendermcp_hyper3d_mode
    del bpy.types.Scene.blendermcp_hyper3d_api_key

    del bpy.types.Scene.mcp_llm_backend
    del bpy.types.Scene.mcp_claude_model_name
    del bpy.types.Scene.mcp_ollama_model_name

    print("BlenderMCP addon unregistered")


if __name__ == "__main__":
    register()
