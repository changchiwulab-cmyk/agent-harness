#!/usr/bin/env python3
"""Standalone CLI validator for Task Card YAML files.

Ported from agent-harness system/validate_task_card.py. Validates against
schemas/task_card.schema.yaml minimum-viable rules:
    - required fields present and non-empty
    - definition_of_done is a non-empty list of non-empty strings
    - skill_type / risk_level / status values from allowed sets
    - expected_output.format and filename non-empty

Exit codes:
    0 — pass
    1 — usage error (no path given)
    2 — schema fail (errors printed to stdout)
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REQUIRED_FIELDS = ("task_id", "date", "goal", "definition_of_done", "skill_type", "risk_level")
VALID_SKILLS = {"research", "analysis", "writing", "ops", "review"}
VALID_RISK = {"low", "medium", "high", "critical"}
VALID_STATUS = {"pending", "in_progress", "checkpoint", "review", "done", "failed", "partial"}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        card = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        return [f"YAML 解析失敗：{e}"]
    except OSError as e:
        return [f"檔案讀取失敗：{e}"]

    if not isinstance(card, dict):
        return ["Task Card 不是 YAML mapping"]

    for field in REQUIRED_FIELDS:
        if not card.get(field):
            errors.append(f"缺少必填欄位：{field}")

    dod = card.get("definition_of_done", [])
    if not isinstance(dod, list) or len(dod) == 0:
        errors.append("definition_of_done 必須包含至少一條可驗證條件")
    else:
        for i, item in enumerate(dod):
            if not isinstance(item, str):
                errors.append(f"definition_of_done[{i}] 必須是字串（got {type(item).__name__}）")
            elif not item.strip():
                errors.append(f"definition_of_done[{i}] 不能為空字串")

    skill = card.get("skill_type", "")
    if skill and skill not in VALID_SKILLS:
        errors.append(f"skill_type 無效：'{skill}'，允許值：{sorted(VALID_SKILLS)}")

    risk = card.get("risk_level", "")
    if risk and risk not in VALID_RISK:
        errors.append(f"risk_level 無效：'{risk}'，允許值：{sorted(VALID_RISK)}")

    status = card.get("status", "")
    if status and status not in VALID_STATUS:
        errors.append(f"status 無效：'{status}'，允許值：{sorted(VALID_STATUS)}")

    output = card.get("expected_output", {})
    if not isinstance(output, dict):
        errors.append("expected_output 必須是 mapping")
    else:
        if not output.get("format"):
            errors.append("expected_output.format 不能為空")
        if not output.get("filename"):
            errors.append("expected_output.filename 不能為空")

    return errors


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("用法：validate_task_card.py <path-to-task-card.yaml>", file=sys.stderr)
        return 1

    path = Path(args[0])
    errors = validate(path)
    if errors:
        print(f"❌ Task Card 驗證失敗：{path}")
        for e in errors:
            print(f"   - {e}")
        return 2
    print(f"✅ Task Card 驗證通過：{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
