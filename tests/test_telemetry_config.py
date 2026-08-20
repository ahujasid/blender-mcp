"""Tests for safe telemetry configuration fallback behavior."""

from blender_mcp import telemetry


def test_missing_private_config_disables_telemetry(monkeypatch):
    monkeypatch.setenv("DISABLE_TELEMETRY", "true")
    monkeypatch.setattr(telemetry, "_telemetry_collector", None)

    collector = telemetry.get_telemetry()

    assert collector.config.enabled is False
    assert collector.config.supabase_url == ""
    assert collector.config.supabase_anon_key == ""
