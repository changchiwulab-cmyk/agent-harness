#!/usr/bin/env python3
"""
Task Card Schema Validator
用法：python system/validate_task_card.py tasks/your-task.yaml
"""

import sys
import yaml

# 必填欄位與 scripts/check_spec_consistency.rb 的 REQUIRED_FIELDS 同步；
# 兩邊一致性由 scripts/test_check_spec_consistency.rb 的 parity 測試在 CI 保證。
REQUIRED_FIELDS = [
    "task_id",
    "date",
    "status",
    "goal",
    "definition_of_done",
    "expected_output",
    "risk_level",
    "approval_needed",
    "skill_type",
    "allowed_tools",
]
VALID_SKILLS = {"research", "analysis", "writing", "ops", "review"}
VALID_RISK = {"low", "medium", "high", "critical"}
VALID_STATUS = {"pending", "in_progress", "checkpoint", "review", "done", "failed"}


def _is_empty(value) -> bool:
    # approval_needed: false 是合法值，不能用 truthiness 判空
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def validate(path: str) -> list[str]:
    errors = []
    try:
        with open(path) as f:
            card = yaml.safe_load(f)
    except Exception as e:
        return [f"YAML 解析失敗：{e}"]

    # 必填欄位
    for field in REQUIRED_FIELDS:
        if _is_empty(card.get(field)):
            errors.append(f"缺少必填欄位：{field}")

    # definition_of_done 至少一條
    dod = card.get("definition_of_done", [])
    if not isinstance(dod, list) or len(dod) == 0:
        errors.append("definition_of_done 必須包含至少一條可驗證條件")
    else:
        for i, item in enumerate(dod):
            if not item or not str(item).strip():
                errors.append(f"definition_of_done[{i}] 不能為空字串")

    # skill_type 值域
    skill = card.get("skill_type", "")
    if skill and skill not in VALID_SKILLS:
        errors.append(f"skill_type 無效：'{skill}'，允許值：{VALID_SKILLS}")

    # risk_level 值域
    risk = card.get("risk_level", "")
    if risk and risk not in VALID_RISK:
        errors.append(f"risk_level 無效：'{risk}'，允許值：{VALID_RISK}")

    # status 值域
    status = card.get("status", "")
    if status and status not in VALID_STATUS:
        errors.append(f"status 無效：'{status}'，允許值：{VALID_STATUS}")

    # expected_output 結構
    output = card.get("expected_output") or {}
    for key in ("format", "location", "filename"):
        if not output.get(key):
            errors.append(f"expected_output.{key} 不能為空")

    # allowed_tools 白名單（GATE_POLICY schema_check：allowed_tools 非空）
    tools = card.get("allowed_tools")
    if tools is not None and not isinstance(tools, list):
        errors.append("allowed_tools 必須是清單")

    return errors


def main():
    if len(sys.argv) < 2:
        print("用法：python system/validate_task_card.py tasks/your-task.yaml")
        sys.exit(1)

    path = sys.argv[1]
    errors = validate(path)

    if errors:
        print(f"❌ Task Card 驗證失敗：{path}")
        for e in errors:
            print(f"   - {e}")
        sys.exit(1)
    else:
        print(f"✅ Task Card 驗證通過：{path}")
        sys.exit(0)


if __name__ == "__main__":
    main()
