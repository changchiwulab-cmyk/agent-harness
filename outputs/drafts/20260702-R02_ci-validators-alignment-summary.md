# 20260702-R02 摘要：CI / 驗證器對齊（發現 #1 #7 #8 #9）

## 改了什麼

- **#1** AUDIT_LOG 漂移檢查進 CI：`spec-consistency.yml` 加 `generate_audit_log.py --check` 步驟；checkout 加 `fetch-depth: 0`（checkpoint 靠 `git log --grep` 推導，shallow clone 會假 DRIFT）。現有 DRIFT 於任務收尾統一重生清除。
- **#7** GATE_POLICY.yaml task_id 格式敘述改「YYYYMMDD-NNN 或 YYYYMMDD-XNNN（字母前綴選用）」對齊 `TASK_ID_PATTERN`；「allowed_tools 非空」由兩個驗證器實際檢查（Ruby REQUIRED_FIELDS + 型別檢查；Python 必填 + 清單檢查）。
- **#8** `validate_task_card.py` REQUIRED_FIELDS 收斂為與 Ruby 同組 10 欄（補 status/expected_output/approval_needed/allowed_tools）；布林欄位判空改用 `_is_empty`（`approval_needed: false` 不再誤判缺欄）；expected_output 檢查補 location。防再漂移：`test_check_spec_consistency.rb` 加 parity 測試，regex 抽 Python 清單與 Ruby 常數比對。
- **#9** `check_context_budget.rb` 對 `skills/*/SKILL.md` 逐檔檢查 ≤1,500 tokens（CLAUDE.md 硬限制首次有守門），聯合 3,000 預算不動。

## 驗證

- `ruby scripts/test_check_spec_consistency.rb`：21 測試綠（含 parity）。
- `ruby scripts/check_spec_consistency.rb`：47 張卡全過（allowed_tools 必填生效）。
- `ruby scripts/test_check_context_budget.rb`：13 測試綠；預算檢查列出 5 個 skill 全數在限內。
- e2e smoke + failure drill 全綠（dummy card 10 欄齊備、broken fixture 仍正確被拒）。

## Checkpoints

- 3d83ddd（驗證器 + 預算）
- faca132（CI workflow）
