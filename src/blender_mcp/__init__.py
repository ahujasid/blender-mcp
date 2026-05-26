"""Blender integration through the Model Context Protocol."""

__version__ = "0.1.0"

# Keep package imports lightweight (the MCP server depends on `mcp`).
# Import `blender_mcp.server` explicitly when you need server functionality.

from .blender_connection import BlenderConnection
