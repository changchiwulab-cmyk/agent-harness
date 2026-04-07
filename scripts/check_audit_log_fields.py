#!/usr/bin/env python3
"""檢查 logs/AUDIT_LOG.md 的欄位定義與範例紀錄是否完整。"""

from pathlib import Path
import re
import sys


AUDIT_LOG = Path("logs/AUDIT_LOG.md")

REQUIRED_FIELDS = [
    "task_id:",
    "date:",
    "skill_type:",
    "goal:",
    "status:",
    "model_used:",
    "model_tier:",
    "routing_reason:",
    "upgrade_reason:",
    "downgrade_reason:",
    "verify_outcome:",
    "execution_trace_ref:",
    "output_path:",
]

ALLOWED_STATUS = {"done", "failed", "partial"}
ALLOWED_MODEL_TIER = {"lite", "standard", "strong"}
ALLOWED_VERIFY_OUTCOME = {
    "pass",
    "fail_schema",
    "fail_rules",
    "fail_completion",
    "fail_risk",
}


def main() -> int:
    if not AUDIT_LOG.exists():
        print(f"[ERROR] File not found: {AUDIT_LOG}")
        return 1

    content = AUDIT_LOG.read_text(encoding="utf-8")
    missing = [field for field in REQUIRED_FIELDS if field not in content]

    if missing:
        print("[FAIL] AUDIT_LOG 缺少必要欄位：")
        for field in missing:
            print(f"  - {field}")
        return 1

    # 檢查範例紀錄 code block（若存在）
    example_match = re.search(
        r"###\s*範例紀錄.*?```yaml(.*?)```",
        content,
        flags=re.DOTALL,
    )
    if not example_match:
        print("[FAIL] 找不到『範例紀錄』YAML 區塊。")
        return 1

    example_block = example_match.group(1)
    keys = set(re.findall(r"^\s*(?:-\s*)?([a-z_]+):", example_block, flags=re.MULTILINE))
    missing_in_example = [f[:-1] for f in REQUIRED_FIELDS if f[:-1] not in keys]

    if missing_in_example:
        print("[FAIL] 範例紀錄缺少必要欄位：")
        for field in missing_in_example:
            print(f"  - {field}")
        return 1

    # 檢查範例值域
    def _extract(key: str) -> str:
        m = re.search(rf"^\s*{key}:\s*\"([^\"]*)\"", example_block, flags=re.MULTILINE)
        return m.group(1) if m else ""

    status = _extract("status")
    model_tier = _extract("model_tier")
    verify_outcome = _extract("verify_outcome")

    if status not in ALLOWED_STATUS:
        print(f"[FAIL] 範例紀錄 status 非法：{status}")
        return 1
    if model_tier not in ALLOWED_MODEL_TIER:
        print(f"[FAIL] 範例紀錄 model_tier 非法：{model_tier}")
        return 1
    if verify_outcome not in ALLOWED_VERIFY_OUTCOME:
        print(f"[FAIL] 範例紀錄 verify_outcome 非法：{verify_outcome}")
        return 1

    print("[PASS] AUDIT_LOG 欄位、範例紀錄與值域皆完整。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
