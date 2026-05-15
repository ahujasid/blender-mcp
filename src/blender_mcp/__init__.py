"""Blender integration through the Model Context Protocol."""

__version__ = "0.1.0"

# Expose key classes and functions for easier imports
from .server import BlenderConnection, get_blender_connection

# BMA_PATCH: expose env-variable accessors for tool-gating
from .bma_env import (  # noqa: F401
    BmaEnvSnapshot,
    get_disabled_tools,
    get_profile as get_env_profile,
    is_external_assets_enabled,
    is_python_execution_allowed,
)

# BMA_PATCH: expose tool-profile gating API
from .tool_profiles import (  # noqa: F401
    get_disabled_tools,
    get_enabled_tools,
    get_profile,
    is_external_asset_allowed,
    is_python_allowed,
    is_tool_enabled,
)
