"""
Blender MCP Stdio Adapter
Implements Model Context Protocol stdio transport inside Blender.

Usage:
    blender --background --python blender_mcp_stdio.py

    Or with GUI for debugging:
    blender --python blender_mcp_stdio.py

Architecture:
    Claude Desktop → stdin/stdout → This Script → bpy.app.timers → Blender API
"""

import json
import sys
import traceback
from typing import Dict, Any, List, Optional
import bpy

# MCP Protocol Version
MCP_VERSION = "2024-11-05"
SERVER_NAME = "blender-mcp"
SERVER_VERSION = "2.0.0"


class MCPStdioServer:
    """
    MCP stdio protocol server running inside Blender.
    Handles JSON-RPC 2.0 requests from stdin, returns responses to stdout.
    """

    def __init__(self):
        self.tools = {}
        self.result_queue = []
        self.running = True
        self.register_tools()

    def log(self, message: str):
        """Log to stderr (won't interfere with stdio protocol on stdout)"""
        print(f"[blender-mcp] {message}", file=sys.stderr, flush=True)

    def register_tools(self):
        """Register all available MCP tools"""
        self.log("Registering tools...")

        # Core Blender tools (always available)
        self.tools["get_scene_info"] = {
            "description": "Get information about the current Blender scene including objects, materials, and scene properties",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
            "handler": self.get_scene_info
        }

        self.tools["get_object_info"] = {
            "description": "Get detailed information about a specific object in the scene by name",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the object to query"
                    }
                },
                "required": ["name"],
                "additionalProperties": False
            },
            "handler": self.get_object_info
        }

        self.tools["execute_code"] = {
            "description": "Execute arbitrary Blender Python (bpy) code and return the output",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute in Blender's environment"
                    }
                },
                "required": ["code"],
                "additionalProperties": False
            },
            "handler": self.execute_code
        }

        self.tools["list_addons"] = {
            "description": "List all installed and enabled Blender addons",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
            "handler": self.list_addons
        }

        self.log(f"Registered {len(self.tools)} tools")

    # ============================================================================
    # Tool Handlers (executed in Blender's main thread)
    # ============================================================================

    def get_scene_info(self) -> Dict[str, Any]:
        """Get information about the current Blender scene"""
        scene = bpy.context.scene
        return {
            "name": scene.name,
            "frame_current": scene.frame_current,
            "frame_start": scene.frame_start,
            "frame_end": scene.frame_end,
            "render_engine": scene.render.engine,
            "object_count": len(scene.objects),
            "objects": [
                {
                    "name": obj.name,
                    "type": obj.type,
                    "location": [obj.location.x, obj.location.y, obj.location.z],
                    "visible": obj.visible_get()
                }
                for obj in list(scene.objects)[:10]  # Limit to 10 objects
            ],
            "materials_count": len(bpy.data.materials),
            "cameras_count": len([obj for obj in scene.objects if obj.type == 'CAMERA']),
            "lights_count": len([obj for obj in scene.objects if obj.type == 'LIGHT']),
        }

    def get_object_info(self, name: str) -> Dict[str, Any]:
        """Get detailed information about a specific object"""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")

        info = {
            "name": obj.name,
            "type": obj.type,
            "location": [obj.location.x, obj.location.y, obj.location.z],
            "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
            "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            "visible": obj.visible_get(),
            "hide_render": obj.hide_render,
            "materials": [slot.material.name for slot in obj.material_slots if slot.material],
        }

        if obj.type == 'MESH' and obj.data:
            mesh = obj.data
            info["mesh"] = {
                "vertices": len(mesh.vertices),
                "edges": len(mesh.edges),
                "polygons": len(mesh.polygons),
            }

        return info

    def execute_code(self, code: str) -> Dict[str, Any]:
        """Execute arbitrary Blender Python code"""
        import io
        from contextlib import redirect_stdout

        try:
            namespace = {"bpy": bpy}
            capture_buffer = io.StringIO()

            with redirect_stdout(capture_buffer):
                exec(code, namespace)

            captured_output = capture_buffer.getvalue()
            return {
                "executed": True,
                "output": captured_output if captured_output else "(no output)"
            }
        except Exception as e:
            return {
                "executed": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def list_addons(self) -> Dict[str, Any]:
        """List all installed and enabled addons"""
        import addon_utils

        all_addons = addon_utils.modules()
        enabled_addons = [mod for mod in all_addons if addon_utils.check(mod.__name__)[1]]

        return {
            "total_addons": len(all_addons),
            "enabled_count": len(enabled_addons),
            "enabled_addons": [
                {
                    "module": mod.__name__,
                    "name": mod.bl_info.get("name", "Unknown"),
                    "version": ".".join(map(str, mod.bl_info.get("version", (0, 0, 0)))),
                    "author": mod.bl_info.get("author", "Unknown"),
                }
                for mod in enabled_addons
            ]
        }

    # ============================================================================
    # MCP Protocol Handlers
    # ============================================================================

    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request"""
        self.log("Initialize request received")
        return {
            "protocolVersion": MCP_VERSION,
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION
            },
            "capabilities": {
                "tools": {}
            }
        }

    def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tools/list request"""
        self.log("Tools list request received")
        return {
            "tools": [
                {
                    "name": name,
                    "description": tool["description"],
                    "inputSchema": tool["inputSchema"]
                }
                for name, tool in self.tools.items()
            ]
        }

    def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tools/call request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        self.log(f"Tool call: {tool_name} with args: {arguments}")

        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Execute tool handler (already in main thread, safe for bpy)
        handler = self.tools[tool_name]["handler"]
        result = handler(**arguments)

        # Return MCP-compliant response
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }
            ]
        }

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Route MCP request to appropriate handler"""
        method = request.get("method")

        if method == "initialize":
            return self.handle_initialize(request.get("params", {}))
        elif method == "tools/list":
            return self.handle_tools_list(request.get("params", {}))
        elif method == "tools/call":
            return self.handle_tools_call(request.get("params", {}))
        else:
            raise ValueError(f"Unknown method: {method}")

    # ============================================================================
    # Stdio Protocol Loop
    # ============================================================================

    def run(self):
        """Main stdio loop - reads JSON-RPC from stdin, writes to stdout"""
        self.log("MCP Stdio Server starting...")
        self.log(f"Blender version: {bpy.app.version_string}")
        self.log(f"Python: {sys.version}")
        self.log("Listening on stdin...")

        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue

                try:
                    # Parse JSON-RPC request
                    request = json.loads(line)
                    request_id = request.get("id")
                    self.log(f"Received request {request_id}: {request.get('method')}")

                    # Handle request
                    result = self.handle_request(request)

                    # Send JSON-RPC response
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": result
                    }
                    print(json.dumps(response), flush=True)
                    self.log(f"Sent response for request {request_id}")

                except json.JSONDecodeError as e:
                    self.log(f"JSON decode error: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error",
                            "data": str(e)
                        }
                    }
                    print(json.dumps(error_response), flush=True)

                except Exception as e:
                    self.log(f"Error handling request: {e}")
                    self.log(traceback.format_exc())
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id") if 'request' in locals() else None,
                        "error": {
                            "code": -32603,
                            "message": "Internal error",
                            "data": str(e)
                        }
                    }
                    print(json.dumps(error_response), flush=True)

        except KeyboardInterrupt:
            self.log("Keyboard interrupt received, shutting down...")
        except Exception as e:
            self.log(f"Fatal error: {e}")
            self.log(traceback.format_exc())
        finally:
            self.log("Server stopped")


def main():
    """Entry point when script is run with: blender --python blender_mcp_stdio.py"""
    server = MCPStdioServer()
    server.run()


if __name__ == "__main__":
    main()
