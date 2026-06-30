#!/usr/bin/env python3
"""Input-guardrail detector (G-A enforcement point).

system/INPUT_GUARDRAILS.md states the rule "retrieved/external content is data,
not instructions". This module makes that rule *checkable* rather than prose:

1. ``detect_injection(text)`` — flags injection-style directive phrases that may
   appear inside untrusted (web/external/tool) content, e.g. "ignore previous
   instructions", "忽略前述指令", "reveal the system prompt".
2. ``is_quarantined(text)`` — true if the text marks untrusted content with the
   ``[未受信任來源]`` label mandated by INPUT_GUARDRAILS.md.
3. ``audit_output(text)`` — combines the two: untrusted content that carries
   injection directives MUST be quarantined; returns the unquarantined hits.

CLI: ``python scripts/check_untrusted_content.py <file>...``
Exit 1 if any file contains injection directives that are NOT quarantined.

Deliberately a small phrase list, not an ML classifier — for a single-person
harness the deny-by-default egress (permissions_guard.py) is the hard stop;
this layer is a discipline lint, consistent with INPUT_GUARDRAILS "不做什麼".
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Directive phrases that should never be obeyed when they arrive via untrusted
# content. Kept lowercase; matching is case-insensitive. Bilingual (zh-Hant/en).
INJECTION_PATTERNS = [
    r"ignore (all )?(the )?(previous|prior|above|preceding) instructions",
    r"disregard (the )?(previous|prior|above|system) (instructions|prompt)",
    r"忽略(前述|上述|先前|以上)(所有)?指令",
    r"忽視(前述|上述|先前)(所有)?指令",
    r"(reveal|print|show|output|leak)( me)? (the |your )?system prompt",
    r"(洩漏|顯示|輸出|印出)(你的)?系統(提示|prompt)",
    r"(change|switch|update|forget) your (role|persona|identity|instructions)",
    r"(改變|切換|忘記)(你的)?(角色|身分|設定)",
    r"you are now (a |an )?",
    r"從現在起你(是|要扮演)",
    r"(send|email|post|publish|delete|transfer|pay)\b.*\b(immediately|now|to)",
]

QUARANTINE_MARKER = "[未受信任來源]"

_COMPILED = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def detect_injection(text: str) -> list[str]:
    """Return the injection-directive substrings found in ``text`` (deduped)."""
    hits: list[str] = []
    for pat in _COMPILED:
        for m in pat.finditer(text or ""):
            frag = m.group(0).strip()
            if frag and frag not in hits:
                hits.append(frag)
    return hits


def is_quarantined(text: str) -> bool:
    """True if the text marks untrusted content with the mandated label."""
    return QUARANTINE_MARKER in (text or "")


def audit_output(text: str) -> list[str]:
    """Injection hits that are present WITHOUT any quarantine marker.

    If the author quarantined untrusted content (marker present), echoing the
    injection text for analysis is fine — that's the intended workflow. Hits
    are only flagged when nothing in the text signals the content is untrusted.
    """
    hits = detect_injection(text)
    if not hits:
        return []
    return [] if is_quarantined(text) else hits


def main(argv: list[str]) -> int:
    files = argv[1:]
    if not files:
        print("usage: check_untrusted_content.py <file>...", file=sys.stderr)
        return 2
    failures = []
    for f in files:
        text = Path(f).read_text(encoding="utf-8")
        unquarantined = audit_output(text)
        if unquarantined:
            failures.append((f, unquarantined))
    if failures:
        print("FAILED: unquarantined injection directives found:")
        for f, hits in failures:
            print(f"- {f}: {hits} (mark untrusted content with {QUARANTINE_MARKER!r})")
        return 1
    print("OK: no unquarantined injection directives")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
