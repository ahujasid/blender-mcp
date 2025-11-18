"""
Persistent settings management for Blender MCP.

Provides a configurable storage layer for user-adjustable values such as the
default vLLM endpoint and model selection strategy. Settings are stored in a
JSON file located under the user's configuration directory (override with
BLENDER_MCP_SETTINGS_PATH).
"""

from __future__ import annotations

import json
import logging
import os
from collections import deque
import copy
from pathlib import Path
from threading import Lock
from typing import Iterable, List, Optional


logger = logging.getLogger("BlenderMCPSettings")

DEFAULT_SETTINGS = {
    "vllm": {
        "endpoint": "http://localhost:8000/v1/chat/completions",
        "models": {
            "type": "ring",
            "items": ["deepseek-ocr"],
            "rotate_on_call": False,
        },
        "health_check": {
            "enabled": True,
            "relative_path": "/health",
            "timeout_seconds": 5,
        },
    }
}


def _default_settings_path() -> Path:
    """Determine the platform-appropriate default settings location."""
    env_override = os.getenv("BLENDER_MCP_SETTINGS_PATH")
    if env_override:
        return Path(env_override).expanduser()

    # Basic cross-platform layout without extra dependencies.
    base_dir: Path
    if os.name == "nt":
        base_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys_platform := os.environ.get("XDG_CONFIG_HOME"):
        base_dir = Path(sys_platform)
    else:
        base_dir = Path.home() / ".config"

    return base_dir / "blender-mcp" / "settings.json"


class ModelRing:
    """
    Round-robin model selector backed by a deque.

    This structure provides deterministic cycling over the configured models and
    can optionally rotate the order every time it is consumed.
    """

    def __init__(self, models: Iterable[str], rotate_on_call: bool = False):
        items = [m for m in models if isinstance(m, str) and m.strip()]
        self._ring = deque(items)
        self._lock = Lock()
        self._rotate_on_call = rotate_on_call

    @classmethod
    def from_config(cls, value: object) -> "ModelRing":
        """
        Build a ModelRing from JSON-deserialized settings.

        Accepts:
            - ModelRing (returns as-is)
            - dict with keys {type: "ring", items: [...], rotate_on_call: bool}
            - iterable of strings
            - single string
        """
        if isinstance(value, cls):
            return value

        rotate_on_call = False
        items: List[str] = []

        if isinstance(value, dict):
            cfg_type = value.get("type")
            if cfg_type and cfg_type != "ring":
                logger.warning("Unsupported model config type '%s'; falling back to ring.", cfg_type)
            raw_items = value.get("items", [])
            if isinstance(raw_items, str):
                items = [raw_items]
            elif isinstance(raw_items, Iterable):
                items = [str(m) for m in raw_items if m]
            rotate_on_call = bool(value.get("rotate_on_call", False))
        elif isinstance(value, str):
            items = [value]
        elif isinstance(value, Iterable):
            items = [str(m) for m in value if m]

        return cls(items, rotate_on_call=rotate_on_call)

    def as_list(self) -> List[str]:
        """Return the models as an ordered list without mutating rotation state."""
        with self._lock:
            return list(self._ring)

    def choose_order(self) -> List[str]:
        """
        Return the models for the next invocation.

        If rotate_on_call is enabled, the deque is rotated once to surface the
        next model at the front before returning the snapshot.
        """
        with self._lock:
            if self._rotate_on_call and self._ring:
                self._ring.rotate(-1)
            return list(self._ring)

    def peek_primary(self) -> Optional[str]:
        """Peek at the current primary model (or None if the ring is empty)."""
        with self._lock:
            return self._ring[0] if self._ring else None

    def to_config(self) -> dict:
        """Serialize the ring back into a settings-friendly dict."""
        with self._lock:
            return {
                "type": "ring",
                "items": list(self._ring),
                "rotate_on_call": self._rotate_on_call,
            }


class SettingsManager:
    """Manage persistence and lookup of Blender MCP settings."""

    def __init__(self, path: Optional[Path] = None):
        self._path = path or _default_settings_path()
        self._settings = {}
        self._load()

    @property
    def path(self) -> Path:
        return self._path

    def _load(self) -> None:
        try:
            if self._path.exists():
                self._settings = json.loads(self._path.read_text())
                logger.info("Loaded Blender MCP settings from %s", self._path)
            else:
                self._settings = copy.deepcopy(DEFAULT_SETTINGS)
                self._ensure_parent_dir()
                self.save()
                logger.info("Created default Blender MCP settings at %s", self._path)
        except Exception as exc:
            logger.error("Failed to load settings (%s); falling back to defaults.", exc)
            self._settings = copy.deepcopy(DEFAULT_SETTINGS)

    def _ensure_parent_dir(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def save(self) -> None:
        try:
            self._ensure_parent_dir()
            with self._path.open("w", encoding="utf-8") as fh:
                json.dump(self._settings, fh, indent=2)
        except Exception as exc:
            logger.error("Failed to persist settings to %s: %s", self._path, exc)

    def get(self, section: str, default: Optional[dict] = None) -> dict:
        return self._settings.get(section, default or {})

    def update(self, section: str, values: dict) -> None:
        current = self._settings.get(section, {})
        current.update(values)
        self._settings[section] = current
        self.save()

    # Convenience methods for vLLM configuration --------------------------------

    def get_vllm_endpoint(self) -> str:
        vllm = self.get("vllm", {})
        return vllm.get("endpoint", DEFAULT_SETTINGS["vllm"]["endpoint"])

    def get_vllm_model_ring(self) -> ModelRing:
        vllm = self.get("vllm", {})
        models = vllm.get("models", DEFAULT_SETTINGS["vllm"]["models"])
        return ModelRing.from_config(models)

    def get_vllm_health_check(self) -> dict:
        vllm = self.get("vllm", {})
        return vllm.get("health_check", DEFAULT_SETTINGS["vllm"]["health_check"]).copy()

    def set_vllm_models(self, models: Iterable[str], rotate_on_call: bool = False) -> None:
        ring = ModelRing(models, rotate_on_call=rotate_on_call)
        self.update("vllm", {"models": ring.to_config()})


def get_settings_manager() -> SettingsManager:
    """Singleton accessor used by the MCP server."""
    global _SETTINGS_MANAGER
    try:
        manager = _SETTINGS_MANAGER
    except NameError:
        manager = SettingsManager()
        _SETTINGS_MANAGER = manager
    return manager


__all__ = ["SettingsManager", "ModelRing", "get_settings_manager"]
