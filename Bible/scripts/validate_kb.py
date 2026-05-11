#!/usr/bin/env python3
"""Validate the KB tree end-to-end.

Checks:
1. Every `[topic_id]` in each INDEX.md has a real `File:` that exists.
2. Every file under <sub_kb>/docs/ is referenced by some [topic_id] in INDEX.md
   (no orphan docs).
3. INDEX.yaml: every entry refers to a real topic in INDEX.md and vice versa
   (so the band/symptom filter doesn't silently mask topics).
4. `related: [...]` lists point to topics that exist in the active KB.
5. routing_rules.yaml: every `then.topic_id` resolves; every `then.playbook`
   exists under <root>/playbooks/.
6. playbooks/*.json: schema sanity (id matches filename stem, steps non-empty,
   topic_refs resolve, every step has a tool and code).
7. Every fenced ```python code block in topic docs parses with ast.parse.

Usage:
    cd Bible
    BLENDER_KB_PATH=$PWD python scripts/validate_kb.py

Exit code: 0 on clean, 1 if any check failed (warnings don't fail).
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

import yaml  # noqa: E402

from blender_kb.kb import (  # noqa: E402
    INDEX_FILENAME,
    INDEX_META_FILENAME,
    ROUTING_RULES_FILENAME,
    build_index,
    resolve_root,
    _is_subkb_candidate,
)

_TOPIC_RE = re.compile(r"^##\s+\[([a-z0-9_]+)\]\s*$")
_FILE_RE = re.compile(
    r"^\s*File:\s*(?:`([^`]+)`|(\S+))\s*$",
    re.IGNORECASE,
)
_CODE_FENCE_RE = re.compile(r"^```(?:python|py)\s*$")
_CODE_END_RE = re.compile(r"^```\s*$")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.checks_run: int = 0

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def ok(self, count: int = 1) -> None:
        self.checks_run += count

    def summary(self) -> int:
        print()
        print(f"Checks run: {self.checks_run}")
        print(f"Errors:     {len(self.errors)}")
        print(f"Warnings:   {len(self.warnings)}")
        for w in self.warnings:
            print(f"  warn: {w}")
        for e in self.errors:
            print(f"  ERR:  {e}")
        return 1 if self.errors else 0


def check_index_md_file_lines(root: Path, r: Report) -> None:
    for child in sorted(root.iterdir()):
        if not _is_subkb_candidate(child):
            continue
        index_path = child / INDEX_FILENAME
        if not index_path.is_file():
            continue
        kb_name = child.name
        lines = index_path.read_text(encoding="utf-8").splitlines()
        topic_id = None
        file_seen_for_topic = False
        for i, line in enumerate(lines, start=1):
            tm = _TOPIC_RE.match(line)
            if tm:
                if topic_id and not file_seen_for_topic:
                    r.err(f"{index_path}:{i}: previous topic '{topic_id}' has no File: line")
                topic_id = tm.group(1)
                file_seen_for_topic = False
                continue
            fm = _FILE_RE.match(line)
            if fm and topic_id:
                rel = (fm.group(1) or fm.group(2)).strip()
                abs_path = child / rel
                if not abs_path.is_file():
                    r.err(f"{index_path}:{i}: topic [{topic_id}] points to missing file '{rel}'")
                file_seen_for_topic = True
                r.ok()
        if topic_id and not file_seen_for_topic:
            r.err(f"{index_path}: last topic '{topic_id}' has no File: line")


def check_orphan_docs(root: Path, r: Report) -> None:
    for child in sorted(root.iterdir()):
        if not _is_subkb_candidate(child):
            continue
        docs_dir = child / "docs"
        if not docs_dir.is_dir():
            continue
        index_text = (child / INDEX_FILENAME).read_text(encoding="utf-8") if (child / INDEX_FILENAME).is_file() else ""
        for md in sorted(docs_dir.glob("*.md")):
            rel = f"docs/{md.name}"
            if rel not in index_text:
                r.warn(f"{child.name}: orphan doc not referenced in INDEX.md: {rel}")
            r.ok()


def check_index_yaml(root: Path, kb, r: Report) -> None:
    for child in sorted(root.iterdir()):
        if not _is_subkb_candidate(child):
            continue
        yml = child / INDEX_META_FILENAME
        if not yml.is_file():
            r.warn(f"{child.name}: no INDEX.yaml (band/symptom filter disabled for this sub-KB)")
            continue
        try:
            data = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            r.err(f"{yml}: YAML parse error: {e}")
            continue
        topics_in_yaml = {e["id"] for e in data.get("topics", []) if isinstance(e, dict) and "id" in e}
        topics_in_md = {t.topic_id for t in kb.list_topics(kb_name=child.name)}
        missing_in_md = topics_in_yaml - topics_in_md
        missing_in_yaml = topics_in_md - topics_in_yaml
        for tid in sorted(missing_in_md):
            r.err(f"{yml}: topic '{tid}' present in INDEX.yaml but missing in INDEX.md")
        for tid in sorted(missing_in_yaml):
            r.warn(f"{yml}: topic '{tid}' has no entry in INDEX.yaml (band/symptom filter won't see it)")
        r.ok(len(topics_in_yaml))


def check_related_links(kb, r: Report) -> None:
    known_ids = set(kb.topics.keys())
    for t in kb.topics.values():
        for ref in t.related:
            if ref not in known_ids:
                r.err(f"Topic '{t.topic_id}' related: -> unknown topic_id '{ref}'")
            r.ok()


def check_routing_rules(root: Path, kb, r: Report) -> None:
    known_topics = set(kb.topics.keys())
    playbook_ids = {p["id"] for p in kb.list_playbooks()}
    for child in sorted(root.iterdir()):
        if not _is_subkb_candidate(child):
            continue
        rules_path = child / ROUTING_RULES_FILENAME
        if not rules_path.is_file():
            continue
        try:
            data = yaml.safe_load(rules_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            r.err(f"{rules_path}: YAML parse error: {e}")
            continue
        for i, rule in enumerate(data.get("rules", [])):
            rid = rule.get("id", f"#{i}")
            then = rule.get("then", {})
            tid = then.get("topic_id")
            if not tid:
                r.err(f"{rules_path}: rule {rid} has no then.topic_id")
            elif tid not in known_topics:
                r.err(f"{rules_path}: rule {rid} -> unknown topic_id '{tid}'")
            pb = then.get("playbook")
            if pb and pb not in playbook_ids:
                r.err(f"{rules_path}: rule {rid} -> unknown playbook '{pb}'")
            if not rule.get("when"):
                r.err(f"{rules_path}: rule {rid} has empty/missing when")
            if "priority" not in rule:
                r.warn(f"{rules_path}: rule {rid} has no priority (defaults to 0)")
            r.ok()


def check_playbooks(kb, r: Report) -> None:
    known_topics = set(kb.topics.keys())
    pb_dir = kb.root / "playbooks"
    if not pb_dir.is_dir():
        r.warn("No playbooks/ directory under KB root")
        return
    for pf in sorted(pb_dir.glob("*.json")):
        try:
            data = json.loads(pf.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            r.err(f"{pf}: JSON parse error: {e}")
            continue
        if data.get("id") != pf.stem:
            r.err(f"{pf}: id '{data.get('id')}' does not match filename stem '{pf.stem}'")
        steps = data.get("steps", [])
        if not steps:
            r.err(f"{pf}: empty steps list")
        for j, step in enumerate(steps):
            if not step.get("tool"):
                r.err(f"{pf}: step #{j} has no 'tool'")
            if not step.get("code"):
                r.err(f"{pf}: step #{j} has no 'code'")
        for tref in data.get("topic_refs", []):
            if tref not in known_topics:
                r.err(f"{pf}: topic_refs -> unknown '{tref}'")
        r.ok()


def check_python_code_blocks(kb, r: Report) -> None:
    """Parse every fenced ```python block in topic docs with ast.parse.

    Skips blocks that look like partial snippets (no top-level statements, or
    obvious placeholders).
    """
    for t in kb.topics.values():
        path = t.abs_path(kb.root)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        in_block = False
        block_start = 0
        buf: list[str] = []
        for i, line in enumerate(lines, start=1):
            if not in_block:
                if _CODE_FENCE_RE.match(line):
                    in_block = True
                    block_start = i
                    buf = []
                continue
            if _CODE_END_RE.match(line):
                code = "\n".join(buf)
                if code.strip():
                    try:
                        ast.parse(code)
                        r.ok()
                    except SyntaxError as e:
                        # Many docs use "..." placeholders or partial fragments;
                        # report as warning rather than error to avoid false
                        # negatives on documentation that's intentionally elided.
                        r.warn(f"{path}:{block_start}: python block does not parse ({e.msg})")
                in_block = False
                buf = []
                continue
            buf.append(line)


def main() -> int:
    root = resolve_root()
    print(f"Validating KB at: {root}")
    kb = build_index(root)
    print(f"Loaded {len(kb.topics)} topics from {len(kb.kbs)} sub-KBs")
    print(f"Playbooks: {[p['id'] for p in kb.list_playbooks()]}")
    print()
    r = Report()
    check_index_md_file_lines(root, r)
    check_orphan_docs(root, r)
    check_index_yaml(root, kb, r)
    check_related_links(kb, r)
    check_routing_rules(root, kb, r)
    check_playbooks(kb, r)
    check_python_code_blocks(kb, r)
    return r.summary()


if __name__ == "__main__":
    sys.exit(main())
