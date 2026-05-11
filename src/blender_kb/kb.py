"""KB indexing and lookup. Pure-stdlib, no Blender dependency.

The KB is a tree like:

    <root>/
      CLAUDE.md
      SYSTEM_PROMPT.md
      <kb_name>/
        INDEX.md          # contains "## [topic_id]" blocks with "File: `docs/x.md`"
        docs/
          x.md
        ...

This module parses every INDEX.md found under <root> and exposes:
- resolve_root(): locates the KB root via env var / cwd / walk-up
- KnowledgeBase: in-memory index, list_topics, get_topic, search, read_relative
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ENV_VAR = "BLENDER_KB_PATH"
ROOT_MARKER = "CLAUDE.md"
INDEX_FILENAME = "INDEX.md"
MAX_WALK_UP = 6

# "## [topic_id]" anchor, lowercase + digits + underscore
_TOPIC_RE = re.compile(r"^##\s+\[([a-z0-9_]+)\]\s*$")
# `File: \`docs/foo.md\`` line (backticks optional)
_FILE_RE = re.compile(r"^\s*File:\s*`?([^`\s]+)`?\s*$", re.IGNORECASE)


class KBError(Exception):
    """Base error for KB operations."""


class KBNotFound(KBError):
    pass


class KBPathEscape(KBError):
    """A requested path resolves outside the KB root."""


@dataclass
class Topic:
    topic_id: str
    kb_name: str          # e.g. "Blender for 3d print documentation"
    title: str            # bold line right after the heading
    when_to_use: str      # the "Quando usarlo:" line, if any
    file_rel: str         # path relative to kb_name root, e.g. "docs/mesh_repair.md"

    def abs_path(self, root: Path) -> Path:
        return root / self.kb_name / self.file_rel


@dataclass
class KnowledgeBase:
    root: Path
    topics: dict[str, Topic] = field(default_factory=dict)         # topic_id -> Topic
    kbs: dict[str, Path] = field(default_factory=dict)             # kb_name -> abs INDEX.md path
    duplicates: list[tuple[str, str, str]] = field(default_factory=list)  # (topic_id, kb_a, kb_b)

    # ---- listing ------------------------------------------------------------

    def list_topics(self, kb_name: str | None = None) -> list[Topic]:
        items = self.topics.values()
        if kb_name:
            items = (t for t in items if t.kb_name == kb_name)
        return sorted(items, key=lambda t: (t.kb_name, t.topic_id))

    def list_kbs(self) -> list[str]:
        return sorted(self.kbs.keys())

    # ---- read ---------------------------------------------------------------

    def get_topic(self, topic_id: str) -> tuple[Topic, str]:
        topic = self.topics.get(topic_id)
        if not topic:
            raise KBNotFound(f"Unknown topic_id '{topic_id}'. Use kb_list_topics to discover.")
        path = topic.abs_path(self.root)
        if not path.exists():
            raise KBNotFound(f"File missing for topic '{topic_id}': {path}")
        return topic, path.read_text(encoding="utf-8")

    def read_relative(self, relative: str) -> tuple[Path, str]:
        """Read any file under the KB root by relative path. Containment-checked."""
        # Reject absolute paths and explicit traversal upfront
        if os.path.isabs(relative) or relative.startswith(("/", "\\")):
            raise KBPathEscape(f"Absolute paths not allowed: {relative}")
        target = (self.root / relative).resolve()
        root_resolved = self.root.resolve()
        # Containment: target must be root_resolved or a descendant
        try:
            target.relative_to(root_resolved)
        except ValueError:
            raise KBPathEscape(f"Path '{relative}' escapes KB root")
        if not target.exists():
            raise KBNotFound(f"No such file under KB root: {relative}")
        if target.is_dir():
            raise KBError(f"Path is a directory, not a file: {relative}")
        return target, target.read_text(encoding="utf-8")

    # ---- search -------------------------------------------------------------

    def search(
        self,
        query: str,
        kb_name: str | None = None,
        max_results: int = 10,
        context_lines: int = 2,
    ) -> list[dict]:
        """Case-insensitive substring grep over indexed topic docs.

        Returns list of dicts: {topic_id, kb_name, file_rel, line_no, snippet}.
        """
        q = query.strip().lower()
        if not q:
            return []
        results: list[dict] = []
        for topic in self.list_topics(kb_name=kb_name):
            path = topic.abs_path(self.root)
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            for i, line in enumerate(lines):
                if q in line.lower():
                    lo = max(0, i - context_lines)
                    hi = min(len(lines), i + context_lines + 1)
                    snippet = "\n".join(lines[lo:hi])
                    results.append({
                        "topic_id": topic.topic_id,
                        "kb_name": topic.kb_name,
                        "file_rel": topic.file_rel,
                        "line_no": i + 1,
                        "snippet": snippet,
                    })
                    if len(results) >= max_results:
                        return results
        return results


# ----------------------------- discovery -------------------------------------

def resolve_root(explicit: str | os.PathLike | None = None) -> Path:
    """Locate the KB root.

    Order: explicit arg > $BLENDER_KB_PATH > $CWD/Bible > walk-up looking for a
    directory that contains CLAUDE.md and at least one sub-folder with INDEX.md.
    Raises KBNotFound if nothing matches.
    """
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if _looks_like_root(p):
            return p
        raise KBNotFound(f"Explicit KB path is not a valid KB root: {p}")

    env_val = os.environ.get(ENV_VAR)
    if env_val:
        p = Path(env_val).expanduser().resolve()
        if _looks_like_root(p):
            return p
        raise KBNotFound(f"${ENV_VAR}={env_val} does not point to a valid KB root")

    cwd = Path.cwd().resolve()
    candidate = cwd / "Bible"
    if _looks_like_root(candidate):
        return candidate
    if _looks_like_root(cwd):
        return cwd

    # Walk up from CWD, also probing a child named "Bible" at each level
    current = cwd
    for _ in range(MAX_WALK_UP):
        for probe in (current / "Bible", current):
            if _looks_like_root(probe):
                return probe
        if current.parent == current:
            break
        current = current.parent

    raise KBNotFound(
        f"Cannot locate KB root. Set ${ENV_VAR} to the directory containing "
        f"{ROOT_MARKER!r} and the sub-KB folders."
    )


def _looks_like_root(path: Path) -> bool:
    if not path.is_dir():
        return False
    if not (path / ROOT_MARKER).is_file():
        return False
    # Must contain at least one immediate sub-folder with an INDEX.md
    for child in path.iterdir():
        if child.is_dir() and (child / INDEX_FILENAME).is_file():
            return True
    return False


# ----------------------------- parsing ---------------------------------------

def build_index(root: Path) -> KnowledgeBase:
    """Discover all sub-KBs and parse their INDEX.md files into a KnowledgeBase."""
    kb = KnowledgeBase(root=root)
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        index_path = child / INDEX_FILENAME
        if not index_path.is_file():
            continue
        kb_name = child.name
        kb.kbs[kb_name] = index_path
        for topic in _parse_index(index_path, kb_name):
            existing = kb.topics.get(topic.topic_id)
            if existing:
                # Keep the first occurrence; record the collision
                kb.duplicates.append((topic.topic_id, existing.kb_name, topic.kb_name))
                continue
            kb.topics[topic.topic_id] = topic
    return kb


def _parse_index(index_path: Path, kb_name: str) -> Iterable[Topic]:
    """Yield Topic objects parsed from an INDEX.md."""
    lines = index_path.read_text(encoding="utf-8").splitlines()
    i = 0
    n = len(lines)
    while i < n:
        m = _TOPIC_RE.match(lines[i])
        if not m:
            i += 1
            continue
        topic_id = m.group(1)
        # Scan forward until the next "## [" heading or EOF for title/when/file
        title = ""
        when = ""
        file_rel = ""
        j = i + 1
        while j < n and not _TOPIC_RE.match(lines[j]):
            line = lines[j].strip()
            # First non-empty bold line is the title
            if not title and line.startswith("**") and line.endswith("**") and len(line) > 4:
                title = line.strip("*").strip()
            elif not when and line.lower().startswith("quando usarlo"):
                # "Quando usarlo: ..."
                when = line.split(":", 1)[1].strip() if ":" in line else ""
            elif not file_rel:
                fm = _FILE_RE.match(lines[j])
                if fm:
                    file_rel = fm.group(1).strip()
            j += 1
        if file_rel:
            yield Topic(
                topic_id=topic_id,
                kb_name=kb_name,
                title=title,
                when_to_use=when,
                file_rel=file_rel,
            )
        # else: heading without a "File:" line — skip silently
        i = j
