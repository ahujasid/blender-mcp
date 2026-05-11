# Code created by Siddharth Ahuja: www.github.com/ahujasid (c) 2025
# Refocused for STL print-prep workflow.

import bpy
import bmesh
import mathutils
import json
import threading
import socket
import time
import traceback
import io
import os
from bpy.props import IntProperty, BoolProperty
from contextlib import redirect_stdout

bl_info = {
    "name": "Blender MCP (Print Prep)",
    "author": "BlenderMCP",
    "version": (1, 3),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > BlenderMCP",
    "description": "Connect Blender to Claude via MCP for STL print-prep workflow",
    "category": "Interface",
}


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
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        if self.server_thread:
            try:
                if self.server_thread.is_alive():
                    self.server_thread.join(timeout=1.0)
            except:
                pass
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
                except socket.timeout:
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
        print("Client handler started")
        client.settimeout(None)
        buffer = b''
        try:
            while self.running:
                try:
                    data = client.recv(8192)
                    if not data:
                        print("Client disconnected")
                        break
                    buffer += data
                    try:
                        command = json.loads(buffer.decode('utf-8'))
                        buffer = b''

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
                                    error_response = {"status": "error", "message": str(e)}
                                    client.sendall(json.dumps(error_response).encode('utf-8'))
                                except:
                                    pass
                            return None

                        bpy.app.timers.register(execute_wrapper, first_interval=0.0)
                    except json.JSONDecodeError:
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
        try:
            return self._execute_command_internal(command)
        except Exception as e:
            print(f"Error executing command: {str(e)}")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def _execute_command_internal(self, command):
        cmd_type = command.get("type")
        params = command.get("params", {})

        handlers = {
            "ping": self.ping,
            "get_scene_info": self.get_scene_info,
            "get_object_info": self.get_object_info,
            "get_viewport_screenshot": self.get_viewport_screenshot,
            "execute_code": self.execute_code,
            "get_telemetry_consent": self.get_telemetry_consent,
            "import_stl": self.import_stl,
            "export_stl": self.export_stl,
            "analyze_mesh_for_print": self.analyze_mesh_for_print,
        }

        handler = handlers.get(cmd_type)
        if handler:
            try:
                print(f"Executing handler for {cmd_type}")
                result = handler(**params)
                print("Handler execution complete")
                return {"status": "success", "result": result}
            except Exception as e:
                print(f"Error in handler: {str(e)}")
                traceback.print_exc()
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"Unknown command type: {cmd_type}"}

    def ping(self):
        return {"ok": True}

    def get_scene_info(self):
        try:
            print("Getting scene info...")
            scene_info = {
                "name": bpy.context.scene.name,
                "object_count": len(bpy.context.scene.objects),
                "objects": [],
                "unit_system": bpy.context.scene.unit_settings.system,
                "unit_scale_length": bpy.context.scene.unit_settings.scale_length,
            }
            for i, obj in enumerate(bpy.context.scene.objects):
                if i >= 10:
                    break
                scene_info["objects"].append({
                    "name": obj.name,
                    "type": obj.type,
                    "location": [round(float(obj.location.x), 2),
                                 round(float(obj.location.y), 2),
                                 round(float(obj.location.z), 2)],
                })
            print(f"Scene info collected: {len(scene_info['objects'])} objects")
            return scene_info
        except Exception as e:
            print(f"Error in get_scene_info: {str(e)}")
            traceback.print_exc()
            return {"error": str(e)}

    @staticmethod
    def _get_aabb(obj):
        """World-space axis-aligned bounding box (AABB) of a mesh object."""
        if obj.type != 'MESH':
            raise TypeError("Object must be a mesh")
        local_bbox_corners = [mathutils.Vector(corner) for corner in obj.bound_box]
        world_bbox_corners = [obj.matrix_world @ corner for corner in local_bbox_corners]
        min_corner = mathutils.Vector(map(min, zip(*world_bbox_corners)))
        max_corner = mathutils.Vector(map(max, zip(*world_bbox_corners)))
        return [[*min_corner], [*max_corner]]

    @staticmethod
    def _mm_per_unit():
        """How many millimeters one Blender unit represents."""
        return float(bpy.context.scene.unit_settings.scale_length) * 1000.0

    def _dimensions_mm(self, obj):
        bbox = self._get_aabb(obj)
        mm = self._mm_per_unit()
        return [round((bbox[1][i] - bbox[0][i]) * mm, 3) for i in range(3)]

    def get_object_info(self, name):
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")

        obj_info = {
            "name": obj.name,
            "type": obj.type,
            "location": [obj.location.x, obj.location.y, obj.location.z],
            "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
            "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            "visible": obj.visible_get(),
            "materials": [slot.material.name for slot in obj.material_slots if slot.material],
        }

        if obj.type == "MESH":
            obj_info["world_bounding_box"] = self._get_aabb(obj)
            obj_info["dimensions_mm"] = self._dimensions_mm(obj)
            mesh = obj.data
            if mesh:
                obj_info["mesh"] = {
                    "vertices": len(mesh.vertices),
                    "edges": len(mesh.edges),
                    "polygons": len(mesh.polygons),
                }
        return obj_info

    def get_viewport_screenshot(self, max_size=800, filepath=None, format="png"):
        try:
            if not filepath:
                return {"error": "No filepath provided"}

            area = next((a for a in bpy.context.screen.areas if a.type == 'VIEW_3D'), None)
            if not area:
                return {"error": "No 3D viewport found"}

            with bpy.context.temp_override(area=area):
                bpy.ops.screen.screenshot_area(filepath=filepath)

            img = bpy.data.images.load(filepath)
            width, height = img.size
            if max(width, height) > max_size:
                scale = max_size / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img.scale(new_width, new_height)
                img.file_format = format.upper()
                img.save()
                width, height = new_width, new_height
            bpy.data.images.remove(img)

            return {"success": True, "width": width, "height": height, "filepath": filepath}
        except Exception as e:
            return {"error": str(e)}

    def execute_code(self, code):
        try:
            namespace = {"bpy": bpy}
            capture_buffer = io.StringIO()
            with redirect_stdout(capture_buffer):
                exec(code, namespace)
            return {"executed": True, "result": capture_buffer.getvalue()}
        except Exception as e:
            raise Exception(f"Code execution error: {str(e)}")

    def get_telemetry_consent(self):
        try:
            addon_prefs = bpy.context.preferences.addons.get(__name__)
            consent = addon_prefs.preferences.telemetry_consent if addon_prefs else True
        except (AttributeError, KeyError):
            consent = True
        return {"consent": consent}

    # ---------- STL print-prep handlers ----------

    @staticmethod
    def _call_stl_import(filepath):
        """Run the right STL import operator across Blender 3.x and 4.x."""
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"STL file not found: {filepath}")
        if hasattr(bpy.ops.wm, "stl_import"):
            bpy.ops.wm.stl_import(filepath=filepath)
        elif hasattr(bpy.ops.import_mesh, "stl"):
            bpy.ops.import_mesh.stl(filepath=filepath)
        else:
            raise RuntimeError("No STL import operator available in this Blender build")

    @staticmethod
    def _call_stl_export(filepath, apply_modifiers):
        """Run the right STL export operator across Blender 3.x and 4.x."""
        if hasattr(bpy.ops.wm, "stl_export"):
            bpy.ops.wm.stl_export(
                filepath=filepath,
                export_selected_objects=True,
                apply_modifiers=apply_modifiers,
            )
        elif hasattr(bpy.ops.export_mesh, "stl"):
            bpy.ops.export_mesh.stl(
                filepath=filepath,
                use_selection=True,
                use_mesh_modifiers=apply_modifiers,
            )
        else:
            raise RuntimeError("No STL export operator available in this Blender build")

    def import_stl(self, filepath, object_name=None):
        existing = set(bpy.data.objects.keys())
        self._call_stl_import(filepath)

        new_objs = [bpy.data.objects[name] for name in bpy.data.objects.keys() if name not in existing]
        if not new_objs:
            raise RuntimeError("STL import produced no new objects")
        obj = new_objs[0]
        if object_name:
            obj.name = object_name

        mesh = obj.data
        return {
            "name": obj.name,
            "source_file": filepath,
            "mesh": {
                "vertices": len(mesh.vertices),
                "edges": len(mesh.edges),
                "polygons": len(mesh.polygons),
            },
            "dimensions_mm": self._dimensions_mm(obj),
            "world_bounding_box": self._get_aabb(obj),
            "unit_scale_length": float(bpy.context.scene.unit_settings.scale_length),
        }

    def export_stl(self, object_name, filepath, apply_modifiers=True):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object not found: {object_name}")
        if obj.type != 'MESH':
            raise TypeError(f"Object {object_name} is not a mesh (type={obj.type})")

        out_dir = os.path.dirname(filepath)
        if out_dir and not os.path.isdir(out_dir):
            raise FileNotFoundError(f"Output directory does not exist: {out_dir}")

        # Select only the target object so the exporter picks it up.
        for o in bpy.context.selected_objects:
            o.select_set(False)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        self._call_stl_export(filepath, apply_modifiers)

        if not os.path.isfile(filepath):
            raise RuntimeError(f"STL export did not produce a file at {filepath}")

        return {
            "success": True,
            "filepath": filepath,
            "size_bytes": os.path.getsize(filepath),
            "object": obj.name,
            "triangle_count_estimate": len(obj.data.polygons),
            "apply_modifiers": apply_modifiers,
            "dimensions_mm": self._dimensions_mm(obj),
        }

    def analyze_mesh_for_print(self, object_name):
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object not found: {object_name}")
        if obj.type != 'MESH':
            raise TypeError(f"Object {object_name} is not a mesh (type={obj.type})")

        # Work on an evaluated copy so modifiers are accounted for.
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()

        bm = bmesh.new()
        try:
            bm.from_mesh(mesh)
            bm.normal_update()

            non_manifold_edges = sum(1 for e in bm.edges if not e.is_manifold)
            boundary_edges = [e for e in bm.edges if e.is_boundary]
            boundary_loops = self._count_boundary_loops(boundary_edges)

            degenerate_faces = sum(1 for f in bm.faces if f.calc_area() < 1e-12)

            shells = self._count_shells(bm)

            watertight = non_manifold_edges == 0
            if watertight:
                signed_volume = bm.calc_volume(signed=True)
                mm = self._mm_per_unit()
                signed_volume_mm3 = signed_volume * (mm ** 3)
                normals_consistent = signed_volume_mm3 > 0
                normals_status = "consistent" if normals_consistent else "all_inverted"
            else:
                signed_volume_mm3 = None
                normals_status = "unknown_open_mesh"

            result = {
                "object": obj.name,
                "vertex_count": len(bm.verts),
                "edge_count": len(bm.edges),
                "face_count": len(bm.faces),
                "dimensions_mm": self._dimensions_mm(obj),
                "non_manifold_edges": non_manifold_edges,
                "boundary_edges": len(boundary_edges),
                "boundary_loops": boundary_loops,
                "disconnected_shells": shells,
                "degenerate_faces": degenerate_faces,
                "watertight": watertight,
                "normals": normals_status,
                "signed_volume_mm3": signed_volume_mm3,
            }
            result["ready_to_slice"] = (
                watertight
                and degenerate_faces == 0
                and shells == 1
                and normals_status == "consistent"
            )
            return result
        finally:
            bm.free()
            eval_obj.to_mesh_clear()

    @staticmethod
    def _count_boundary_loops(boundary_edges):
        """Count how many closed loops the boundary edges form."""
        edge_set = set(e.index for e in boundary_edges)
        edge_by_index = {e.index: e for e in boundary_edges}
        visited = set()
        loops = 0
        for start_idx in list(edge_set):
            if start_idx in visited:
                continue
            loops += 1
            stack = [start_idx]
            while stack:
                idx = stack.pop()
                if idx in visited:
                    continue
                visited.add(idx)
                edge = edge_by_index[idx]
                for v in edge.verts:
                    for linked in v.link_edges:
                        if linked.index in edge_set and linked.index not in visited:
                            stack.append(linked.index)
        return loops

    @staticmethod
    def _count_shells(bm):
        """Count disconnected mesh islands (shells) via BFS over shared edges."""
        unvisited = set(f.index for f in bm.faces)
        face_by_index = {f.index: f for f in bm.faces}
        shells = 0
        while unvisited:
            shells += 1
            start = next(iter(unvisited))
            stack = [start]
            while stack:
                fi = stack.pop()
                if fi not in unvisited:
                    continue
                unvisited.remove(fi)
                face = face_by_index[fi]
                for edge in face.edges:
                    for linked in edge.link_faces:
                        if linked.index in unvisited:
                            stack.append(linked.index)
        return shells


# Blender Addon Preferences
class BLENDERMCP_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    telemetry_consent: BoolProperty(
        name="Allow Telemetry",
        description="Allow collection of prompts, code snippets, and screenshots to help improve Blender MCP",
        default=True,
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Telemetry & Privacy:", icon='PREFERENCES')
        box = layout.box()
        row = box.row()
        row.prop(self, "telemetry_consent", text="Allow Telemetry")
        box.separator()
        if self.telemetry_consent:
            box.label(text="With consent: We collect anonymized prompts, code, and screenshots.", icon='INFO')
        else:
            box.label(text="Without consent: We only collect minimal anonymous usage data", icon='INFO')
            box.label(text="(tool names, success/failure, duration - no prompts or code).", icon='BLANK1')
        box.separator()
        box.label(text="All data is fully anonymized. You can change this anytime.", icon='CHECKMARK')
        box.separator()
        row = box.row()
        row.operator("blendermcp.open_terms", text="View Terms and Conditions", icon='TEXT')


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
        layout.label(text="Focus: STL print-prep")
        if not scene.blendermcp_server_running:
            layout.operator("blendermcp.start_server", text="Connect to MCP server")
        else:
            layout.operator("blendermcp.stop_server", text="Disconnect from MCP server")
            layout.label(text=f"Running on port {scene.blendermcp_port}")


class BLENDERMCP_OT_StartServer(bpy.types.Operator):
    bl_idname = "blendermcp.start_server"
    bl_label = "Connect to Claude"
    bl_description = "Start the BlenderMCP server to connect with Claude"

    def execute(self, context):
        scene = context.scene
        if not hasattr(bpy.types, "blendermcp_server") or not bpy.types.blendermcp_server:
            bpy.types.blendermcp_server = BlenderMCPServer(port=scene.blendermcp_port)
        bpy.types.blendermcp_server.start()
        scene.blendermcp_server_running = True
        return {'FINISHED'}


class BLENDERMCP_OT_StopServer(bpy.types.Operator):
    bl_idname = "blendermcp.stop_server"
    bl_label = "Stop the connection to Claude"
    bl_description = "Stop the connection to Claude"

    def execute(self, context):
        scene = context.scene
        if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server:
            bpy.types.blendermcp_server.stop()
            del bpy.types.blendermcp_server
        scene.blendermcp_server_running = False
        return {'FINISHED'}


class BLENDERMCP_OT_OpenTerms(bpy.types.Operator):
    bl_idname = "blendermcp.open_terms"
    bl_label = "View Terms and Conditions"
    bl_description = "Open the Terms and Conditions document"

    def execute(self, context):
        terms_url = "https://github.com/ahujasid/blender-mcp/blob/main/TERMS_AND_CONDITIONS.md"
        try:
            import webbrowser
            webbrowser.open(terms_url)
            self.report({'INFO'}, "Terms and Conditions opened in browser")
        except Exception as e:
            self.report({'ERROR'}, f"Could not open Terms and Conditions: {str(e)}")
        return {'FINISHED'}


def register():
    bpy.types.Scene.blendermcp_port = IntProperty(
        name="Port",
        description="Port for the BlenderMCP server",
        default=9876,
        min=1024,
        max=65535,
    )
    bpy.types.Scene.blendermcp_server_running = BoolProperty(name="Server Running", default=False)

    bpy.utils.register_class(BLENDERMCP_AddonPreferences)
    bpy.utils.register_class(BLENDERMCP_PT_Panel)
    bpy.utils.register_class(BLENDERMCP_OT_StartServer)
    bpy.utils.register_class(BLENDERMCP_OT_StopServer)
    bpy.utils.register_class(BLENDERMCP_OT_OpenTerms)
    print("BlenderMCP addon registered")


def unregister():
    if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server:
        bpy.types.blendermcp_server.stop()
        del bpy.types.blendermcp_server

    bpy.utils.unregister_class(BLENDERMCP_PT_Panel)
    bpy.utils.unregister_class(BLENDERMCP_OT_StartServer)
    bpy.utils.unregister_class(BLENDERMCP_OT_StopServer)
    bpy.utils.unregister_class(BLENDERMCP_OT_OpenTerms)
    bpy.utils.unregister_class(BLENDERMCP_AddonPreferences)

    del bpy.types.Scene.blendermcp_port
    del bpy.types.Scene.blendermcp_server_running
    print("BlenderMCP addon unregistered")


if __name__ == "__main__":
    register()
