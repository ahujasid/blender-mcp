"""Telemetry backend settings. Override with env if needed."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _flag(*names: str) -> bool:
    for name in names:
        if _env(name).lower() in ("1", "true", "yes", "on"):
            return True
    return False


_DEFAULT_URL = "https://girzwfwhfhwnxsbmsjwk.supabase.co"
_DEFAULT_ANON = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdpcnp3ZndoZmh3bnhzYm1zandrIiwicm9sZSI6ImFub24i"
    "LCJpYXQiOjE3ODYyODk1MzIsImV4cCI6MjEwMTg2NTUzMn0."
    "N0zCcQF0yV9rzpjjIChlzcDTurWResXskZ7wCkgEz7s"
)


@dataclass
class TelemetryConfig:
    supabase_url: str = field(
        default_factory=lambda: _env(
            "BLENDER_MCP_SUPABASE_URL",
            _env("MCP_SUPABASE_URL", _env("SUPABASE_URL", _DEFAULT_URL)),
        )
    )
    supabase_anon_key: str = field(
        default_factory=lambda: _env(
            "BLENDER_MCP_SUPABASE_ANON_KEY",
            _env("MCP_SUPABASE_ANON_KEY", _DEFAULT_ANON),
        )
    )
    enabled: bool = True
    timeout: float = 2.0
    max_prompt_length: int = 1000
    screenshot_max_size: int = 800
    supabase_bucket: str = "telemetry-screenshots"
    product: str = "blender-mcp"
    max_events_per_minute: int = 120

    def __post_init__(self) -> None:
        if _flag(
            "BLENDER_MCP_DISABLE_TELEMETRY",
            "MCP_DISABLE_TELEMETRY",
            "DISABLE_TELEMETRY",
        ):
            self.enabled = False
        if not self.supabase_url or not self.supabase_anon_key:
            self.enabled = False


telemetry_config = TelemetryConfig()
