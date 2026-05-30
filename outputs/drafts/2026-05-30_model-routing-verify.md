# 模型路由 前後端對齊 — 端到端驗證紀錄（草稿）

> 對應 Task Card：`20260530-V01`。日期：2026-05-30。

## CI / 驗證套件（13 項全綠）

| # | 檢查 | 結果 |
|---|------|------|
| 1 | `ruby -c scripts/check_spec_consistency.rb` | PASS |
| 2 | `scripts/check_spec_consistency.rb` | PASS |
| 3 | `scripts/test_check_spec_consistency.rb` | PASS |
| 4 | `validate_task_card.py`（範例卡 + 5 張新卡） | PASS |
| 5 | 全庫 YAML 解析 | PASS |
| 6 | `check_context_budget.rb`（~1252/3000） | PASS |
| 7 | `test_generate_frontend_manifest.py`（6 測試） | PASS |
| 8 | `generate_frontend_manifest.py --check`（漂移 0） | PASS |
| 9 | `test_permissions_guard.py` | PASS |
| 10 | `test_generate_audit_log.py` | PASS |
| 11 | `tests/e2e/test_dummy_task_smoke.py` | PASS |
| 12 | `tests/e2e/test_failure_drill.py` | PASS |
| 13 | `test_check_decision_revisit.rb` | PASS |

## 前端平台服務驗證

- `GET /frontend/index.html` → 200；引用 `app.js` + `#overviewPanel`
- `GET /frontend/data.json` → 200；`overview.task_model = {fast:34, strategy:9, test:7}`
- `app.js` 治理總覽含「Task 模型分佈」「Run 模型」兩卡

## 前後端對齊確認

| 層 | 產物 | 模型資訊 |
|----|------|---------|
| 後端 政策 | `system/MODEL_ROUTING.yaml` | fast/test/strategy tier + model id + 子代理 |
| 後端 資料 | Task Card `model_routing` / run log `model_used` | optional 欄位，向後相容 |
| 執行 | `.claude/agents/{fast-reader,tester,synthesizer}.md` | 綁定 Haiku/Sonnet/Opus |
| 橋接 | `scripts/generate_frontend_manifest.py` | 衍生 `model_tier` + tally |
| 前端 | `frontend/data.json` + `app.js` | 模型分佈面板 |

四層皆以 `MODEL_ROUTING.yaml` 為單一真相來源，前後端對齊。

## 向後相容

- 新欄位全 optional；驗證器為必填白名單，不拒未知欄位 → 既有 51 卡 / 既有 log 不動即過。
- 唯一結構鎖定測試（empty-repo overview）已同步更新。
- `run_model` 目前 2 筆 unknown（舊 log 無 `model_used`）；新任務累積後填滿，符合預期。
