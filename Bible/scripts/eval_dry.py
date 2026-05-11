#!/usr/bin/env python3
"""Dry-run evaluator: for each case in eval/eval_cases.yaml, runs the routing
engine on `expected_initial_analysis` and compares the top match against
`expected_pipeline[0]`.

Does NOT touch Blender. Useful to detect regressions in routing rules /
playbook references without a full Blender run.

Usage:
    cd Bible
    BLENDER_KB_PATH=$PWD python scripts/eval_dry.py

Exit code: 0 if all cases pass, 1 otherwise.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Allow `import blender_kb...` when run from inside Bible/
HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parent.parent.parent  # Bible/scripts/eval_dry.py -> repo root
sys.path.insert(0, str(REPO_ROOT / "src"))

import yaml  # noqa: E402

from blender_kb.kb import build_index, resolve_root  # noqa: E402
from blender_kb.routing import next_action, route  # noqa: E402


def main() -> int:
    root = resolve_root()
    kb = build_index(root)
    rules = kb.load_routing_rules()
    if not rules:
        print("WARNING: no routing rules loaded — every case will be 'ready'.")

    cases_path = root / "eval" / "eval_cases.yaml"
    if not cases_path.is_file():
        print(f"FAIL: eval cases file not found: {cases_path}")
        return 1
    cases = (yaml.safe_load(cases_path.read_text(encoding="utf-8")) or {}).get("cases", [])
    if not cases:
        print("WARNING: no cases in eval_cases.yaml")
        return 0

    failed = 0
    for case in cases:
        name = case.get("name", "?")
        analysis = case.get("expected_initial_analysis") or {}
        expected_pipeline = case.get("expected_pipeline") or []
        matched = route(analysis, rules)
        na = next_action(matched, analysis)

        # Compare with the first expected step.
        if not expected_pipeline:
            status = "SKIP"
            note = "no expected_pipeline"
        else:
            first = expected_pipeline[0]
            ok = True
            mismatch = []
            if "tool" in first and first["tool"] != na.get("tool"):
                ok = False
                mismatch.append(f"tool: expected {first['tool']!r}, got {na.get('tool')!r}")
            if "rule_id" in first and matched:
                if matched[0].get("id") != first["rule_id"]:
                    ok = False
                    mismatch.append(f"rule_id: expected {first['rule_id']!r}, got {matched[0].get('id')!r}")
            if "playbook" in first:
                top_playbook = matched[0].get("playbook") if matched else None
                if top_playbook != first["playbook"]:
                    ok = False
                    mismatch.append(f"playbook: expected {first['playbook']!r}, got {top_playbook!r}")
            status = "OK" if ok else "FAIL"
            note = "" if ok else "; ".join(mismatch)
            if not ok:
                failed += 1

        prefix = {"OK": "[OK]", "FAIL": "[FAIL]", "SKIP": "[SKIP]"}[status]
        print(f"{prefix} {name}: matched_rules={[m['id'] for m in matched]} next={na.get('tool')} {('-- ' + note) if note else ''}")

    print()
    if failed:
        print(f"{failed} case(s) failed.")
        return 1
    print("All cases passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
