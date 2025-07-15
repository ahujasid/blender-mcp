"""
Example: Cursor Integration Features

This script demonstrates how to use the new Cursor-specific features
in BlenderMCP. Run this in Cursor to see the enhanced functionality.
"""

def demonstrate_cursor_features():
    """Demonstrate the new Cursor-specific features"""
    
    print("🚀 BlenderMCP Cursor Integration Demo")
    print("=" * 50)
    
    # 1. Get project context
    print("\n1. Getting project context...")
    project_info = get_cursor_project_info()
    print(f"Project info: {project_info}")
    
    # 2. Create a script template
    print("\n2. Creating a Blender script template...")
    template = create_blender_script_template(
        "demo_scene", 
        "Create a simple demo scene with basic objects"
    )
    print("Template created successfully!")
    
    # 3. Create a development workflow
    print("\n3. Creating a development workflow script...")
    workflow = create_development_workflow_script("demo_workflow")
    print("Workflow script created successfully!")
    
    # 4. Get current scene info
    print("\n4. Getting current scene information...")
    scene_info = get_scene_info()
    print(f"Scene info: {scene_info}")
    
    # 5. Create a simple scene with enhanced logging
    print("\n5. Creating a simple scene with enhanced logging...")
    scene_code = """
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "DemoCube"

# Create a sphere
bpy.ops.mesh.primitive_uv_sphere_add(location=(3, 0, 0))
sphere = bpy.context.active_object
sphere.name = "DemoSphere"

# Add a light
bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
light = bpy.context.active_object
light.name = "DemoLight"

print("Demo scene created successfully!")
"""
    
    result = execute_blender_code_with_logging(scene_code, enable_logging=True)
    print(f"Scene creation result: {result}")
    
    # 6. Export the scene as code
    print("\n6. Exporting scene as executable code...")
    exported_code = get_blender_scene_as_code()
    print("Scene exported as code successfully!")
    
    # 7. Create MCP configuration template
    print("\n7. Creating MCP configuration template...")
    config_template = create_cursor_config_template()
    print("Configuration template created successfully!")
    
    print("\n✅ Cursor integration demo completed!")
    print("\nNext steps:")
    print("- Use the generated templates in your projects")
    print("- Try the enhanced logging features for debugging")
    print("- Export your scenes as code for version control")
    print("- Check the CURSOR_SETUP.md file for detailed instructions")

if __name__ == "__main__":
    demonstrate_cursor_features() 