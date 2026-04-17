#!/usr/bin/env python3
"""
Task Card Schema Validator
用法：python system/validate_task_card.py tasks/your-task.yaml
"""

import sys
import yaml

REQUIRED_FIELDS = ["task_id", "date", "goal", "definition_of_done", "skill_type", "risk_level"]
VALID_SKILLS = {"research", "analysis", "writing", "ops", "review"}
VALID_RISK = {"low", "medium", "high", "critical"}
VALID_STATUS = {"pending", "in_progress", "checkpoint", "review", "done", "failed"}


def validate(path: str) -> list[str]:
    errors = []
    try:
        with open(path) as f:
            card = yaml.safe_load(f)
    except Exception as e:
        return [f"YAML 解析失敗：{e}"]

    # 必填欄位
    for field in REQUIRED_FIELDS:
        if not card.get(field):
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
    output = card.get("expected_output", {})
    if not output.get("format"):
        errors.append("expected_output.format 不能為空")
    if not output.get("filename"):
        errors.append("expected_output.filename 不能為空")
    if not output.get("location"):
        errors.append("expected_output.location 不能為空")

    # allowed_tools 白名單（Gate 2 rule_check 依賴此欄位）
    allowed_tools = card.get("allowed_tools")
    if not isinstance(allowed_tools, list) or len(allowed_tools) == 0:
        errors.append("allowed_tools 必須為非空 list（至少列出一個工具）")

    # max_tool_calls 必須為正整數
    max_calls = card.get("max_tool_calls")
    if max_calls is None:
        errors.append("缺少必填欄位：max_tool_calls")
    elif not isinstance(max_calls, int) or isinstance(max_calls, bool) or max_calls <= 0:
        errors.append(f"max_tool_calls 必須為正整數，實際：{max_calls!r}")

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
