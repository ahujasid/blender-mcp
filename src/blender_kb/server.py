"""FastMCP server exposing the local Bible/ Knowledge Base.

Tools:
  kb_status()                              -> KB root, KB folders, topic count
  kb_list_topics(kb_name?)                 -> indexed topics with summary
  kb_get_topic(topic_id, max_chars?)       -> full markdown of a topic doc
  kb_search(query, kb_name?, max_results?) -> grep snippets across topic docs
  kb_read(relative_path, max_chars?)       -> read any file under KB root (escape hatch)

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
def kb_list_topics(kb_name: str | None = None) -> str:
    """List indexed topics with short summary.

    Parameters:
    - kb_name: optional, restrict to one sub-KB (e.g. "Blender for 3d print documentation").
               Use kb_status() to see available sub-KBs.

    Returns JSON: [{topic_id, kb_name, title, when_to_use, file_rel}, ...]
    """
    try:
        kb = _get_kb()
    except KBError as e:
        return f"Error: {e}"
    topics = kb.list_topics(kb_name=kb_name)
    if kb_name and not topics:
        available = ", ".join(kb.list_kbs())
        return f"Error: no topics for kb_name={kb_name!r}. Available: {available}"
    return json.dumps([
        {
            "topic_id": t.topic_id,
            "kb_name": t.kb_name,
            "title": t.title,
            "when_to_use": t.when_to_use,
            "file_rel": t.file_rel,
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
        "Use the tools `kb_list_topics`, `kb_get_topic`, `kb_search`, `kb_read` "
        "to access the documentation on demand. Do not write Blender code without "
        "first reading the relevant topic.\n"
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
