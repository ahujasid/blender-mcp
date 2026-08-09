"""Strip credential-like substrings from outbound telemetry payloads."""
from __future__ import annotations

import hashlib
import re
from typing import Any

# Order matters: more specific first
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("github_pat", re.compile(r"\bghp_[A-Za-z0-9]{20,}\b")),
    ("github_oauth", re.compile(r"\bgho_[A-Za-z0-9]{20,}\b")),
    ("github_fine_grained", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("openai_sk", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("anthropic", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("supabase_publishable", re.compile(r"\bsb_publishable_[A-Za-z0-9_-]+\b")),
    ("supabase_secret", re.compile(r"\bsb_secret_[A-Za-z0-9_-]+\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    (
        "generic_api_key_assign",
        re.compile(
            r"(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?token)\b\s*[:=]\s*['\"]?([^\s'\"]{12,})"
        ),
    ),
    ("bearer", re.compile(r"(?i)\bBearer\s+([A-Za-z0-9._\-+/=]{16,})")),
]


def _hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()[:16]


def redact_text(text: str | None) -> tuple[str | None, bool, list[str]]:
    """Return (redacted_text, secret_like, kinds)."""
    if not text:
        return text, False, []
    kinds: list[str] = []
    out = text
    for kind, pat in _PATTERNS:
        def repl(m: re.Match[str], _kind: str = kind) -> str:
            raw = m.group(0)
            # prefer last group if assignment-style
            if m.lastindex:
                raw = m.group(m.lastindex) or m.group(0)
            kinds.append(_kind)
            return f"[REDACTED:{_kind}:{_hash_secret(raw)}]"

        new_out, n = pat.subn(repl, out)
        if n:
            out = new_out
    # unique kinds preserve order
    seen: set[str] = set()
    uniq: list[str] = []
    for k in kinds:
        if k not in seen:
            seen.add(k)
            uniq.append(k)
    return out, bool(uniq), uniq


def redact_metadata(meta: dict[str, Any] | None) -> tuple[dict[str, Any] | None, bool, list[str]]:
    if not meta:
        return meta, False, []
    import json

    try:
        raw = json.dumps(meta, ensure_ascii=False, default=str)
    except Exception:
        raw = str(meta)
    redacted, secret_like, kinds = redact_text(raw)
    if not secret_like:
        return meta, False, []
    try:
        return json.loads(redacted), True, kinds
    except Exception:
        return {"_redacted": redacted}, True, kinds
