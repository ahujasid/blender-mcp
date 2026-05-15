"""Tests for blender_mcp.tool_profiles (no Blender required).

Covers:
- minimal blocks execute_blender_code
- no_python blocks execute_blender_code
- python_enabled allows execute_blender_code
- minimal blocks asset tools
- full allows all tools (original upstream behaviour preserved)
- get_bma_profile_info returns active profile (via server logic)
- headless smoke skipped when Blender not found
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure the fork src is importable without an mcp package installed.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blender_mcp.tool_profiles import (
    EXTERNAL_ASSET_SAFE_PROFILES,
    PYTHON_SAFE_PROFILES,
    get_disabled_tools,
    get_enabled_tools,
    get_profile,
    is_external_asset_allowed,
    is_python_allowed,
    is_tool_enabled,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _with_profile(profile: str):
    """Context manager: temporarily set BMA_MCP_PROFILE."""
    return patch.dict(os.environ, {"BMA_MCP_PROFILE": profile})


_ASSET_TOOLS = {
    "get_polyhaven_status",
    "search_polyhaven_assets",
    "download_polyhaven_asset",
    "get_sketchfab_status",
    "search_sketchfab_models",
    "download_sketchfab_model",
    "get_hyper3d_status",
    "generate_hyper3d_model_via_text",
    "get_hunyuan3d_status",
    "generate_hunyuan3d_model",
}


# ---------------------------------------------------------------------------
# minimal profile
# ---------------------------------------------------------------------------

class TestMinimalProfile:
    def test_blocks_execute_blender_code(self):
        with _with_profile("minimal"):
            assert is_tool_enabled("execute_blender_code") is False

    def test_python_not_allowed(self):
        with _with_profile("minimal"):
            assert is_python_allowed() is False

    def test_blocks_all_asset_tools(self):
        with _with_profile("minimal"):
            for tool in _ASSET_TOOLS:
                assert is_tool_enabled(tool) is False, f"minimal must block {tool}"

    def test_external_asset_not_allowed(self):
        with _with_profile("minimal"):
            assert is_external_asset_allowed() is False

    def test_allows_bma_safe_tools(self):
        with _with_profile("minimal"):
            for tool in [
                "bma_get_scene_info", "bma_create_object", "bma_set_transform",
                "bma_set_material", "bma_create_light", "bma_create_camera",
                "bma_export_scene",
            ]:
                assert is_tool_enabled(tool) is True, f"minimal must allow {tool}"

    def test_allows_get_scene_info(self):
        with _with_profile("minimal"):
            assert is_tool_enabled("get_scene_info") is True

    def test_allows_get_bma_profile_info(self):
        with _with_profile("minimal"):
            assert is_tool_enabled("get_bma_profile_info") is True

    def test_is_in_python_safe_profiles(self):
        assert "minimal" in PYTHON_SAFE_PROFILES

    def test_is_in_external_asset_safe_profiles(self):
        assert "minimal" in EXTERNAL_ASSET_SAFE_PROFILES


# ---------------------------------------------------------------------------
# no_python profile
# ---------------------------------------------------------------------------

class TestNoPythonProfile:
    def test_blocks_execute_blender_code(self):
        with _with_profile("no_python"):
            assert is_tool_enabled("execute_blender_code") is False

    def test_python_not_allowed(self):
        with _with_profile("no_python"):
            assert is_python_allowed() is False

    def test_blocks_asset_tools(self):
        with _with_profile("no_python"):
            for tool in _ASSET_TOOLS:
                assert is_tool_enabled(tool) is False, f"no_python must block {tool}"

    def test_execute_blender_code_in_disabled_list(self):
        with _with_profile("no_python"):
            assert "execute_blender_code" in get_disabled_tools()

    def test_is_in_python_safe_profiles(self):
        assert "no_python" in PYTHON_SAFE_PROFILES


# ---------------------------------------------------------------------------
# python_enabled profile
# ---------------------------------------------------------------------------

class TestPythonEnabledProfile:
    def test_allows_execute_blender_code(self):
        with _with_profile("python_enabled"):
            assert is_tool_enabled("execute_blender_code") is True

    def test_python_is_allowed(self):
        with _with_profile("python_enabled"):
            assert is_python_allowed() is True

    def test_still_blocks_asset_tools(self):
        with _with_profile("python_enabled"):
            for tool in _ASSET_TOOLS:
                assert is_tool_enabled(tool) is False, f"python_enabled must block {tool}"

    def test_execute_blender_code_in_enabled_list(self):
        with _with_profile("python_enabled"):
            assert "execute_blender_code" in get_enabled_tools()


# ---------------------------------------------------------------------------
# full profile
# ---------------------------------------------------------------------------

class TestFullProfile:
    def test_allows_execute_blender_code(self):
        with _with_profile("full"):
            assert is_tool_enabled("execute_blender_code") is True

    def test_allows_asset_tools(self):
        with _with_profile("full"):
            for tool in _ASSET_TOOLS:
                assert is_tool_enabled(tool) is True, f"full must allow {tool}"

    def test_python_is_allowed(self):
        with _with_profile("full"):
            assert is_python_allowed() is True

    def test_external_asset_is_allowed(self):
        with _with_profile("full"):
            assert is_external_asset_allowed() is True

    def test_disabled_list_is_empty_by_default(self):
        with _with_profile("full"), \
             patch.dict(os.environ, {"BMA_DISABLED_TOOLS": ""}):
            assert get_disabled_tools() == []

    def test_get_profile_returns_full_def(self):
        with _with_profile("full"):
            prof = get_profile()
            assert prof.name == "full"
            assert prof.allowed is None  # unrestricted


# ---------------------------------------------------------------------------
# inspection_enabled profile
# ---------------------------------------------------------------------------

class TestInspectionEnabledProfile:
    def test_blocks_execute_blender_code(self):
        with _with_profile("inspection_enabled"):
            assert is_tool_enabled("execute_blender_code") is False

    def test_allows_viewport_screenshot(self):
        with _with_profile("inspection_enabled"):
            assert is_tool_enabled("get_viewport_screenshot") is True

    def test_blocks_asset_tools(self):
        with _with_profile("inspection_enabled"):
            for tool in _ASSET_TOOLS:
                assert is_tool_enabled(tool) is False, f"inspection_enabled must block {tool}"


# ---------------------------------------------------------------------------
# get_bma_profile_info server logic (without Blender/MCP)
# ---------------------------------------------------------------------------

class TestGetBmaProfileInfo:
    def test_returns_active_profile_in_result(self):
        """get_bma_profile_info logic produces a dict with active_profile == set profile."""
        from blender_mcp.tool_profiles import (
            get_profile as tp_get_profile,
            get_enabled_tools,
            get_disabled_tools as tp_get_disabled,
            is_python_allowed,
            is_external_asset_allowed,
        )
        import os as _os

        with _with_profile("minimal"):
            profile = tp_get_profile()
            result = {
                "active_profile": profile.name,
                "enabled_tools": sorted(get_enabled_tools(profile)),
                "disabled_tools": sorted(tp_get_disabled(profile)),
                "allow_python_execution": is_python_allowed(profile),
                "allow_external_assets": is_external_asset_allowed(profile),
            }

        assert result["active_profile"] == "minimal"
        assert "execute_blender_code" not in result["enabled_tools"]
        assert result["allow_python_execution"] is False
        assert result["allow_external_assets"] is False

    def test_full_profile_has_no_disabled_tools(self):
        from blender_mcp.tool_profiles import get_profile, get_disabled_tools

        with _with_profile("full"), \
             patch.dict(os.environ, {"BMA_DISABLED_TOOLS": ""}):
            profile = get_profile()
            disabled = get_disabled_tools(profile)

        assert disabled == []

    def test_python_enabled_profile_shows_execute_in_enabled(self):
        from blender_mcp.tool_profiles import get_profile, get_enabled_tools

        with _with_profile("python_enabled"):
            profile = get_profile()
            enabled = get_enabled_tools(profile)

        assert "execute_blender_code" in enabled


# ---------------------------------------------------------------------------
# Headless smoke: skip when Blender not found
# ---------------------------------------------------------------------------

class TestHeadlessSmokeSkip:
    def test_skip_when_blender_not_found(self):
        """HeadlessBlenderMcpLauncher.build_command raises McpServerStartError when blender missing."""
        # Import from main project, not fork — launcher lives in benchmark.mcp.headless.
        main_src = Path(__file__).parent.parent.parent  # BMA_Bench/
        if str(main_src) not in sys.path:
            sys.path.insert(0, str(main_src))

        from benchmark.mcp.config import McpServerConfig
        from benchmark.mcp.errors import McpServerStartError
        from benchmark.mcp.headless.launcher import HeadlessBlenderMcpLauncher

        cfg = McpServerConfig(
            server_distribution="local",
            package_source="./vendor/blender-mcp-bma",
            blender_host="127.0.0.1",
            blender_port=9876,
            profile="minimal",
            disable_telemetry=True,
        )
        launcher = HeadlessBlenderMcpLauncher(cfg, addon_path=Path("/nonexistent/addon.py"))

        with patch("benchmark.mcp.headless.launcher._find_blender", return_value=None):
            with pytest.raises(McpServerStartError, match="not found"):
                launcher.build_command()
