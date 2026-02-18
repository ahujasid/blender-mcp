from __future__ import annotations

import os
from pathlib import Path

from gradio_client import Client


BASE_DIR = Path(__file__).resolve().parent
APP_URL = os.getenv("HUNYUAN_GRADIO_URL", "http://0.0.0.0:6889/")
DEFAULT_IMAGE = BASE_DIR / "whitewolf.png"
DEFAULT_GLB = Path(os.getenv("HUNYUAN_TEST_GLB", str(BASE_DIR / "white_mesh.glb")))


def make_client() -> Client:
    return Client(APP_URL)


def ensure_exists(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
