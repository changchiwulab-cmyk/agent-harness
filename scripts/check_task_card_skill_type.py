#!/usr/bin/env python3
"""Check that task card files use allowed `skill_type` values."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ALLOWED_SKILL_TYPES = {"research", "writing", "ops", "review", "analysis"}
TARGET_FILES = (
    Path("tasks/TASK_CARD_TEMPLATE.yaml"),
    Path("tasks/examples/2026-04-03_market-research-example.yaml"),
)


def extract_skill_type(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^skill_type:.*$", text, flags=re.MULTILINE)
    if not match:
        raise ValueError(f"{path} 缺少 skill_type 欄位")

    raw = match.group(0).split(":", 1)[1]
    raw = raw.split("#", 1)[0].strip()
    return raw.strip('"').strip("'")


def main() -> int:
    for path in TARGET_FILES:
        skill_type = extract_skill_type(path)
        if skill_type and skill_type not in ALLOWED_SKILL_TYPES:
            raise ValueError(f"{path} skill_type 不在允許清單: {skill_type}")

    print("task card skill_type check passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as err:
        print(err, file=sys.stderr)
        raise SystemExit(1)
