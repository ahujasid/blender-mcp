"""Shared paths for the test suite.

These tests read the root addon.py as a source file (it cannot be imported
without bpy), so they need the repo root rather than the tests directory.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ROOT_ADDON = REPO_ROOT / "addon.py"
