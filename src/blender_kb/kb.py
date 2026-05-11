"""KB indexing and lookup. Pure-stdlib + PyYAML.

The KB is a tree like:

    <root>/
      CLAUDE.md
      SYSTEM_PROMPT.md
      playbooks/                 # optional: JSON playbooks for kb_get_playbook
        repair_basic.json
        ...
      <kb_name>/
        INDEX.md                 # human-readable, parsed for topic_id + File:
        INDEX.yaml               # optional, machine-readable metadata
        docs/                    # active topic files
          x.md
        _archive/                # ignored by default (band C / out of scope)
          INDEX.md
          docs/
        routing_rules.yaml       # optional, consumed by kb_route
        ...

This module parses every active INDEX.md found under <root> and exposes:
- resolve_root(): locates the KB root via env var / cwd / walk-up
- KnowledgeBase: in-memory index, list_topics, get_topic, search, read_relative
                 playbooks, routing rules
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml  # type: ignore
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "PyYAML is required (pip install pyyaml). See pyproject.toml dependencies."
    ) from e

ENV_VAR = "BLENDER_KB_PATH"
ROOT_MARKER = "CLAUDE.md"
INDEX_FILENAME = "INDEX.md"
INDEX_META_FILENAME = "INDEX.yaml"
ROUTING_RULES_FILENAME = "routing_rules.yaml"
PLAYBOOKS_DIR = "playbooks"
MAX_WALK_UP = 6

# Folders skipped by sub-KB discovery (archived / hidden / package metadata)
_SKIP_DIRS = {"playbooks", "eval", "scripts", "templates"}
_SKIP_PREFIXES = ("_", ".")

# "## [topic_id]" anchor, lowercase + digits + underscore
_TOPIC_RE = re.compile(r"^##\s+\[([a-z0-9_]+)\]\s*$")
# `File: \`docs/foo.md\`` (backticked, may contain spaces)
# or `File: docs/foo.md` (no backticks, no spaces in path)
_FILE_RE = re.compile(
    r"^\s*File:\s*(?:`([^`]+)`|(\S+))\s*$",
    re.IGNORECASE,
)


class KBError(Exception):
    """Base error for KB operations."""


class KBNotFound(KBError):
    pass


class KBPathEscape(KBError):
    """A requested path resolves outside the KB root."""


@dataclass
class Topic:
    topic_id: str
    kb_name: str
    title: str
    when_to_use: str
    file_rel: str
    # Optional structured metadata from INDEX.yaml
    band: str = ""                                 # "A" | "B" | "C" | ""
    solves_symptoms: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    related: list[str] = field(default_factory=list)

    def abs_path(self, root: Path) -> Path:
        return root / self.kb_name / self.file_rel


@dataclass
class KnowledgeBase:
    root: Path
    topics: dict[str, Topic] = field(default_factory=dict)
    kbs: dict[str, Path] = field(default_factory=dict)
    duplicates: list[tuple[str, str, str]] = field(default_factory=list)

    # ---- listing ------------------------------------------------------------

    def list_topics(
        self,
        kb_name: str | None = None,
        band: str | None = None,
        solves_symptom: str | None = None,
    ) -> list[Topic]:
        items = list(self.topics.values())
        if kb_name:
            items = [t for t in items if t.kb_name == kb_name]
        if band:
            items = [t for t in items if t.band == band]
        if solves_symptom:
            s = solves_symptom.strip()
            items = [t for t in items if s in t.solves_symptoms]
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
        if os.path.isabs(relative) or relative.startswith(("/", "\\")):
            raise KBPathEscape(f"Absolute paths not allowed: {relative}")
        target = (self.root / relative).resolve()
        root_resolved = self.root.resolve()
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
        """Case-insensitive substring grep over indexed topic docs."""
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

    # ---- routing & playbooks ------------------------------------------------

    def load_routing_rules(self, kb_name: str | None = None) -> list[dict]:
        """Load routing_rules.yaml from each sub-KB (or just the requested one).

        Returns the merged list. Each rule must contain at least `when` and `then`.
        """
        rules: list[dict] = []
        names = [kb_name] if kb_name else self.list_kbs()
        for name in names:
            path = self.root / name / ROUTING_RULES_FILENAME
            if not path.is_file():
                continue
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            file_rules = data.get("rules", [])
            for r in file_rules:
                r.setdefault("kb_name", name)
            rules.extend(file_rules)
        return rules

    def list_playbooks(self) -> list[dict]:
        """Return summary of all playbooks under <root>/playbooks/."""
        pdir = self.root / PLAYBOOKS_DIR
        if not pdir.is_dir():
            return []
        out: list[dict] = []
        for pf in sorted(pdir.glob("*.json")):
            try:
                data = json.loads(pf.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            out.append({
                "id": data.get("id", pf.stem),
                "file": pf.name,
                "title": data.get("title", ""),
                "when_to_use": data.get("when_to_use", ""),
                "step_count": len(data.get("steps", [])),
            })
        return out

    def get_playbook(self, playbook_id: str) -> dict:
        pdir = self.root / PLAYBOOKS_DIR
        candidates = [pdir / f"{playbook_id}.json"]
        for pf in candidates:
            if pf.is_file():
                return json.loads(pf.read_text(encoding="utf-8"))
        raise KBNotFound(f"Unknown playbook_id '{playbook_id}'. Use kb_list_playbooks.")


# ----------------------------- discovery -------------------------------------

def resolve_root(explicit: str | os.PathLike | None = None) -> Path:
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
    for child in path.iterdir():
        if not _is_subkb_candidate(child):
            continue
        if (child / INDEX_FILENAME).is_file():
            return True
    return False


def _is_subkb_candidate(path: Path) -> bool:
    """Decide whether a child directory should be scanned as a sub-KB."""
    if not path.is_dir():
        return False
    name = path.name
    if name in _SKIP_DIRS:
        return False
    if name.startswith(_SKIP_PREFIXES):
        return False
    return True


# ----------------------------- parsing ---------------------------------------

def build_index(root: Path) -> KnowledgeBase:
    """Discover all sub-KBs and parse INDEX.md (+ optional INDEX.yaml) into a KnowledgeBase."""
    kb = KnowledgeBase(root=root)
    for child in sorted(root.iterdir()):
        if not _is_subkb_candidate(child):
            continue
        index_path = child / INDEX_FILENAME
        if not index_path.is_file():
            continue
        kb_name = child.name
        kb.kbs[kb_name] = index_path
        meta = _load_index_yaml(child / INDEX_META_FILENAME)
        for topic in _parse_index(index_path, kb_name):
            _enrich_with_meta(topic, meta.get(topic.topic_id))
            existing = kb.topics.get(topic.topic_id)
            if existing:
                kb.duplicates.append((topic.topic_id, existing.kb_name, topic.kb_name))
                continue
            kb.topics[topic.topic_id] = topic
    return kb


def _load_index_yaml(path: Path) -> dict[str, dict]:
    """Load INDEX.yaml; return {topic_id: metadata_dict}. Empty if missing/invalid."""
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    topics = data.get("topics", [])
    if not isinstance(topics, list):
        return {}
    out: dict[str, dict] = {}
    for entry in topics:
        if isinstance(entry, dict) and "id" in entry:
            out[entry["id"]] = entry
    return out


def _enrich_with_meta(topic: Topic, meta: dict | None) -> None:
    if not meta:
        return
    topic.band = str(meta.get("band", "") or "")
    topic.solves_symptoms = list(meta.get("solves_symptoms") or [])
    topic.inputs = list(meta.get("inputs") or [])
    topic.outputs = list(meta.get("outputs") or [])
    topic.related = list(meta.get("related") or [])


def _parse_index(index_path: Path, kb_name: str) -> Iterable[Topic]:
    lines = index_path.read_text(encoding="utf-8").splitlines()
    i = 0
    n = len(lines)
    while i < n:
        m = _TOPIC_RE.match(lines[i])
        if not m:
            i += 1
            continue
        topic_id = m.group(1)
        title = ""
        when = ""
        file_rel = ""
        j = i + 1
        while j < n and not _TOPIC_RE.match(lines[j]):
            line = lines[j].strip()
            if not title and line.startswith("**") and line.endswith("**") and len(line) > 4:
                title = line.strip("*").strip()
            elif not when and line.lower().startswith("quando usarlo"):
                when = line.split(":", 1)[1].strip() if ":" in line else ""
            elif not file_rel:
                fm = _FILE_RE.match(lines[j])
                if fm:
                    file_rel = (fm.group(1) or fm.group(2)).strip()
            j += 1
        if file_rel:
            yield Topic(
                topic_id=topic_id,
                kb_name=kb_name,
                title=title,
                when_to_use=when,
                file_rel=file_rel,
            )
        i = j
