"""Blender integration through the Model Context Protocol."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("blender-mcp")
except PackageNotFoundError:
    # Package is not installed (e.g. running from a source checkout)
    __version__ = "unknown"

# Expose key classes and functions for easier imports
from .server import BlenderConnection, get_blender_connection
