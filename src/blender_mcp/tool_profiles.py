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
# Complete tool catalogue (mirrors upstream blender-mcp tools)
# ---------------------------------------------------------------------------

_ALL_TOOLS: frozenset[str] = frozenset({
    "get_bma_profile_info",
    "get_scene_info",
    "get_object_info",
    "get_viewport_screenshot",
    "execute_blender_code",
    "get_polyhaven_categories",
    "search_polyhaven_assets",
    "download_polyhaven_asset",
    "set_texture",
    "get_polyhaven_status",
    "get_hyper3d_status",
    "get_sketchfab_status",
    "search_sketchfab_models",
    "download_sketchfab_model",
    "generate_hyper3d_model_via_text",
    "generate_hyper3d_model_via_images",
})

_PYTHON_TOOLS: frozenset[str] = frozenset({"execute_blender_code"})

_EXTERNAL_ASSET_TOOLS: frozenset[str] = frozenset({
    "get_polyhaven_categories",
    "search_polyhaven_assets",
    "download_polyhaven_asset",
    "set_texture",
    "get_polyhaven_status",
    "search_sketchfab_models",
    "download_sketchfab_model",
    "generate_hyper3d_model_via_text",
    "generate_hyper3d_model_via_images",
    "get_hyper3d_status",
    "get_sketchfab_status",
})

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
    "minimal": _ProfileDef(
        name="minimal",
        allowed=frozenset({
            "get_bma_profile_info",
            "get_scene_info",
            "get_object_info",
        }),
        python=False,
        external_assets=False,
    ),
    "inspection_enabled": _ProfileDef(
        name="inspection_enabled",
        allowed=frozenset({
            "get_bma_profile_info",
            "get_scene_info",
            "get_object_info",
            "get_viewport_screenshot",
        }),
        python=False,
        external_assets=False,
    ),
    "no_python": _ProfileDef(
        name="no_python",
        allowed=_ALL_TOOLS - {"execute_blender_code"},
        python=False,
        external_assets=True,
    ),
    "python_enabled": _ProfileDef(
        name="python_enabled",
        allowed=frozenset({
            "get_bma_profile_info",
            "get_scene_info",
            "get_object_info",
            "get_viewport_screenshot",
            "execute_blender_code",
            "get_polyhaven_status",
            "get_hyper3d_status",
            "get_sketchfab_status",
        }),
        python=True,
        external_assets=False,
    ),
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

    If *profile* is None the active env profile is used.
    Extra tools disabled via BMA_DISABLED_TOOLS are always excluded.

    execute_blender_code is unconditionally blocked for PYTHON_SAFE_PROFILES
    regardless of any env-variable override.
    """
    p = _resolve(profile)

    # Absolute restriction: execute_blender_code is never enabled for safe profiles.
    if tool_name == "execute_blender_code" and p.name in PYTHON_SAFE_PROFILES:
        return False

    # Explicit env-level override: BMA_DISABLED_TOOLS
    if tool_name in _env_disabled_tools():
        return False

    if p.allowed is None:
        return True
    return tool_name in p.allowed


def is_python_allowed(profile: _ProfileDef | str | None = None) -> bool:
    """Return True if Python execution (execute_blender_code) is permitted.

    For PYTHON_SAFE_PROFILES (minimal, no_python, inspection_enabled) the
    restriction is absolute — BMA_ALLOW_PYTHON_EXECUTION cannot override it.
    For python_enabled and full, BMA_ALLOW_PYTHON_EXECUTION is respected.
    """
    p = _resolve(profile)
    # Absolute restriction for safe profiles — no env override allowed.
    if p.name in PYTHON_SAFE_PROFILES:
        return False
    return _env_python_allowed() or p.python


def is_external_asset_allowed(profile: _ProfileDef | str | None = None) -> bool:
    """Return True if external asset tools are permitted.

    Respects BMA_ENABLE_EXTERNAL_ASSETS env override.
    """
    if _env_external_assets():
        return True
    return _resolve(profile).external_assets


def get_disabled_tools(profile: _ProfileDef | str | None = None) -> list[str]:
    """Return tools that are NOT permitted by *profile* (plus BMA_DISABLED_TOOLS overrides)."""
    p = _resolve(profile)
    env_disabled = set(_env_disabled_tools())

    if p.allowed is None:
        # full profile: only env-level disabled tools apply
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
