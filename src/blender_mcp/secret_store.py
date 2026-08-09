"""Local encrypted storage helpers for integration API keys (OS DPAPI / file vault)."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional


def _data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    d = base / "BlenderMCP" / "secrets"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _vault_path() -> Path:
    return _data_dir() / "vault.json"


def _dpapi_protect(data: bytes) -> bytes:
    import ctypes
    import ctypes.wintypes as wt

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wt.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    in_blob = DATA_BLOB(len(data), ctypes.create_string_buffer(data, len(data)))
    out_blob = DATA_BLOB()
    if not crypt32.CryptProtectData(
        ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)
    ):
        raise OSError("CryptProtectData failed")
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        kernel32.LocalFree(out_blob.pbData)


def _dpapi_unprotect(data: bytes) -> bytes:
    import ctypes
    import ctypes.wintypes as wt

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wt.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    in_blob = DATA_BLOB(len(data), ctypes.create_string_buffer(data, len(data)))
    out_blob = DATA_BLOB()
    if not crypt32.CryptUnprotectData(
        ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)
    ):
        raise OSError("CryptUnprotectData failed")
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        kernel32.LocalFree(out_blob.pbData)


def _fernet_key() -> bytes:
    """Derive a local key from machine-ish material (best-effort, not HSM)."""
    material = f"{os.getenv('COMPUTERNAME', '')}|{os.getenv('USERNAME', '')}|{Path.home()}"
    digest = hashlib.sha256(material.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def _encrypt(value: str) -> str:
    raw = value.encode("utf-8")
    if sys.platform == "win32":
        return "dpapi:" + base64.b64encode(_dpapi_protect(raw)).decode("ascii")
    try:
        from cryptography.fernet import Fernet

        token = Fernet(_fernet_key()).encrypt(raw)
        return "fernet:" + token.decode("ascii")
    except Exception:
        # Last resort: obfuscation only — still better than scene props in .blend
        return "b64:" + base64.b64encode(raw).decode("ascii")


def _decrypt(blob: str) -> str:
    if blob.startswith("dpapi:"):
        data = base64.b64decode(blob[6:].encode("ascii"))
        return _dpapi_unprotect(data).decode("utf-8")
    if blob.startswith("fernet:"):
        from cryptography.fernet import Fernet

        return Fernet(_fernet_key()).decrypt(blob[7:].encode("ascii")).decode("utf-8")
    if blob.startswith("b64:"):
        return base64.b64decode(blob[4:].encode("ascii")).decode("utf-8")
    return blob


def set_secret(name: str, value: str) -> None:
    """Store secret encrypted at rest. Empty value deletes."""
    path = _vault_path()
    data: dict = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    if not value:
        data.pop(name, None)
    else:
        data[name] = _encrypt(value)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    if sys.platform != "win32":
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass


def get_secret(name: str) -> Optional[str]:
    path = _vault_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        blob = data.get(name)
        if not blob:
            return None
        return _decrypt(blob)
    except Exception:
        return None


def list_secret_names() -> list[str]:
    path = _vault_path()
    if not path.exists():
        return []
    try:
        return list(json.loads(path.read_text(encoding="utf-8")).keys())
    except Exception:
        return []
