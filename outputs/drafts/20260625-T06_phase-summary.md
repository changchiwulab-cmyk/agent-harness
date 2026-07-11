<!--
task_id: 20260625-T06
date: 2026-06-25
skill_type: ops
status: draft
-->

# T06 實作摘要：M5 gate 覆蓋指標 + 高風險演練（關閉 T04 缺口 #2）

## 總結

補 T04 缺口 #2（低風險批次讓 risk/approval gate 空轉）。使用者選「兩者都做」：
- **A. M5 可觀測性指標**：把空轉「可見化」。
- **B. 高風險演練 DR1**：真的走一次 risk/approval 路徑，留下真實樣本。

## 變更清單

| # | 檔案 | 變更 |
|---|---|---|
| A1 | `scripts/governance_metrics.py` | `load_task_cards` 帶出 `risk_level`；新增 `load_approval_records()`；新增 `metric_m5()`（近 3 月無 high/critical 卡且無 approval record → warn）；`collect_metrics` 變 M1–M5 |
| A2 | `scripts/test_governance_metrics.py` | 2 個釘「4 個指標」的測試更新為 5／`{M1..M5}`；新增 `TestMetricM5`（覆蓋有 high-risk / 有 approval / 皆無 / 窗外不算 四案） |
| B1 | `tasks/2026-06-25_dr1_high-risk-gate-drill.yaml` | 高風險演練卡（risk high、approval_needed true、writing） |
| B2 | `outputs/drafts/20260625-DR1_*.md` | 合成電子報草稿，明標演練、停 drafts/ |
| B3 | `logs/approvals/2026-06-25_20260625-DR1_approval.yaml` | 真實 approval record（APR-20260625-001，human_confirm/approved） |
| B4 | `logs/runs/RUN-20260625-006.yaml` | high-risk run-log（D006 rule#3），risk_check 記錄 |
| D | `memory/.../decisions/20260625-D009_*.yaml` | 決策：gate 覆蓋 = M5 + 週期性高風險演練 |

## 驗證結果

- `python3 scripts/test_governance_metrics.py` → **31 tests OK**（含 4 個新 M5 案例）
- `python3 scripts/governance_metrics.py --json --today 2026-06-25` → M5 **ok**：演練前 `high/critical 卡=1`，演練後 `high/critical 卡=2（含 DR1）, approval records=3`——指標即時反映真實覆蓋
- `ruby scripts/check_spec_consistency.rb` → OK（新 approval record + run-log 通過 lint）
- `python3 system/validate_task_card.py`（T06 / DR1）→ pass

## gate 路徑實證（DR1）

- **risk_check**：`risk_level: high` + 對外動作 → 輸出鎖在 `outputs/drafts/`，未進 `reports/`。
- **approval flow**：`approval_needed: true` → 產生真實 `logs/approvals/` 紀錄（human_confirm/approved）。
- **無外送**：硬規則 #2 全程遵守，草稿明標不發布。

## 待人工確認（approval）

- 修改 `scripts/`、寫 `memory/` decision D009 屬 ask 級；DR1 為高風險演練——於 PR #109 review 一併確認。
