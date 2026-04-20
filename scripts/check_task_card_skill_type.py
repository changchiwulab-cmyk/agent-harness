#!/usr/bin/env python3
"""Check that task card files use allowed `skill_type` values."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ALLOWED_SKILL_TYPES = {"research", "analysis", "writing", "ops", "review"}
TASKS_DIR = Path("tasks")
EXCLUDE_NAMES = {"TASK_CARD_TEMPLATE", "DECISION_LOG_TEMPLATE", "WEEKLY_REVIEW_TEMPLATE"}


def extract_skill_type(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^skill_type:.*$", text, flags=re.MULTILINE)
    if not match:
        return None

    raw = match.group(0).split(":", 1)[1]
    raw = raw.split("#", 1)[0].strip()
    value = raw.strip('"').strip("'")
    return value if value else None


def extract_task_id(path: Path) -> str | None:
    """Extract task_id value from a Task Card YAML (line-based, same style as extract_skill_type)."""
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^task_id:.*$", text, flags=re.MULTILINE)
    if not match:
        return None

    raw = match.group(0).split(":", 1)[1]
    raw = raw.split("#", 1)[0].strip()
    value = raw.strip('"').strip("'")
    return value if value else None


def collect_task_cards() -> list[Path]:
    cards = []
    for path in sorted(TASKS_DIR.rglob("*.yaml")):
        stem = path.stem.upper().replace("-", "_").replace(" ", "_")
        if any(excl in stem for excl in EXCLUDE_NAMES):
            continue
        cards.append(path)
    return cards


def main() -> int:
    task_cards = collect_task_cards()

    if not task_cards:
        print("no task cards found — skipping check")
        return 0

    errors = []
    seen_task_ids: dict[str, Path] = {}  # D007 — task_id 全域唯一
    for path in task_cards:
        skill_type = extract_skill_type(path)
        if skill_type is None:
            errors.append(f"{path} 缺少 skill_type 欄位")
        elif skill_type not in ALLOWED_SKILL_TYPES:
            errors.append(
                f"{path} skill_type 不在允許清單: '{skill_type}' "
                f"(允許值: {sorted(ALLOWED_SKILL_TYPES)})"
            )

        task_id = extract_task_id(path)
        if task_id:
            if task_id in seen_task_ids:
                errors.append(
                    f"{path} task_id '{task_id}' 已在 {seen_task_ids[task_id]} 使用（需全域唯一，見 D007）"
                )
            else:
                seen_task_ids[task_id] = path

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1

    print(f"task card skill_type check passed ({len(task_cards)} cards checked)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as err:
        print(err, file=sys.stderr)
        raise SystemExit(1)
