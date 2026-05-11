"""Routing engine for kb_route.

Takes the JSON output of `analyze_mesh_for_print` and a list of rules
(loaded from each sub-KB's routing_rules.yaml) and returns the rules that
match, sorted by priority descending.

The engine is pure-python and has no MCP dependency, so it's testable on its
own.
"""
from __future__ import annotations

import operator
import re
from typing import Any, Iterable

# Allowed comparison operators for "OP NUM" match expressions.
_OPS = {
    ">":  operator.gt,
    "<":  operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}

# Match expressions like ">= 0.4" / "> 1" / "< 256" / "==5"
_NUM_OP_RE = re.compile(r"^\s*(>=|<=|==|!=|>|<)\s*(-?\d+(?:\.\d+)?)\s*$")


class RoutingError(Exception):
    pass


def derive_metrics(analysis: dict) -> dict:
    """Add convenience metrics on top of the raw analyze_mesh_for_print output.

    The router can match on these too — they are computed once here so the
    rules stay declarative.
    """
    derived = dict(analysis)  # shallow copy
    dims = analysis.get("dimensions_mm") or []
    if isinstance(dims, list) and len(dims) >= 1 and all(isinstance(d, (int, float)) for d in dims):
        derived["max_dimension_mm"] = max(dims)
        derived["min_dimension_mm"] = min(dims)
    edges = analysis.get("edge_count") or 0
    non_man = analysis.get("non_manifold_edges") or 0
    derived["ratio_non_manifold"] = (non_man / edges) if edges > 0 else 0.0
    return derived


def evaluate_rule(rule: dict, metrics: dict) -> bool:
    """Return True iff ALL conditions in rule['when'] match."""
    when = rule.get("when") or {}
    if not when:
        return False
    for key, match_expr in when.items():
        actual = metrics.get(key)
        if not _condition_matches(actual, match_expr):
            return False
    return True


def _condition_matches(actual: Any, match_expr: Any) -> bool:
    """Single-condition match. match_expr can be:
       - a string like ">= 0.4" (numeric comparison)
       - a literal value (exact equality, with bool/str)
    """
    if isinstance(match_expr, str):
        m = _NUM_OP_RE.match(match_expr)
        if m:
            op, num_str = m.group(1), m.group(2)
            try:
                num = float(num_str)
            except ValueError:
                return False
            if actual is None:
                return False
            try:
                return _OPS[op](float(actual), num)
            except (TypeError, ValueError):
                return False
        # Plain string => exact equality
        return actual == match_expr
    # Non-string literal (bool, int, float, list, ...): direct equality
    return actual == match_expr


def route(analysis: dict, rules: Iterable[dict]) -> list[dict]:
    """Evaluate every rule against the analysis and return matches sorted by
    priority descending. Each returned dict contains rule['then'] augmented
    with id/priority/rationale and originating kb_name.
    """
    metrics = derive_metrics(analysis)
    matched: list[dict] = []
    for rule in rules:
        if evaluate_rule(rule, metrics):
            then = dict(rule.get("then") or {})
            matched.append({
                "id": rule.get("id", "?"),
                "priority": int(rule.get("priority", 0)),
                "rationale": (rule.get("rationale") or "").strip(),
                "kb_name": rule.get("kb_name", ""),
                **then,
            })
    matched.sort(key=lambda r: r["priority"], reverse=True)
    return matched


def summarize_analysis(analysis: dict) -> dict:
    """Pick the few keys that matter for a routing decision so we can echo
    them back to the caller without dumping the whole input."""
    keys = (
        "vertex_count", "edge_count", "face_count",
        "non_manifold_edges", "boundary_loops", "disconnected_shells",
        "degenerate_faces", "normals", "watertight",
        "dimensions_mm", "ready_to_slice",
    )
    return {k: analysis[k] for k in keys if k in analysis}


def next_action(matched: list[dict], analysis: dict) -> dict:
    """Translate the top-priority match into a directly-executable next step.

    Returns one of:
      {"tool": "ready", ...}                — nothing to do, mesh is print-ready
      {"tool": "ask_user", ...}             — top rule needs user input
      {"tool": "kb_get_playbook", "args": {"playbook_id": ...}}
      {"tool": "kb_get_topic",    "args": {"topic_id": ...}}
    """
    if not matched:
        if analysis.get("ready_to_slice") is True:
            return {
                "tool": "ready",
                "message": "ready_to_slice=true and no rules matched. Proceed to preprint_validation + export_stl.",
            }
        return {
            "tool": "kb_get_topic",
            "args": {"topic_id": "preprint_validation"},
            "message": "No routing rule matched but ready_to_slice is not true. Run preprint_validation for a finer diagnostic.",
        }

    top = matched[0]
    if top.get("needs_user_input"):
        return {
            "tool": "ask_user",
            "rule_id": top["id"],
            "topic_id": top.get("topic_id"),
            "rationale": top.get("rationale", ""),
            "message": "Top rule requires a decision from the user before any action.",
        }
    if top.get("playbook"):
        return {
            "tool": "kb_get_playbook",
            "args": {"playbook_id": top["playbook"]},
            "rule_id": top["id"],
            "topic_id": top.get("topic_id"),
        }
    return {
        "tool": "kb_get_topic",
        "args": {"topic_id": top["topic_id"]},
        "rule_id": top["id"],
    }
