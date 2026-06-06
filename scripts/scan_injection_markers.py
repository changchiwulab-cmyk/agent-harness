#!/usr/bin/env python3
"""Prompt-injection marker scanner (AGI-2: 20260606-B01).

Read-only detector for the sentinels that show up when external content (web
search results, fetched files, tool output) tries to hijack the agent —
OWASP ASI01 prompt injection. Per the harness's "可控 > 能力" stance and to
avoid false-positive blocking on legitimate text (a report *about* injection
quotes these very phrases), this is a DETECTION LIBRARY used by the red-team
test suite, NOT a runtime-blocking hook and NOT a CI gate over drafts.

Public API: ``scan_text(text) -> list[(pattern_id, matched_snippet)]``.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# (id, compiled pattern). Curated to catch goal/permission hijack + data
# masquerading as instructions, while staying narrow enough to be meaningful.
_PATTERNS_RAW = [
    ("ignore_previous", r"ignore\s+(all\s+|the\s+)?(previous|prior|above)\s+(instruction|prompt|context|rule)"),
    ("disregard", r"disregard\s+(all\s+)?(previous|prior|the\s+above)"),
    ("role_override", r"you\s+are\s+now\b|you'?re\s+now\b|pretend\s+to\s+be\b"),
    ("fake_system_turn", r"(^|\n)\s*system\s*:|</?system>"),
    ("new_instructions", r"new\s+instructions?\s*:"),
    ("goal_hijack", r"(change|update|modify|ignore|replace)\s+(your\s+)?(goal|objective|definition_of_done|task\s+card)"),
    ("permission_bypass", r"(override|bypass|disable|turn\s+off)\s+(the\s+)?(permission|guardrail|safety|approval|deny)"),
    ("secret_exfil", r"(exfiltrate|leak|send|post|upload)\b[^\n]{0,40}\b(http|api[_\s-]?key|secret|token|password|credential)"),
    ("hidden_from_user", r"(do\s+not|don'?t|without)\s+(tell|inform|notify|alert|mention\s+to)\s+(the\s+)?user"),
    ("fake_tool_call", r"<tool_call>|<function_call>|```tool_code"),
]
PATTERNS = [(pid, re.compile(rx, re.IGNORECASE | re.MULTILINE)) for pid, rx in _PATTERNS_RAW]


def scan_text(text: str) -> list[tuple[str, str]]:
    """Return [(pattern_id, matched_snippet)] for every injection sentinel hit."""
    hits: list[tuple[str, str]] = []
    for pid, pat in PATTERNS:
        for m in pat.finditer(text or ""):
            hits.append((pid, m.group(0).strip()))
    return hits


def scan_file(path: Path) -> list[tuple[str, str]]:
    try:
        return scan_text(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="files to scan (default: read stdin)")
    args = parser.parse_args(argv)

    total = 0
    if args.paths:
        for p in args.paths:
            for pid, snippet in scan_file(p):
                total += 1
                print(f"{p}: [{pid}] {snippet!r}")
    else:
        for pid, snippet in scan_text(sys.stdin.read()):
            total += 1
            print(f"<stdin>: [{pid}] {snippet!r}")
    print(f"scan_injection_markers: {total} marker(s) found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
