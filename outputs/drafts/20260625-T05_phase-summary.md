<!--
task_id: 20260625-T05
date: 2026-06-25
skill_type: ops
status: draft
-->

# T05 實作摘要：test_batch run-log 強制機制（關閉 T04 缺口 #1）+ Codex P2 修正

## 總結

落實 T04 框架回測的缺口 #1（run-log scope 對乾淨成功批次零紀錄）：新增 `test_batch` 旗標，並以 **CI 硬性強制**「標記為測試批次的卡必須留 `logs/runs/` run-log」。同時回填本次 3 主題批次（T01–T04）的 run-logs，當場關閉缺口；並回應 PR #109 的 Codex P2 review，把 T04 §3 失敗模式由 4 類別彙整升級為 per-ID 全 15 模式列舉。決策記為 D008（additive 延伸 D006，不取代）。

## 變更清單

| # | 檔案 | 變更 |
|---|---|---|
| A1 | `tasks/TASK_CARD_TEMPLATE.yaml` | 新增可選欄位 `test_batch: false`（含說明） |
| A2 | `system/EXECUTION_LOG_SCHEMA.yaml` | 使用範圍新增第 5 觸發條件 `test_batch: true`，引用 D008 |
| A3 | `scripts/check_spec_consistency.rb` | 新增 top-level `test_batch_run_log_violations`：test_batch:true 但缺對應 run-log → error；非 boolean → error。主程式收集 `logs/runs/` 的 task_id 後套用 |
| A4 | `scripts/test_check_spec_consistency.rb` | 新增 5 個 minitest 案例（true+log/true 無 log/false/欄位缺/非 boolean） |
| B1 | `tasks/2026-06-25_t0{1..4}_*.yaml` | 四張卡各加 `test_batch: true` |
| B2 | `logs/runs/RUN-20260625-001..004.yaml` | 回填 T01–T04 run-logs（status completed、gate 全 pass、token source rule_estimated） |
| B3 | `frontend/data.json` | 重新產生（CI drift check 通過） |
| C1 | `outputs/drafts/20260625-T04_*.md` §3 | 改為逐 ID 列舉全部 15 個失敗模式（回應 Codex P2）；T04 卡 result_summary 同步更新 |
| D1 | `memory/.../decisions/20260625-D008_*.yaml` | 新決策：test_batch 為 D006 第 5 觸發條件（additive） |
| E | `logs/runs/RUN-20260625-005.yaml` | 本卡自身（checkpoints≥3，依 D006 rule#4）run-log |

## 驗證結果

- `ruby scripts/check_spec_consistency.rb` → OK（4 卡 test_batch:true 皆有對應 run-log）
- `ruby scripts/test_check_spec_consistency.rb` → 25 runs, 0 failures（含 5 個新案例）
- **負向測試**：旗標加上、run-log 未建時 `check_spec_consistency.rb` 如期紅燈（exit 1，4 筆 error）→ 補 run-log 後轉綠，證明硬擋有效
- `python3 system/validate_task_card.py tasks/2026-06-25_t05_*.yaml` → pass
- `python3 scripts/generate_frontend_manifest.py --check` → up to date（無漂移）
- `python3 -m pytest tests/` → 7 passed（既有 e2e gate 契約 + failure drill 未被破壞）

## 與框架原則的對齊

- **不回退 D006**：happy-path 不強加儀式仍成立；test_batch 是「刻意留證據」的特例，用顯式旗標區分。
- **硬規則 #2**：本摘要與所有產出留在 `outputs/drafts/`，未晉升 reports/。
- **ask 級動作**：修改 `system/` 與寫 `memory/` decision 屬 ask，核准閘門為 PR #109 review（approval_needed: true）。

## 待人工確認（approval）

- 修改 `system/EXECUTION_LOG_SCHEMA.yaml`、`tasks/TASK_CARD_TEMPLATE.yaml`、`scripts/`、寫入 `memory/.../decisions/D008` 屬 ask 級，於 PR #109 review 一併確認。
