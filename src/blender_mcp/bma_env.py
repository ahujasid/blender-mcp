# BMA_PATCH: benchmark-specific env-variable reader for tool-gating.
"""Read BMA_* environment variables that control tool-gating in blender-mcp-bma."""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

_DEFAULT_PROFILE = "minimal"
_DEFAULT_DISABLED_TOOLS = ""
_DEFAULT_ENABLE_EXTERNAL_ASSETS = "false"
_DEFAULT_ALLOW_PYTHON_EXECUTION = "false"


def _bool_env(name: str, default: str) -> bool:
    return os.environ.get(name, default).lower() == "true"


def _list_env(name: str, default: str = "") -> list[str]:
    raw = os.environ.get(name, default).strip()
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


# ---------------------------------------------------------------------------
# Public accessors (re-read on every call so tests can monkey-patch os.environ)
# ---------------------------------------------------------------------------

def get_profile() -> str:
    """Return the active BMA_MCP_PROFILE (default: 'minimal')."""
    return os.environ.get("BMA_MCP_PROFILE", _DEFAULT_PROFILE).strip().lower() or _DEFAULT_PROFILE


def get_disabled_tools() -> list[str]:
    """Return tools explicitly disabled via BMA_DISABLED_TOOLS (comma-separated, default: empty)."""
    return _list_env("BMA_DISABLED_TOOLS", _DEFAULT_DISABLED_TOOLS)


def is_external_assets_enabled() -> bool:
    """Return True only when BMA_ENABLE_EXTERNAL_ASSETS=true (default: False)."""
    return _bool_env("BMA_ENABLE_EXTERNAL_ASSETS", _DEFAULT_ENABLE_EXTERNAL_ASSETS)


def is_python_execution_allowed() -> bool:
    """Return True only when BMA_ALLOW_PYTHON_EXECUTION=true (default: False)."""
    return _bool_env("BMA_ALLOW_PYTHON_EXECUTION", _DEFAULT_ALLOW_PYTHON_EXECUTION)


# ---------------------------------------------------------------------------
# Convenience: snapshot of all BMA env settings
# ---------------------------------------------------------------------------

class BmaEnvSnapshot:
    """Immutable snapshot of BMA gating env vars read at instantiation time."""

    __slots__ = ("profile", "disabled_tools", "external_assets", "python_execution")

    def __init__(self) -> None:
        self.profile: str = get_profile()
        self.disabled_tools: list[str] = get_disabled_tools()
        self.external_assets: bool = is_external_assets_enabled()
        self.python_execution: bool = is_python_execution_allowed()

    def __repr__(self) -> str:
        return (
            f"BmaEnvSnapshot(profile={self.profile!r}, "
            f"disabled_tools={self.disabled_tools!r}, "
            f"external_assets={self.external_assets}, "
            f"python_execution={self.python_execution})"
        )
