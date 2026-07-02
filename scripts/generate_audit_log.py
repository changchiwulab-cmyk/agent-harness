#!/usr/bin/env python3
"""Audit Log Generator.

Derives the structured portion of logs/AUDIT_LOG.md from tasks/20*.yaml +
git history, leaving operator-authored fields (notes, error_summary) intact.

Why:
    The hand-written AUDIT_LOG has self-reporting bias — the agent grades
    itself. Deriving task_id / date / skill_type / goal / status / output_path
    from the Task Card itself makes the audit machine-checkable against the
    artifacts that exist on disk.

Checkpoints:
    The card's own `checkpoints:` field is authoritative when non-empty — it
    lives in the same reviewed diff as the card, and unlike `git log --grep`
    it survives squash merges (branch checkpoint commits become unreachable
    on main after a squash, which would otherwise make `--check` fail every
    CI run). Cards without recorded checkpoints fall back to
    `git log --grep="checkpoint: [task_id]"`.

Behavior:
    - Reads tasks/20*.yaml.
    - For each task, uses the card's recorded checkpoints, falling back to
      matching `checkpoint: [task_id]` commits via git.
    - Renders a YAML record per task and emits AUDIT_LOG.md with a stable header.
    - If --check is passed, compares generated body against the existing file's
      auto-section and fails non-zero on drift.
    - Manual notes section (between MANUAL_NOTES markers) is preserved verbatim.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parents[1]
TASKS_GLOB = "tasks/20*.yaml"
AUDIT_LOG_PATH = ROOT / "logs" / "AUDIT_LOG.md"

AUTO_BEGIN = "<!-- AUTO_AUDIT_BEGIN -->"
AUTO_END = "<!-- AUTO_AUDIT_END -->"

HEADER = """# Audit Log

每次任務的結構化欄位由 `scripts/generate_audit_log.py` 從 Task Card + git log 自動產生。
人工備註寫在「人工備註」區段，不會被覆蓋。

格式：YAML blocks 由生成器維護，依 `task_id` 倒序。
"""


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def collect_tasks(root: Path) -> list[dict[str, Any]]:
    items = []
    for p in sorted(root.glob(TASKS_GLOB)):
        if not p.is_file():
            continue
        doc = load_yaml(p)
        if not doc.get("task_id"):
            continue
        items.append(doc)
    # Sort by task_id descending (newest first), tie-break by date.
    items.sort(key=lambda d: (str(d.get("task_id", "")), str(d.get("date", ""))), reverse=True)
    return items


def find_checkpoints(task_id: str, root: Path) -> list[dict[str, str]]:
    """Return list of {commit, subject} for `checkpoint: [task_id]` commits."""
    try:
        out = subprocess.run(
            ["git", "log", f"--grep=checkpoint: \\[{task_id}\\]", "--pretty=%h%x09%s"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    rows = []
    for line in out.stdout.splitlines():
        if "\t" not in line:
            continue
        commit, subject = line.split("\t", 1)
        rows.append({"commit": commit.strip(), "subject": subject.strip()})
    return rows


def resolve_checkpoints(task: dict[str, Any], root: Path) -> list[dict[str, str]]:
    """Card-recorded checkpoints when present, else git-derived (see docstring)."""
    recorded = task.get("checkpoints")
    if isinstance(recorded, list) and recorded:
        return [dict(item) for item in recorded if isinstance(item, dict)]
    return find_checkpoints(str(task.get("task_id", "")), root)


def derive_record(task: dict[str, Any], root: Path) -> dict[str, Any]:
    task_id = str(task.get("task_id", ""))
    output = task.get("expected_output") or {}
    output_path = ""
    if isinstance(output, dict):
        loc = str(output.get("location", "")).rstrip("/")
        fn = str(output.get("filename", ""))
        if loc and fn:
            output_path = f"{loc}/{fn}"

    return {
        "task_id": task_id,
        "date": str(task.get("date", "")),
        "skill_type": str(task.get("skill_type", "")),
        "goal": str(task.get("goal", "")),
        "status": str(task.get("status", "")),
        "risk_level": str(task.get("risk_level", "")),
        "approval_needed": bool(task.get("approval_needed", False)),
        "output_path": output_path,
        "checkpoints": resolve_checkpoints(task, root),
        "actual_tool_calls": task.get("actual_tool_calls"),
        "result_summary": str(task.get("result_summary", "")),
        "completion_time": str(task.get("completion_time", "")),
    }


def render_records(records: Iterable[dict[str, Any]]) -> str:
    """Render derived records as YAML blocks separated by `---`."""
    chunks = []
    for rec in records:
        chunk = "```yaml\n" + yaml.safe_dump(
            rec, sort_keys=False, allow_unicode=True, default_flow_style=False
        ).rstrip() + "\n```\n"
        chunks.append(chunk)
    return "\n".join(chunks).rstrip() + "\n"


MANUAL_HEADING = "## 人工備註"
MANUAL_PLACEHOLDER = "<!-- 在此補充自動產生欄位之外的脈絡、教訓、決策連結 -->\n"


def split_manual_notes(existing: str) -> str:
    """Return manual-notes body (without the heading), normalised.

    Three cases:
    1. AUTO markers present → take everything after AUTO_END (normal path).
    2. AUTO markers absent + file non-empty → fallback: treat the entire
       post-HEADER body as manual notes. This protects hand-written
       `logs/AUDIT_LOG.md` from being silently destroyed when the generator
       is first run before the file has been migrated to the marker format.
    3. Empty file → empty manual section.

    Strips the existing `## 人工備註` heading so the renderer can re-emit it
    deterministically without duplication.
    """
    if AUTO_BEGIN in existing and AUTO_END in existing:
        _, _, rest = existing.partition(AUTO_END)
        body = rest.lstrip("\n")
    elif existing.strip():
        # Fallback: preserve everything after the canonical HEADER. We compare
        # against HEADER prefix-by-prefix because the existing file's header
        # may have been hand-customised.
        body = existing
        header_first_line = HEADER.splitlines()[0]
        if body.startswith(header_first_line):
            # Skip past the first contiguous block (the header) — anything that
            # is not a YAML block fence or auto marker.
            lines = body.splitlines(keepends=True)
            i = 0
            # Drop the H1 line plus any non-record prose immediately under it,
            # up to the first ```yaml fence or YAML record list separator.
            while i < len(lines) and not lines[i].lstrip().startswith("```yaml") \
                    and not lines[i].lstrip().startswith("- task_id:"):
                i += 1
            body = "".join(lines[i:])
        body = body.lstrip("\n")
    else:
        return ""
    if body.startswith(MANUAL_HEADING):
        body = body[len(MANUAL_HEADING):].lstrip("\n")
    return body


def build_document(records: Iterable[dict[str, Any]], existing: str) -> str:
    body = render_records(records)
    manual_after = split_manual_notes(existing)
    parts = [
        HEADER.rstrip() + "\n\n",
        f"{AUTO_BEGIN}\n",
        body,
        f"{AUTO_END}\n",
        f"\n{MANUAL_HEADING}\n\n",
    ]
    if manual_after.strip():
        parts.append(manual_after if manual_after.endswith("\n") else manual_after + "\n")
    else:
        parts.append(MANUAL_PLACEHOLDER)
    return "".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="exit non-zero if AUDIT_LOG.md is out of date")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--print-records", action="store_true", help="print derived records as JSON and exit")
    args = parser.parse_args(argv)

    root = args.root
    output = args.output if args.output else (root / "logs" / "AUDIT_LOG.md")

    tasks = collect_tasks(root)
    records = [derive_record(t, root) for t in tasks]

    if args.print_records:
        print(json.dumps(records, ensure_ascii=False, indent=2, default=str))
        return 0

    existing = output.read_text(encoding="utf-8") if output.exists() else ""
    rendered = build_document(records, existing)

    if args.check:
        if existing != rendered:
            print(
                f"DRIFT: {output.relative_to(root)} is out of date. "
                "Re-run scripts/generate_audit_log.py.",
                file=sys.stderr,
            )
            return 1
        print(f"OK: {output.relative_to(root)} is up to date.")
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(f"Generated {output.relative_to(root)} ({len(records)} task records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
