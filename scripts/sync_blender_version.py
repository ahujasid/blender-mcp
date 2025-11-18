#!/usr/bin/env python3
"""Synchronize Blender MCP version strings across pyproject, package init, and addon UI."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - fallback for 3.10
    import tomli as tomllib  # type: ignore[no-redef]

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = ROOT / "pyproject.toml"
INIT_PATH = ROOT / "src" / "blender_mcp" / "__init__.py"
ADDON_PATH = ROOT / "addon.py"

SEMVER_RE = re.compile(
    r"""
    ^
    (?P<major>0|[1-9]\d*)
    \.
    (?P<minor>0|[1-9]\d*)
    \.
    (?P<patch>0|[1-9]\d*)
    (?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?
    (?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?
    $
    """,
    re.VERBOSE,
)

INIT_VERSION_RE = re.compile(r'__version__\s*=\s*"([^"]+)"')
BL_INFO_VERSION_RE = re.compile(r'"version"\s*:\s*\(([^)]+)\)')


def load_version() -> str:
    data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    try:
        version = data["project"]["version"]
    except KeyError as exc:  # pragma: no cover - configuration guard
        raise SystemExit(f"Missing project.version in {PYPROJECT_PATH}") from exc
    if not isinstance(version, str):
        raise SystemExit("project.version must be a string")
    match = SEMVER_RE.match(version)
    if not match:
        raise SystemExit(f"project.version is not SemVer: {version}")
    return version


def expected_version_tuple(version: str) -> str:
    match = SEMVER_RE.match(version)
    if not match:
        raise SystemExit(f"Invalid SemVer: {version}")
    major = match.group("major")
    minor = match.group("minor")
    patch = match.group("patch")
    return f"{int(major)}, {int(minor)}, {int(patch)}"


def check_init(version: str) -> bool:
    text = INIT_PATH.read_text(encoding="utf-8")
    match = INIT_VERSION_RE.search(text)
    return bool(match and match.group(1) == version)


def write_init(version: str) -> None:
    text = INIT_PATH.read_text(encoding="utf-8")
    if INIT_VERSION_RE.search(text):
        text = INIT_VERSION_RE.sub(f'__version__ = "{version}"', text, count=1)
    else:  # pragma: no cover - layout safeguard
        text = text.rstrip() + f'\n__version__ = "{version}"\n'
    INIT_PATH.write_text(text, encoding="utf-8")


def check_addon(version_tuple: str) -> bool:
    text = ADDON_PATH.read_text(encoding="utf-8")
    match = BL_INFO_VERSION_RE.search(text)
    return bool(match and match.group(1).replace(" ", "") == version_tuple.replace(" ", ""))


def write_addon(version_tuple: str) -> None:
    text = ADDON_PATH.read_text(encoding="utf-8")
    if BL_INFO_VERSION_RE.search(text):
        text = BL_INFO_VERSION_RE.sub(f'"version": ({version_tuple})', text, count=1)
    else:  # pragma: no cover - layout safeguard
        text = text.rstrip() + f'\nbl_info["version"] = ({version_tuple})\n'
    ADDON_PATH.write_text(text, encoding="utf-8")


def run(write: bool) -> int:
    version = load_version()
    version_tuple = expected_version_tuple(version)

    init_ok = check_init(version)
    addon_ok = check_addon(version_tuple)

    if write and not init_ok:
        write_init(version)
        init_ok = True
    if write and not addon_ok:
        write_addon(version_tuple)
        addon_ok = True

    problems = []
    if not init_ok:
        problems.append(f"{INIT_PATH} disagrees with pyproject version {version}")
    if not addon_ok:
        problems.append(f"{ADDON_PATH} disagrees with pyproject version {version_tuple}")

    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Update files in place when version drift is detected.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return run(write=args.write)


if __name__ == "__main__":
    raise SystemExit(main())
