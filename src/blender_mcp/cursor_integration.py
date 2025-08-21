"""
Cursor-specific integration features for BlenderMCP.

This module provides enhanced functionality specifically designed for use with Cursor,
including better error handling, development-focused tools, and integration with
Cursor's AI capabilities.
"""

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import subprocess
import sys

logger = logging.getLogger("BlenderMCP.CursorIntegration")

@dataclass
class CursorProjectInfo:
    """Information about the current Cursor project context"""
    project_root: Optional[str] = None
    has_git: bool = False
    python_version: Optional[str] = None
    has_requirements: bool = False
    has_pyproject: bool = False

class CursorIntegration:
    """Enhanced integration features for Cursor users"""
    
    def __init__(self):
        self.project_info = self._detect_project_info()
    
    def _detect_project_info(self) -> CursorProjectInfo:
        """Detect information about the current project context"""
        try:
            # Try to get the current working directory
            cwd = os.getcwd()
            
            # Check if this is a git repository
            has_git = os.path.exists(os.path.join(cwd, ".git"))
            
            # Check for Python project files
            has_requirements = os.path.exists(os.path.join(cwd, "requirements.txt"))
            has_pyproject = os.path.exists(os.path.join(cwd, "pyproject.toml"))
            
            # Get Python version
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            
            return CursorProjectInfo(
                project_root=cwd,
                has_git=has_git,
                python_version=python_version,
                has_requirements=has_requirements,
                has_pyproject=has_pyproject
            )
        except Exception as e:
            logger.warning(f"Could not detect project info: {e}")
            return CursorProjectInfo()
    
    def get_project_context(self) -> Dict[str, Any]:
        """Get context information about the current project for Cursor"""
        return {
            "project_root": self.project_info.project_root,
            "has_git": self.project_info.has_git,
            "python_version": self.project_info.python_version,
            "has_requirements": self.project_info.has_requirements,
            "has_pyproject": self.project_info.has_pyproject,
            "cursor_integration": True
        }
    
    def create_blender_script_template(self, script_name: str, description: str = "") -> str:
        """Create a template for a Blender Python script that can be used in Cursor"""
        template = f'''"""
{description or f"Blender script: {script_name}"}

This script can be executed in Blender using the execute_blender_code tool.
Generated for Cursor integration.
"""

import bpy
import bmesh
from mathutils import Vector

def main():
    """Main execution function"""
    # Clear existing objects (optional)
    # bpy.ops.object.select_all(action='SELECT')
    # bpy.ops.object.delete(use_global=False)
    
    # Your Blender operations here
    # Example:
    # bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    
    print(f"Script '{script_name}' executed successfully")

if __name__ == "__main__":
    main()
'''
        return template
    
    def create_cursor_config_template(self) -> str:
        """Create a template for Cursor MCP configuration"""
        config = {
            "mcpServers": {
                "blender": {
                    "command": "uvx",
                    "args": ["blender-mcp"]
                }
            }
        }
        return json.dumps(config, indent=2)
    
    def create_development_workflow_script(self, workflow_name: str) -> str:
        """Create a development workflow script for Cursor users"""
        template = f'''"""
Development Workflow: {workflow_name}

This script demonstrates a typical development workflow for Blender projects in Cursor.
"""

import bpy
import json
import os

def log_scene_state():
    """Log the current state of the Blender scene"""
    scene_info = {{
        "objects": [],
        "materials": [],
        "lights": [],
        "cameras": []
    }}
    
    for obj in bpy.context.scene.objects:
        obj_info = {{
            "name": obj.name,
            "type": obj.type,
            "location": [obj.location.x, obj.location.y, obj.location.z],
            "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z]
        }}
        scene_info["objects"].append(obj_info)
    
    print(f"Scene State: {{json.dumps(scene_info, indent=2)}}")
    return scene_info

def setup_development_environment():
    """Set up a development-friendly environment"""
    # Set up viewport shading for development
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'MATERIAL'
                    space.shading.use_scene_lights = True
                    space.shading.use_scene_world = True
    
    # Set up a basic lighting setup
    if not any(obj.type == 'LIGHT' for obj in bpy.context.scene.objects):
        bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
        sun = bpy.context.active_object
        sun.data.energy = 5.0
    
    print("Development environment set up successfully")

def main():
    """Main workflow execution"""
    print(f"Starting development workflow: {{workflow_name}}")
    
    # Set up development environment
    setup_development_environment()
    
    # Log initial scene state
    initial_state = log_scene_state()
    
    # Your workflow operations here
    
    # Log final scene state
    final_state = log_scene_state()
    
    print(f"Workflow '{{workflow_name}}' completed successfully")

if __name__ == "__main__":
    main()
'''
        return template

# Global instance for easy access
cursor_integration = CursorIntegration() 