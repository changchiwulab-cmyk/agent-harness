#!/usr/bin/env python3
"""PreToolUse hook: a *new* formal output requires a backing Task Card.

The self-assessment (§3.1) flagged that硬規則 1「沒有 Task Card，不執行任何任務」
had **0% deterministic enforcement** — it was pure prompt self-restraint. This
guard makes the rule real at the point where it actually matters: creating a
*formal output* under ``outputs/reports/``.

Deterministic rule (Write/Edit tools):
    - Writes outside ``outputs/reports/`` → allow (drafts, logs, code, scratch
      stay frictionless — deliberately, to avoid the §3.3 trap of locking the
      99% low-risk path).
    - Writing/creating a NEW file under ``outputs/reports/`` → allow only if some
      Task Card under ``tasks/`` names that filename in ``expected_output.filename``.
      Otherwise BLOCK ("no Task Card for formal output / 硬規則 1").
    - Editing a report that already exists → allow (it was promoted under
      governance already; amendments such as addenda are legitimate).

Like permissions_guard.py this is a deny-list at one chokepoint, not a sandbox:
false positives (blocking benign work) are worse than the occasional miss.

Output (JSON on stdout): {"decision": "allow"} or {"decision": "block", "reason": ...}
Exit code 2 signals a deterministic block to Claude Code.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = (ROOT / "outputs" / "reports").resolve()
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def report_output_filenames(root: Path) -> set[str]:
    """Filenames a Task Card declares as a *formal report* output.

    Only cards whose ``expected_output.location`` is under ``outputs/reports/``
    count. A card that declares a draft output (``outputs/drafts/foo.md``) must
    NOT authorize creating a same-named formal report (``outputs/reports/foo.md``)
    — formal outputs need their own backing Task Card.
    """
    names: set[str] = set()
    tasks_dir = root / "tasks"
    if not tasks_dir.exists():
        return names
    for path in tasks_dir.rglob("*.yaml"):
        if "TEMPLATE" in path.name:
            continue
        try:
            card = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if not isinstance(card, dict):
            continue
        out = card.get("expected_output") or {}
        location = (out.get("location") or "").strip().rstrip("/")
        fn = (out.get("filename") or "").strip()
        if fn and location.endswith("outputs/reports"):
            names.add(fn)
    return names


def evaluate(file_path: str, root: Path = ROOT) -> tuple[str, str | None]:
    """Return ('allow', None) or ('block', reason) for a Write/Edit target."""
    if not file_path:
        return "allow", None
    target = Path(file_path)
    if not target.is_absolute():
        target = (root / target)
    target = target.resolve()
    reports_dir = (root / "outputs" / "reports").resolve()

    try:
        target.relative_to(reports_dir)
    except ValueError:
        return "allow", None   # not a formal output — frictionless

    if target.exists():
        return "allow", None   # amend an already-promoted report

    if target.name in report_output_filenames(root):
        return "allow", None

    return (
        "block",
        f"no Task Card declares '{target.name}' as a formal report output (outputs/reports/) — "
        f"正式產出需有對應 Task Card（硬規則 1）。請先建 tasks/ 卡片或改寫到 outputs/drafts/。",
    )


def _extract_path(tool_input: dict) -> str:
    if not isinstance(tool_input, dict):
        return ""
    return (
        tool_input.get("file_path")
        or tool_input.get("path")
        or tool_input.get("notebook_path")
        or ""
    )


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps({"decision": "allow"}))
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"decision": "allow", "warning": f"hook input not JSON: {e}"}))
        return 0

    tool_name = payload.get("tool_name") or payload.get("name") or ""
    if tool_name not in WRITE_TOOLS:
        print(json.dumps({"decision": "allow"}))
        return 0

    tool_input = payload.get("tool_input") or payload.get("input") or {}
    decision, reason = evaluate(_extract_path(tool_input))
    if decision == "block":
        print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
        print(f"BLOCKED by task_card_guard: {reason}", file=sys.stderr)
        return 2

    print(json.dumps({"decision": "allow"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
