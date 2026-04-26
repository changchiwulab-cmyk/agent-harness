# 20260426-O04 — Decision Log 補歷史摘要

**任務**：補登 v1→v2 三筆關鍵歷史決策。
**狀態**：done
**完成日期**：2026-04-26

## 變更項目

| # | 動作 | 檔案 | 主題 |
|---|------|------|------|
| 1 | create | `decisions/20260426-D008_approval-policy-extraction.yaml` | Approval Policy 從 GLOBAL_RULES 拆獨立檔（v2） |
| 2 | create | `decisions/20260426-D009_failure-taxonomy-extraction.yaml` | Failure Taxonomy 拆獨立檔，14 模式（v2） |
| 3 | create | `decisions/20260426-D010_analysis-skill-added.yaml` | 第 5 skill「analysis」加入（v2） |

## DoD 比對

| # | 條件 | 結果 |
|---|------|:----:|
| 1 | D008 建立 | ✅ |
| 2 | D009 建立 | ✅ |
| 3 | D010 建立 | ✅ |
| 4 | 遵守 DECISION_LOG_TEMPLATE schema | ✅ |
| 5 | 每筆引用 commit / 時間點作為證據 | ✅（每筆含 evidence 段） |
| 6 | CI 三檢全綠 | ✅ |
| 7 | AUDIT_LOG_2026-Q2.md 新增 1 筆 | ✅ |

DoD 7/7 通過。

## 關鍵調整

- **原訂 D008「不採用資料庫、改用 YAML/MD 為持久層」與既有 D001 重複**。檢查 decisions/ 目錄發現
  D001（2026-04-03 task-card-over-database）已涵蓋此決策。本卡改為三筆未紀錄的 v1→v2 治理決策。
- 三筆皆加入 `evidence:` 自訂段（不在原 schema 中），引用 commit hash / README 段落 / 既有檔案
  作為歷史佐證，提高可追溯性。

## 後續觸發

- D010 註明「analysis skill 在實戰中從未被使用」→ 本次 Card E（20260426-A01）為首次實戰
- D008 / D009 的 revisit_trigger 已掛在 retro 流程上，下次 retro 時自動檢視

## 校準資料

- 預估 tokens：~9K
- 工具呼叫：file_read ×2、file_write ×4、bash ×3
- ops 上限 19K，本卡符合預算
