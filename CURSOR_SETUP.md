# Cursor Integration Setup Guide

This guide provides enhanced setup instructions specifically for Cursor users, including new Cursor-specific features and tools.

## Quick Start

### 1. Install Prerequisites

**Install uv package manager:**

**Mac:**
```bash
brew install uv
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
set Path=C:\Users\%USERNAME%\.local\bin;%Path%
```

**Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install BlenderMCP

```bash
uvx install blender-mcp
```

### 3. Configure Cursor

The project includes a `.cursor/mcp.json` file that automatically configures the MCP server when you open this project in Cursor.

If you want to use BlenderMCP globally across all projects:

1. Open Cursor Settings
2. Go to MCP section
3. Click "Add new global MCP server"
4. Use the configuration from `.cursor/mcp.json`

### 4. Install Blender Addon

1. Download `addon.py` from this repository
2. Open Blender
3. Go to Edit > Preferences > Add-ons
4. Click "Install..." and select `addon.py`
5. Enable the addon by checking "Interface: Blender MCP"

## Cursor-Specific Features

### New Tools Available in Cursor

#### 1. Project Context Information
```python
get_cursor_project_info()
```
Provides information about your current project, including:
- Project root directory
- Git repository status
- Python version
- Project configuration files

#### 2. Script Templates
```python
create_blender_script_template(script_name, description)
```
Generates ready-to-use Blender Python script templates with proper structure and imports.

#### 3. Development Workflows
```python
create_development_workflow_script(workflow_name)
```
Creates comprehensive development workflow scripts with logging and error handling.

#### 4. Enhanced Code Execution
```python
execute_blender_code_with_logging(code, enable_logging=True)
```
Execute Blender code with enhanced logging for better debugging in Cursor.

#### 5. Scene to Code Conversion
```python
get_blender_scene_as_code()
```
Converts your current Blender scene into executable Python code for development.

**Note:** This function generates simplified representations of objects. Complex geometry is represented as basic primitives (cubes, spheres, cylinders, planes) with correct transform properties. For complex models, consider using asset libraries or importing original files directly.

#### 6. Configuration Templates
```python
create_cursor_config_template()
```
Generates MCP configuration templates for Cursor.

## Development Workflow

### 1. Project Setup
```python
# Get project context
get_cursor_project_info()

# Create a development workflow
create_development_workflow_script("my_scene_creation")
```

### 2. Scene Development
```python
# Get current scene info
get_scene_info()

# Create script template
create_blender_script_template("scene_setup", "Setup basic scene with lighting")

# Execute with logging
execute_blender_code_with_logging("""
import bpy
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
""")
```

### 3. Asset Integration
```python
# Check available integrations
get_polyhaven_status()
get_sketchfab_status()
get_hyper3d_status()

# Download assets
search_polyhaven_assets("furniture", "models")
download_polyhaven_asset("asset_id", "models")
```

### 4. Scene Export
```python
# Convert scene to code for version control
get_blender_scene_as_code()
```

## Enhanced Error Handling

The Cursor integration includes improved error handling and logging:

- **Connection Diagnostics**: Better error messages for connection issues
- **Code Execution Logging**: Detailed logs for debugging Blender scripts
- **Project Context Awareness**: Automatic detection of project structure
- **Template Generation**: Pre-built templates for common workflows

## Troubleshooting

### Common Issues

#### 1. Connection Failed
```
Error: Could not connect to Blender. Make sure the Blender addon is running.
```

**Solution:**
- Ensure Blender is running
- Check that the BlenderMCP addon is enabled
- Verify the addon shows "Connected to Claude" in the sidebar

#### 2. MCP Server Not Found
```
Error: Command 'uvx' not found
```

**Solution:**
- Install uv: `brew install uv` (Mac) or use the Windows/Linux installers
- Restart Cursor after installation
- Verify installation: `uvx --version`

#### 3. Permission Issues
```
Error: Permission denied
```

**Solution:**
- On Windows, run Cursor as Administrator
- On Mac/Linux, check file permissions
- Ensure uv is in your PATH

#### 4. Blender Script Errors
```
Error: Script execution failed
```

**Solution:**
- Use `execute_blender_code_with_logging()` for better error messages
- Check Blender's System Console for detailed errors
- Verify Python syntax in your scripts

### Debug Mode

Enable debug logging by setting the environment variable:
```bash
export BLENDER_MCP_DEBUG=1
```

### Getting Help

1. **Check Logs**: Look for detailed error messages in Cursor's output
2. **Verify Setup**: Use `get_cursor_project_info()` to check your environment
3. **Test Connection**: Try a simple command like `get_scene_info()`

## Best Practices for Cursor

### 1. Project Organization
- Keep Blender scripts in a dedicated folder
- Use version control for your scene code
- Document your workflows with the template tools

### 2. Development Workflow
- Start with `get_scene_info()` to understand the current state
- Use templates for consistent script structure
- Enable logging for complex operations
- Export scenes as code for version control

### 3. Asset Management
- Check integration status before downloading assets
- Use appropriate asset sources for different needs
- Document asset usage in your project

### 4. Error Prevention
- Always save your Blender work before running scripts
- Test scripts on simple scenes first
- Use the enhanced logging features for debugging

## Advanced Features

### Custom Script Templates
Create your own script templates by modifying the `cursor_integration.py` file:

```python
def create_custom_template(self, template_name: str) -> str:
    # Your custom template logic here
    pass
```

### Integration with Cursor AI
The enhanced tools work seamlessly with Cursor's AI features:
- Use AI to generate scene descriptions
- Let AI create scripts from natural language
- Use AI to debug and optimize your Blender workflows

### Project-Specific Configuration
Create project-specific MCP configurations by modifying `.cursor/mcp.json`:

```json
{
    "mcpServers": {
        "blender": {
            "command": "uvx",
            "args": ["blender-mcp"],
            "env": {
                "BLENDER_MCP_DEBUG": "1"
            }
        }
    }
}
```

## Support and Updates

- **Documentation**: Check the main README.md for general information
- **Community**: Join the [Discord server](https://discord.gg/z5apgR8TFU)
- **Issues**: Report bugs on the GitHub repository
- **Updates**: Keep your installation updated with `uvx install --upgrade blender-mcp`

---

**Note**: This Cursor integration is designed to enhance your development workflow. The core BlenderMCP functionality remains the same, but with additional tools and better integration for Cursor users. 