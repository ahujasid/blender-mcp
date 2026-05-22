# BMA_PATCH: tool-gating profiles for blender-mcp-bma.
"""Profile definitions and tool-gating logic for blender-mcp-bma.

Each profile describes which tools are enabled and whether Python execution
or external asset access is permitted. The active profile is determined by
the BMA_MCP_PROFILE env variable (see bma_env.py).
"""

from __future__ import annotations

from .bma_env import (
    get_disabled_tools as _env_disabled_tools,
    get_profile as _env_get_profile,
    is_external_assets_enabled as _env_external_assets,
    is_python_execution_allowed as _env_python_allowed,
)

# ---------------------------------------------------------------------------
# Complete tool catalogue (all upstream blender-mcp tools)
# ---------------------------------------------------------------------------

_ALL_TOOLS: frozenset[str] = frozenset({
    # Core scene inspection
    "get_bma_profile_info",
    "get_scene_info",
    "get_object_info",
    "get_viewport_screenshot",
    # Python execution
    "execute_blender_code",
    # BMA_PATCH: benchmark-safe structured tools (task 5.18)
    "bma_get_scene_info",
    "bma_create_object",
    "bma_set_transform",
    "bma_set_material",
    "bma_assign_material",
    "bma_create_light",
    "bma_create_camera",
    "bma_create_camera_look_at",
    "bma_export_scene",
    # Poly Haven
    "get_polyhaven_status",
    "get_polyhaven_categories",
    "search_polyhaven_assets",
    "download_polyhaven_asset",
    "set_texture",
    # Sketchfab
    "get_sketchfab_status",
    "search_sketchfab_models",
    "download_sketchfab_model",
    # Hyper3D Rodin
    "get_hyper3d_status",
    "generate_hyper3d_model_via_text",
    "generate_hyper3d_model_via_images",
    "poll_rodin_job_status",
    "import_generated_asset",
    # Hunyuan3D
    "get_hunyuan3d_status",
    "generate_hunyuan3d_model",
    "poll_hunyuan_job_status",
    "import_generated_asset_hunyuan",
})

# All Poly Haven + Sketchfab + Hyper3D Rodin + Hunyuan3D tools.
# BMA_PATCH: explicit safety contract — do not add items to safe profiles.
_EXTERNAL_ASSET_TOOLS: frozenset[str] = frozenset({
    # Poly Haven
    "get_polyhaven_status",
    "get_polyhaven_categories",
    "search_polyhaven_assets",
    "download_polyhaven_asset",
    "set_texture",
    # Sketchfab
    "get_sketchfab_status",
    "search_sketchfab_models",
    "download_sketchfab_model",
    # Hyper3D Rodin
    "get_hyper3d_status",
    "generate_hyper3d_model_via_text",
    "generate_hyper3d_model_via_images",
    "poll_rodin_job_status",
    "import_generated_asset",
    # Hunyuan3D
    "get_hunyuan3d_status",
    "generate_hunyuan3d_model",
    "poll_hunyuan_job_status",
    "import_generated_asset_hunyuan",
})

# Core tools that are safe in every profile.
_CORE_TOOLS: frozenset[str] = _ALL_TOOLS - _EXTERNAL_ASSET_TOOLS - {"execute_blender_code"}

# ---------------------------------------------------------------------------
# Profile data
# ---------------------------------------------------------------------------

class _ProfileDef:
    __slots__ = ("name", "allowed", "python", "external_assets")

    def __init__(
        self,
        name: str,
        allowed: frozenset[str] | None,
        python: bool,
        external_assets: bool,
    ) -> None:
        self.name = name
        self.allowed = allowed          # None == unrestricted
        self.python = python
        self.external_assets = external_assets


_PROFILES: dict[str, _ProfileDef] = {
    # minimal — safe read-only + structured bma_* tools (no Python, no external assets).
    "minimal": _ProfileDef(
        name="minimal",
        allowed=frozenset({
            "get_bma_profile_info",
            "get_scene_info",
            "get_object_info",
            # BMA_PATCH: benchmark-safe structured tools allowed in minimal (task 5.18)
            "bma_get_scene_info",
            "bma_create_object",
            "bma_set_transform",
            "bma_set_material",
            "bma_assign_material",
            "bma_create_light",
            "bma_create_camera",
            "bma_create_camera_look_at",
            "bma_export_scene",
        }),
        python=False,
        external_assets=False,
    ),
    # inspection_enabled — scene inspection + viewport screenshot; no Python, no external.
    "inspection_enabled": _ProfileDef(
        name="inspection_enabled",
        allowed=_CORE_TOOLS | {"get_viewport_screenshot"},
        python=False,
        external_assets=False,
    ),
    # no_python — all core tools; no Python, no external assets.
    "no_python": _ProfileDef(
        name="no_python",
        allowed=_CORE_TOOLS,
        python=False,
        external_assets=False,
    ),
    # python_enabled — core tools + execute_blender_code; no external assets.
    "python_enabled": _ProfileDef(
        name="python_enabled",
        allowed=_CORE_TOOLS | {"execute_blender_code"},
        python=True,
        external_assets=False,
    ),
    # full — all tools, no restrictions.
    "full": _ProfileDef(
        name="full",
        allowed=None,
        python=True,
        external_assets=True,
    ),
}

_FALLBACK_PROFILE = "minimal"

# Profiles where execute_blender_code is UNCONDITIONALLY disabled.
# No env-variable override can lift this restriction.
# BMA_PATCH: explicit safety contract — do not remove.
PYTHON_SAFE_PROFILES: frozenset[str] = frozenset({
    "minimal",
    "no_python",
    "inspection_enabled",
})

# Profiles where execute_blender_code is permitted.
PYTHON_ALLOWED_PROFILES: frozenset[str] = frozenset({
    "python_enabled",
    "full",
})

# Profiles where ALL external asset tools are UNCONDITIONALLY disabled.
# BMA_PATCH: explicit safety contract — do not remove.
EXTERNAL_ASSET_SAFE_PROFILES: frozenset[str] = frozenset({
    "minimal",
    "no_python",
    "inspection_enabled",
})

# Profiles where external asset tools are permitted.
EXTERNAL_ASSET_ALLOWED_PROFILES: frozenset[str] = frozenset({
    "full",
})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_profile(name: str | None = None) -> _ProfileDef:
    """Return the _ProfileDef for *name*, or the active env profile if name is None.

    Falls back to 'minimal' for unknown names.
    """
    resolved = (name or _env_get_profile()).strip().lower()
    return _PROFILES.get(resolved, _PROFILES[_FALLBACK_PROFILE])


def is_tool_enabled(tool_name: str, profile: _ProfileDef | str | None = None) -> bool:
    """Return True if *tool_name* is permitted by *profile*.

    Absolute restrictions (cannot be overridden by env vars):
    - execute_blender_code is blocked for PYTHON_SAFE_PROFILES.
    - all _EXTERNAL_ASSET_TOOLS are blocked for EXTERNAL_ASSET_SAFE_PROFILES.

    Additional tools can be disabled via BMA_DISABLED_TOOLS.
    """
    p = _resolve(profile)

    # Absolute restriction: execute_blender_code blocked for safe profiles.
    if tool_name == "execute_blender_code" and p.name in PYTHON_SAFE_PROFILES:
        return False

    # Absolute restriction: external asset tools blocked for safe profiles.
    if tool_name in _EXTERNAL_ASSET_TOOLS and p.name in EXTERNAL_ASSET_SAFE_PROFILES:
        return False

    # Explicit env-level override: BMA_DISABLED_TOOLS
    if tool_name in _env_disabled_tools():
        return False

    if p.allowed is None:
        return True
    return tool_name in p.allowed


def is_python_allowed(profile: _ProfileDef | str | None = None) -> bool:
    """Return True if Python execution (execute_blender_code) is permitted.

    Restriction is absolute for PYTHON_SAFE_PROFILES — env override cannot lift it.
    """
    p = _resolve(profile)
    if p.name in PYTHON_SAFE_PROFILES:
        return False
    return _env_python_allowed() or p.python


def is_external_asset_allowed(profile: _ProfileDef | str | None = None) -> bool:
    """Return True if external asset tools are permitted.

    Restriction is absolute for EXTERNAL_ASSET_SAFE_PROFILES.
    For other profiles, BMA_ENABLE_EXTERNAL_ASSETS env override is respected.
    """
    p = _resolve(profile)
    if p.name in EXTERNAL_ASSET_SAFE_PROFILES:
        return False
    return _env_external_assets() or p.external_assets


def get_disabled_tools(profile: _ProfileDef | str | None = None) -> list[str]:
    """Return tools that are NOT permitted by *profile* (plus BMA_DISABLED_TOOLS overrides)."""
    p = _resolve(profile)
    env_disabled = set(_env_disabled_tools())

    if p.allowed is None:
        return sorted(env_disabled)

    disabled = (_ALL_TOOLS - p.allowed) | env_disabled
    return sorted(disabled)


def get_enabled_tools(profile: _ProfileDef | str | None = None) -> list[str]:
    """Return tools that ARE permitted by *profile*, minus BMA_DISABLED_TOOLS overrides."""
    p = _resolve(profile)
    env_disabled = set(_env_disabled_tools())

    if p.allowed is None:
        return sorted(_ALL_TOOLS - env_disabled)

    return sorted(p.allowed - env_disabled)


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _resolve(profile: _ProfileDef | str | None) -> _ProfileDef:
    if isinstance(profile, _ProfileDef):
        return profile
    return get_profile(profile)
