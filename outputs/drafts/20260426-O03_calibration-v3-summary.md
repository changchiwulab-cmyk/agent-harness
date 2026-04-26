# 20260426-O03 — 校準 SOP + v3 量化觸發摘要

**任務**：補完校準操作 SOP 與 v3 升級量化觸發條件。
**狀態**：done
**完成日期**：2026-04-26

## 變更項目

| # | 動作 | 檔案 | 摘要 |
|---|------|------|------|
| 1 | edit | `system/COST_POLICY.md` | 新增「下次校準操作 SOP」章節：5 步流程 + analysis fallback + 異常偏差處理 |
| 2 | edit | `README.md` | v3 升級條件由質性改為四項量化指標（含 4 週持續窗口） |
| 3 | create | `memory/active_projects/agent-harness/decisions/20260426-D007_v3-trigger-quantification.yaml` | 量化選值依據 + 風險 + revisit trigger |

## DoD 比對

| # | 條件 | 結果 |
|---|------|:----:|
| 1 | COST_POLICY 校準 SOP 完整 | ✅ |
| 2 | README v3 改為量化 | ✅ |
| 3 | D007 紀錄量化選值依據 | ✅ |
| 4 | CI 三檢全綠 | ✅ |
| 5 | AUDIT_LOG_2026-Q2.md 新增 1 筆 | ✅ |

DoD 5/5 通過。

## 關鍵量化指標

**v3 升級觸發**（任一持續 ≥ 4 週）：
- Context 接近上限：單月 ≥ 3 次 budget ≥ 90%
- 失敗模式重複：同一 ID 4 週內 ≥ 3 次
- 任務超預算：同 skill 連續 ≥ 3 筆超 COST_POLICY 上限
- 規則衝突：跨 skill routing 拆分需求單月 ≥ 5 次

**校準 SOP 觸發**（任一）：
- 累積 ≥ 5 筆新任務
- 任一 skill 新增 ≥ 3 筆實測
- 單筆超 skill 上限 ≥ 2 次（立即重算該 skill）

## 校準資料

- 預估 tokens：~10K
- 工具呼叫：file_read ×2、file_edit ×2、file_write ×2、bash ×3
- ops 上限 19K，本卡符合預算
