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
from datetime import datetime
import math
import random
