#!/usr/bin/env python3
"""
Task Card Schema Validator
用法：python system/validate_task_card.py tasks/your-task.yaml
"""

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FIELDS = ["task_id", "date", "goal", "definition_of_done", "skill_type", "risk_level"]
VALID_SKILLS = {"research", "analysis", "writing", "ops", "review", "orchestration"}
VALID_RISK = {"low", "medium", "high", "critical"}
VALID_STATUS = {"pending", "in_progress", "checkpoint", "review", "done", "failed"}
# 模型路由（選填）：別名與完整 id 皆可，見 system/MODEL_ROUTING.md
VALID_MODELS = {
    "haiku", "sonnet", "opus", "fable",
    "claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-8", "claude-fable-5",
}


def _has_cycle(deps: dict[str, list[str]]) -> bool:
    """Kahn 拓樸排序：回傳 True 表示 DAG 有環。"""
    indeg = {n: 0 for n in deps}
    for n, ds in deps.items():
        for d in ds:
            if d in indeg:
                indeg[n] += 1
    queue = [n for n, c in indeg.items() if c == 0]
    seen = 0
    while queue:
        n = queue.pop()
        seen += 1
        for m, ds in deps.items():
            if n in ds:
                indeg[m] -= 1
                if indeg[m] == 0:
                    queue.append(m)
    return seen != len(deps)


def validate_orchestration(card: dict) -> list[str]:
    """編排父卡（skill_type=orchestration）的 subtasks DAG 與 fan_in 驗證。

    非 orchestration 卡回傳空清單（不影響既有卡片）。subtasks[].card 路徑相對 repo ROOT。
    """
    if card.get("skill_type") != "orchestration":
        return []
    errors: list[str] = []
    subtasks = card.get("subtasks")
    if not isinstance(subtasks, list) or not subtasks:
        return ["orchestration 父卡的 subtasks 必須為非空 list"]

    ids: list[str] = []
    for i, st in enumerate(subtasks):
        if not isinstance(st, dict):
            errors.append(f"subtasks[{i}] 必須為 mapping")
            continue
        sid = st.get("id")
        cardp = st.get("card")
        if not sid:
            errors.append(f"subtasks[{i}] 缺少 id")
        if not cardp:
            errors.append(f"subtasks[{i}] 缺少 card 路徑")
        elif not (ROOT / cardp).exists():
            errors.append(f"subtasks[{i}].card 檔案不存在：{cardp}")
        if sid:
            if sid in ids:
                errors.append(f"subtask id 重複：{sid}")
            ids.append(sid)

    deps: dict[str, list[str]] = {}
    for st in subtasks:
        if not isinstance(st, dict) or not st.get("id"):
            continue
        d = st.get("depends_on", []) or []
        if not isinstance(d, list):
            errors.append(f"subtask '{st['id']}' 的 depends_on 必須為 list")
            d = []
        for dep in d:
            if dep not in ids:
                errors.append(f"subtask '{st['id']}' 依賴不存在的 id：{dep}")
        deps[st["id"]] = [x for x in d if x in ids]

    if deps and _has_cycle(deps):
        errors.append("subtasks DAG 存在環（circular dependency）")

    fan_in = card.get("fan_in")
    if isinstance(fan_in, dict) and fan_in.get("into"):
        parent = (ROOT / fan_in["into"]).parent
        if not parent.exists():
            errors.append(f"fan_in.into 的父目錄不存在：{fan_in['into']}")

    return errors


def validate(path: str) -> list[str]:
    errors = []
    try:
        with open(path) as f:
            card = yaml.safe_load(f)
    except Exception as e:
        return [f"YAML 解析失敗：{e}"]

    if not isinstance(card, dict):
        return ["Task Card 根節點必須為 mapping"]

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

    # model 值域（選填）
    model = card.get("model", "")
    if model and model not in VALID_MODELS:
        errors.append(f"model 無效：'{model}'，允許值：{VALID_MODELS}")

    # expected_output 結構
    output = card.get("expected_output", {})
    if not output.get("format"):
        errors.append("expected_output.format 不能為空")
    if not output.get("filename"):
        errors.append("expected_output.filename 不能為空")

    # 編排父卡的 subtasks DAG 驗證（僅 skill_type=orchestration 時生效）
    errors.extend(validate_orchestration(card))

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
