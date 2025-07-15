"""Blender integration through the Model Context Protocol."""

__version__ = "1.3.0"

# Expose key classes and functions for easier imports
try:
    from .server import BlenderConnection, get_blender_connection
except ImportError:
    # Allow importing cursor_integration without MCP dependencies
    pass

# Always expose cursor integration
try:
    from .cursor_integration import CursorIntegration, CursorProjectInfo
except ImportError:
    pass
