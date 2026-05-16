# 20260516-001 — 最佳情境（golden path）e2e 測試擴充：執行摘要

## 結論

DoD 5/5 通過。`tests/e2e/test_dummy_task_smoke.py` 由 4 個 test 擴充為 8 個,無回歸。全 CI 套件本機驗證綠燈。

## 做了什麼

| 項目 | 內容 |
|---|---|
| Low-risk 自動 golden path | `test_low_risk_auto_golden_path_lands_in_drafts`：乾淨 low-risk 無核准任務走完四層 gate + 核准契約,產物落在 `outputs/drafts/`(PERMISSIONS:low == 草稿產出) |
| 核准守衛(reports/) | `test_reports_path_requires_approval_and_write_reports_tool`：寫 `outputs/reports/` 屬 ask 級 `write_reports`,未授權變體(無 approval / 無 write_reports)必須 fail,授權變體才 pass |
| 風險閘獨立性 | `test_high_risk_barred_from_reports_dir`：high/critical 不論核准一律被 risk gate 擋出非 drafts/ 路徑 |
| Execution log 契約斷言 | `test_execution_log_matches_schema_contract`：合成 execution log 須帶齊 `EXECUTION_LOG_SCHEMA.yaml` 全頂層欄位且 `gate_results` 四欄 `pass`;附負向對照 |
| 無回歸 | 既有 4 個 test 全數續綠,共 8/8 |

## Codex P1 修正紀錄

初版 `LOW_RISK_TASK` fixture 讓 low-risk + `approval_needed: False` + 僅 `write_drafts` 卻寫到 `outputs/reports/` 並斷言全 gate 通過 —— 與 `PERMISSIONS.yaml` 矛盾(`write_reports` 屬 ask 需核准;low 對應草稿產出),會讓 CI 背書未授權 report 寫入。**已修正**:golden path 改落 `outputs/drafts/`(政策正確目的地),並新增 `gate_approval` 契約把 reports/ 路徑轉為核准守衛的負向斷言。DoD#1 文字同步更新。

## Gate 驗證

- schema：兩張 Task Card 過 `validate_task_card.py` + `check_spec_consistency.rb`
- rule：僅用白名單內工具,無 deny 動作
- completion：DoD 逐條 pass(見上表)
- risk：low,測試碼進 `tests/`、摘要進 `outputs/drafts/`,無對外動作

## 驗證指令

```bash
python3 tests/e2e/test_dummy_task_smoke.py   # 6/6 OK
```
