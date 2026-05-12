"""FastMCP server exposing the local Bible/ Knowledge Base.

Tools:
  kb_status()                                              -> KB root + stats
  kb_list_topics(kb_name?, band?, solves_symptom?)         -> indexed topics
  kb_get_topic(topic_id, max_chars?)                       -> full markdown
  kb_search(query, kb_name?, max_results?, context_lines?) -> grep snippets
  kb_read(relative_path, max_chars?)                       -> escape hatch
  kb_route(analysis_json)                                  -> action routing
  kb_list_playbooks()                                      -> available playbooks
  kb_get_playbook(playbook_id)                             -> single playbook
  kb_list_sessions(limit?, with_summary?)                  -> recent session logs
  kb_get_session(session_id)                               -> full session log

Prompts:
  kb_bootstrap()  -> CLAUDE.md + SYSTEM_PROMPT.md + INDEX summaries, intended as
                     the first message of a session.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .kb import (
    ENV_VAR,
    KBError,
    KBNotFound,
    KBPathEscape,
    KnowledgeBase,
    build_index,
    resolve_root,
)
from .routing import next_action, route, summarize_analysis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("BlenderKB")

mcp = FastMCP("blender-kb")

# Lazy-loaded singleton. The KB is small (text files) so a single load is fine,
# but defer it so import doesn't fail when the env var is missing.
_KB: KnowledgeBase | None = None
_KB_ERROR: str | None = None


def _get_kb() -> KnowledgeBase:
    global _KB, _KB_ERROR
    if _KB is not None:
        return _KB
    try:
        root = resolve_root()
        _KB = build_index(root)
        logger.info(
            "KB loaded: root=%s, sub-KBs=%s, topics=%d",
            root, list(_KB.kbs.keys()), len(_KB.topics),
        )
        return _KB
    except KBError as e:
        _KB_ERROR = str(e)
        raise


def _reset_for_tests() -> None:
    """Reset the singleton (used in tests, not exposed to MCP)."""
    global _KB, _KB_ERROR
    _KB = None
    _KB_ERROR = None


def _truncate(text: str, max_chars: int | None) -> tuple[str, bool]:
    if max_chars is None or max_chars <= 0 or len(text) <= max_chars:
        return text, False
    return text[:max_chars], True


# --------------------------------- tools -------------------------------------

@mcp.tool()
def kb_status() -> str:
    """Report the KB root currently in use and basic stats.

    Use this first if you don't know whether the KB is reachable.
    """
    try:
        kb = _get_kb()
    except KBError as e:
        return json.dumps({
            "ok": False,
            "error": str(e),
            "env_var": ENV_VAR,
            "env_value": os.environ.get(ENV_VAR),
            "cwd": str(Path.cwd()),
        }, indent=2)
    return json.dumps({
        "ok": True,
        "root": str(kb.root),
        "sub_kbs": kb.list_kbs(),
        "topic_count": len(kb.topics),
        "duplicate_topic_ids": kb.duplicates,
        "env_var": ENV_VAR,
        "env_value": os.environ.get(ENV_VAR),
    }, indent=2)


@mcp.tool()
def kb_list_topics(
    kb_name: str | None = None,
    band: str | None = None,
    solves_symptom: str | None = None,
) -> str:
    """List indexed topics with short summary, with optional filters.

    Parameters:
    - kb_name: restrict to one sub-KB (e.g. "Blender for 3d print documentation").
               Use kb_status() to see available sub-KBs.
    - band:    "A" = core print-prep workflow, "B" = adjacent / reference.
               Archived (band "C") topics are stored in `_archive/` and are
               never returned by this tool.
    - solves_symptom: filter to topics that address a specific symptom from the
               analyze_mesh_for_print output, e.g. "non_manifold_edges",
               "disconnected_shells", "polycount_high", "dimensions_wrong".

    Returns JSON: [{topic_id, kb_name, title, when_to_use, file_rel, band,
                   solves_symptoms, related}, ...]
    """
    try:
        kb = _get_kb()
    except KBError as e:
        return f"Error: {e}"
    topics = kb.list_topics(
        kb_name=kb_name, band=band, solves_symptom=solves_symptom,
    )
    if kb_name and not topics and not band and not solves_symptom:
        available = ", ".join(kb.list_kbs())
        return f"Error: no topics for kb_name={kb_name!r}. Available: {available}"
    return json.dumps([
        {
            "topic_id": t.topic_id,
            "kb_name": t.kb_name,
            "title": t.title,
            "when_to_use": t.when_to_use,
            "file_rel": t.file_rel,
            "band": t.band,
            "solves_symptoms": t.solves_symptoms,
            "related": t.related,
        }
        for t in topics
    ], indent=2, ensure_ascii=False)


@mcp.tool()
def kb_get_topic(topic_id: str, max_chars: int = 0) -> str:
    """Return the full markdown of a KB topic document.

    Parameters:
    - topic_id: the bracketed id from an INDEX.md, e.g. "mesh_repair", "fdm_printing_constraints".
                Use kb_list_topics() to discover.
    - max_chars: optional truncation (0 = no limit). If truncated, a note is appended.

    Returns the raw markdown (or an Error: ... string on failure).
    """
    try:
        kb = _get_kb()
        topic, content = kb.get_topic(topic_id)
    except KBNotFound as e:
        return f"Error: {e}"
    except KBError as e:
        return f"Error: {e}"
    text, truncated = _truncate(content, max_chars if max_chars > 0 else None)
    header = (
        f"# Topic [{topic.topic_id}] from {topic.kb_name}\n"
        f"# File: {topic.file_rel}\n\n"
    )
    if truncated:
        text += f"\n\n[... truncated at {max_chars} chars; re-call with larger max_chars or use kb_read with offset]"
    return header + text


@mcp.tool()
def kb_search(
    query: str,
    kb_name: str | None = None,
    max_results: int = 10,
    context_lines: int = 2,
) -> str:
    """Case-insensitive substring search across indexed topic documents.

    Parameters:
    - query: substring to search for.
    - kb_name: optional, restrict to one sub-KB.
    - max_results: cap on total matches returned (default 10).
    - context_lines: lines of context before/after each match (default 2).

    Returns JSON list of matches; each match has {topic_id, kb_name, file_rel, line_no, snippet}.
    """
    try:
        kb = _get_kb()
    except KBError as e:
        return f"Error: {e}"
    if not query or not query.strip():
        return "Error: empty query"
    results = kb.search(
        query=query,
        kb_name=kb_name,
        max_results=max(1, max_results),
        context_lines=max(0, context_lines),
    )
    return json.dumps({
        "query": query,
        "kb_name": kb_name,
        "count": len(results),
        "results": results,
    }, indent=2, ensure_ascii=False)


@mcp.tool()
def kb_read(relative_path: str, max_chars: int = 0) -> str:
    """Read any file under the KB root by relative path. Use for files NOT indexed
    by topic_id (e.g. FIELD_NOTES.md, SYSTEM_PROMPT.md, Printer Infos/*.md).

    Parameters:
    - relative_path: path relative to KB root, e.g.
        "Blender for 3d print documentation/FIELD_NOTES.md"
        "Bambu Wiki documentation/Printer Infos/a1_specs.md"
        "CLAUDE.md"
      Absolute paths and traversal outside the KB root are rejected.
    - max_chars: optional truncation (0 = no limit).

    Returns the raw text (or an Error: ... string on failure).
    """
    try:
        kb = _get_kb()
        _, content = kb.read_relative(relative_path)
    except KBPathEscape as e:
        return f"Error: {e}"
    except KBNotFound as e:
        return f"Error: {e}"
    except KBError as e:
        return f"Error: {e}"
    text, truncated = _truncate(content, max_chars if max_chars > 0 else None)
    if truncated:
        text += f"\n\n[... truncated at {max_chars} chars]"
    return text


# --------------------------------- routing -----------------------------------

@mcp.tool()
def kb_route(analysis_json: str) -> str:
    """Map the output of `analyze_mesh_for_print` to a sequence of cleanup actions.

    Loads the routing rules from each sub-KB's `routing_rules.yaml`, evaluates
    them against the analysis, and returns the matched rules sorted by priority
    descending, plus a `next_action` directly executable by the assistant.

    Parameters:
    - analysis_json: the JSON string returned by `analyze_mesh_for_print`
      (or any dict-compatible JSON with the same keys: vertex_count,
       face_count, non_manifold_edges, boundary_loops, disconnected_shells,
       degenerate_faces, normals, dimensions_mm, ready_to_slice, ...).

    Returns JSON with:
      input_summary  : echo of the analysis keys that drove the decision
      matched_rules  : list of {id, priority, topic_id, section, playbook,
                                expected_after, rationale, needs_user_input}
      next_action    : {tool, args, ...} — what to do next

    Use this BEFORE deciding which topic to load. It will tell you the exact
    topic_id + playbook to fetch, or signal `ask_user` for ambiguous cases.
    """
    try:
        kb = _get_kb()
    except KBError as e:
        return f"Error: {e}"

    if not analysis_json or not analysis_json.strip():
        return "Error: empty analysis_json"
    try:
        analysis = json.loads(analysis_json)
    except json.JSONDecodeError as e:
        return f"Error: analysis_json is not valid JSON: {e}"
    if not isinstance(analysis, dict):
        return f"Error: analysis_json must be a JSON object, got {type(analysis).__name__}"

    rules = kb.load_routing_rules()
    matched = route(analysis, rules)
    return json.dumps({
        "input_summary": summarize_analysis(analysis),
        "matched_rules": matched,
        "next_action": next_action(matched, analysis),
        "rules_loaded": len(rules),
    }, indent=2, ensure_ascii=False)


@mcp.tool()
def kb_list_playbooks() -> str:
    """List available playbooks under <root>/playbooks/.

    A playbook is a JSON file with a deterministic sequence of cleanup steps
    (e.g. repair_basic, decimate_to_target). Use `kb_get_playbook(id)` to
    fetch the actual steps.

    Returns JSON: [{id, file, title, when_to_use, step_count}, ...]
    """
    try:
        kb = _get_kb()
    except KBError as e:
        return f"Error: {e}"
    return json.dumps(kb.list_playbooks(), indent=2, ensure_ascii=False)


@mcp.tool()
def kb_get_playbook(playbook_id: str) -> str:
    """Return the full JSON of a playbook (steps + metadata).

    Parameters:
    - playbook_id: filename stem of a playbook under <root>/playbooks/,
      e.g. "repair_basic", "decimate_to_target".

    Returns the playbook JSON or an Error: ... string.
    """
    try:
        kb = _get_kb()
        data = kb.get_playbook(playbook_id)
    except KBNotFound as e:
        return f"Error: {e}"
    except KBError as e:
        return f"Error: {e}"
    return json.dumps(data, indent=2, ensure_ascii=False)


# --------------------------------- sessions ----------------------------------

@mcp.tool()
def kb_list_sessions(limit: int = 10, with_summary: bool = False) -> str:
    """List the most recent session logs in Bible/sessions/, newest first.

    Sessions are written automatically by the MCP at the end of every
    print-prep workflow (see learning_loop.md). They are the input to
    cross-session pattern review.

    Parameters:
    - limit: how many recent sessions to return (default 10).
    - with_summary: if True, also include step_count, rules_fired list,
      final_ready_to_slice, final_face_count for each session. Useful for
      a richer overview at the cost of a bit more JSON.

    Returns JSON list of session entries with id, file, started, duration_s,
    status, use_case, satisfaction (and the summary fields if requested).
    """
    try:
        kb = _get_kb()
    except KBError as e:
        return f"Error: {e}"
    sessions = kb.list_sessions(limit=max(1, limit), with_summary=with_summary)
    return json.dumps(sessions, indent=2, ensure_ascii=False)


@mcp.tool()
def kb_get_session(session_id: str) -> str:
    """Return the full parsed session log YAML as JSON.

    Use this after `kb_list_sessions` to drill into a specific session
    (e.g. for cross-session review or comparison).

    Parameters:
    - session_id: filename stem of a session log under Bible/sessions/,
      e.g. "2026-05-11_dragon_v1".

    Returns the session dict (kickoff, scene_initial, steps[],
    final_analysis, output, feedback, introspection) as JSON.
    """
    try:
        kb = _get_kb()
        data = kb.get_session(session_id)
    except KBNotFound as e:
        return f"Error: {e}"
    except KBError as e:
        return f"Error: {e}"
    return json.dumps(data, indent=2, ensure_ascii=False)


# --------------------------------- prompt ------------------------------------

@mcp.prompt()
def kb_bootstrap() -> str:
    """Bootstrap prompt: returns CLAUDE.md + SYSTEM_PROMPT.md + a compact summary
    of available topic ids. Intended as the first message of a new session so the
    assistant knows the KB layout and operating rules before any task."""
    try:
        kb = _get_kb()
    except KBError as e:
        return f"KB unavailable: {e}. Set ${ENV_VAR} and retry."
    parts: list[str] = []
    parts.append(
        "# KB Bootstrap\n"
        f"KB root: `{kb.root}`\n"
        f"Sub-KBs: {', '.join(kb.list_kbs())}\n"
        f"Indexed topics: {len(kb.topics)}\n\n"
        "**Read FIRST**: `kb_get_topic('mcp_blind_operating_protocol')` — "
        "explains how to operate without viewport access (you are blind!), "
        "the 4 senses available (analyze JSON / Toolbox report / screenshot / "
        "Python introspection), and the T+0 session kickoff sequence.\n\n"
        "Then read in order:\n"
        "1. `session_kickoff_template` — parsing user kickoff input\n"
        "2. `use_case_taxonomy` — defaults per use_case (display/mech/.../tool_print)\n"
        "3. `analyze_to_action` — decision tree from analyze_mesh_for_print JSON\n"
        "4. `learning_loop` — write session log + post-mortem at end\n\n"
        "Core tools: `kb_list_topics`, `kb_get_topic`, `kb_search`, `kb_read`, "
        "`kb_route` (routing), `kb_get_playbook` (executable sequences), "
        "`kb_list_sessions`/`kb_get_session` (cross-session review on demand).\n"
        "Do not write Blender code without first reading the relevant topic.\n"
    )
    for fname in ("CLAUDE.md", "SYSTEM_PROMPT.md"):
        try:
            _, body = kb.read_relative(fname)
            parts.append(f"\n---\n## {fname}\n\n{body}")
        except KBError:
            continue
    # Compact topic table per KB
    for kb_name in kb.list_kbs():
        parts.append(f"\n---\n## Topics in {kb_name}\n")
        for t in kb.list_topics(kb_name=kb_name):
            parts.append(f"- `[{t.topic_id}]` {t.title or '(no title)'}")
    return "\n".join(parts)


# --------------------------------- main --------------------------------------

def main() -> None:
    """Run the blender-kb MCP server (stdio transport)."""
    # Eagerly try to load so errors surface in the host's logs at startup.
    try:
        _get_kb()
    except KBError as e:
        logger.warning("KB not loaded at startup: %s", e)
    mcp.run()


if __name__ == "__main__":
    main()
