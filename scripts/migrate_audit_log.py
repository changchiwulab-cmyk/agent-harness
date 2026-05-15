#!/usr/bin/env python3
"""One-time migration: hand-written logs/AUDIT_LOG.md -> AUTO/MANUAL structure.

Why:
    scripts/generate_audit_log.py derives structured fields (task_id, date,
    skill_type, goal, status, output_path, checkpoints, ...) from
    tasks/20*.yaml + git log. But it does NOT — and cannot — derive the
    operator-authored fields that live only in the hand-written AUDIT_LOG:
    `notes`, `error_summary`, `estimated_tokens`, `model_used`,
    `approval_given`. These carry the irreplaceable judgement (lessons, root
    causes, decision links).

    Running the generator directly does not lose data (its split_manual_notes
    fallback keeps the whole old body verbatim), but the result is a duplicated,
    structurally messy file. This script does the clean one-shot: extract the
    non-derivable fields per task_id, lay them out tidily under `## 人工備註`,
    and emit a transitional file with AUTO_BEGIN/AUTO_END markers so that the
    generator can then own the structured section without churn.

Idempotency:
    If logs/AUDIT_LOG.md already contains the AUTO markers, the migration is
    already done (and the yaml blocks are now generator output WITHOUT a
    `notes` field). Re-running must therefore be a strict no-op, otherwise a
    second run would parse the marker-less-source assumption wrong and wipe the
    manual section. The guard below makes re-runs safe.

Flow (see tasks/2026-05-15_audit-integrity.yaml):
    1. python scripts/migrate_audit_log.py        # this script (one-time)
    2. python scripts/generate_audit_log.py       # fills AUTO from task cards
    3. python scripts/generate_audit_log.py --check  # exits 0
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
AUDIT_LOG_PATH = ROOT / "logs" / "AUDIT_LOG.md"

AUTO_BEGIN = "<!-- AUTO_AUDIT_BEGIN -->"
AUTO_END = "<!-- AUTO_AUDIT_END -->"
MANUAL_HEADING = "## 人工備註"
MIGRATION_MARK = (
    "<!-- 以下由 scripts/migrate_audit_log.py 一次性從手寫 AUDIT_LOG 遷移；"
    "結構化欄位改由 generate_audit_log.py 維護，本區段之後人工維護 -->"
)

# Operator-authored fields that generate_audit_log.derive_record cannot
# reconstruct from a Task Card. Order here is the render order.
PRESERVED_FIELDS = (
    "notes",
    "error_summary",
    "estimated_tokens",
    "model_used",
    "approval_given",
)

_FENCE_RE = re.compile(r"```yaml\s*\n(.*?)\n```", re.DOTALL)
_PLACEHOLDERS = {"", "—", "-", "–", "n/a", "na", "none"}


def extract_entries(markdown: str) -> list[dict[str, Any]]:
    """Parse every ```yaml fenced block; flatten lists; skip empty task_id."""
    entries: list[dict[str, Any]] = []
    for block in _FENCE_RE.findall(markdown):
        try:
            doc = yaml.safe_load(block)
        except yaml.YAMLError:
            continue
        rows = doc if isinstance(doc, list) else [doc]
        for row in rows:
            if not isinstance(row, dict):
                continue
            task_id = str(row.get("task_id", "")).strip()
            if not task_id:  # the "## 紀錄格式" template example
                continue
            entries.append(row)
    return entries


def _is_meaningful(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return True  # approval_given: False is meaningful
    return str(value).strip().lower() not in _PLACEHOLDERS


def render_manual_section(entries: list[dict[str, Any]]) -> str:
    # Dedupe by task_id (last occurrence wins), then sort task_id descending
    # to match generate_audit_log's ordering.
    by_id: dict[str, dict[str, Any]] = {}
    for e in entries:
        by_id[str(e["task_id"]).strip()] = e
    ordered = sorted(by_id.values(), key=lambda d: str(d["task_id"]), reverse=True)

    lines = [MANUAL_HEADING, "", MIGRATION_MARK, ""]
    for e in ordered:
        task_id = str(e["task_id"]).strip()
        kept = [(f, e.get(f)) for f in PRESERVED_FIELDS if _is_meaningful(e.get(f))]
        if not kept:
            continue
        lines.append(f"### {task_id}")
        for field, value in kept:
            if isinstance(value, bool):
                value = "true" if value else "false"
            text = str(value).strip().replace("\n", " ")
            lines.append(f"- {field}: {text}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_transitional(manual_section: str) -> str:
    """Marker-framed file. generate_audit_log re-emits HEADER + AUTO body and
    preserves everything after AUTO_END verbatim, so a minimal frame here is
    enough; the leading line only keeps the file readable pre-generation."""
    return (
        "# Audit Log\n\n"
        "（過渡檔：執行 scripts/generate_audit_log.py 後 AUTO 區由生成器填入）\n\n"
        f"{AUTO_BEGIN}\n\n{AUTO_END}\n\n"
        f"{manual_section}"
    )


def _display(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def migrate(path: Path, dry_run: bool = False) -> int:
    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        return 1

    content = path.read_text(encoding="utf-8")

    if AUTO_BEGIN in content:
        print(
            f"NO-OP: {_display(path)} already migrated "
            "(AUTO markers present); manual section left untouched."
        )
        return 0

    entries = extract_entries(content)
    task_ids = sorted({str(e["task_id"]).strip() for e in entries}, reverse=True)
    if not entries:
        print("ERROR: no task entries parsed from source AUDIT_LOG", file=sys.stderr)
        return 1

    manual_section = render_manual_section(entries)
    new_content = build_transitional(manual_section)
    preserved_ids = [
        tid
        for tid in task_ids
        if any(
            _is_meaningful(e.get(f))
            for e in entries
            if str(e["task_id"]).strip() == tid
            for f in PRESERVED_FIELDS
        )
    ]

    print(
        f"Parsed {len(entries)} entries / {len(task_ids)} unique task_ids; "
        f"{len(preserved_ids)} carry preserved operator fields."
    )
    if dry_run:
        print("DRY-RUN: not writing. task_ids:")
        print("  " + ", ".join(task_ids))
        return 0

    path.write_text(new_content, encoding="utf-8")
    print(
        f"Wrote transitional {_display(path)} "
        f"({len(task_ids)} task_ids in 人工備註). "
        "Next: python scripts/generate_audit_log.py"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--dry-run", action="store_true", help="parse + report, do not write"
    )
    args = parser.parse_args(argv)
    target = (args.root / "logs" / "AUDIT_LOG.md") if args.root != ROOT else AUDIT_LOG_PATH
    return migrate(target, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
