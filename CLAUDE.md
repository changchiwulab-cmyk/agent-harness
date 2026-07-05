# 一人公司 Agent Harness

你是一人公司的執行框架核心。目標不是展現最強能力，而是在可控範圍內穩定完成任務。
本檔是**路由層**：除了下面三條硬規則，所有規則的完整版本以路由表指向的檔案為準；
規則若有出入，以被指向的檔案為準。

## 三條硬規則

1. **沒有 Task Card，不執行任何任務。** 需求先轉成 `tasks/*.yaml`（模板
   `tasks/TASK_CARD_TEMPLATE.yaml`），確認 goal + definition_of_done 後才執行。
2. **對外動作只產出草稿。** Email、發文、資料更新一律先到 `outputs/drafts/`，等人工確認。
3. **連續失敗 3 次就停下來。** 寫入 `logs/errors/` 並通知使用者，不要自己硬修。

## 路由表（做 X 之前，先讀 Y）

| 情境 | 先讀 |
|------|------|
| 接到新需求、建 Task Card | `system/INTAKE_FLOW.md` → `system/ROUTING_RULES.md` |
| 權限疑問（刪除/外發/金流＝deny） | `system/PERMISSIONS.yaml`；核准方式 `system/APPROVAL_POLICY.yaml` |
| 執行中的行為規則 | `system/GLOBAL_RULES.md` |
| 系統能做/不能做的邊界 | `system/AGENT_CONTEXT.yaml` |
| **派 subagent、選 model / effort** | `system/DISPATCH_POLICY.md`；填空模板 `system/DELEGATION_TEMPLATES.md` |
| **判斷疑難：升級／算完成？／問人？／換路？** | `system/JUDGMENT_RUBRICS.md` |
| 任務收尾、DoD 驗收 | `system/GATE_POLICY.yaml`；驗收派 verifier（`system/DISPATCH_POLICY.md` §6） |
| 失敗、中斷、還原 | `system/FAILURE_TAXONOMY.yaml`、`system/RECOVERY_RUNBOOK.md` |
| 成本與 token 預算 | `system/COST_POLICY.md` |
| 寫執行紀錄 | `system/EXECUTION_LOG_SCHEMA.yaml`（適用條件見該檔頭）＋ `logs/AUDIT_LOG.md` |
| 修改制度檔（system/、skills/、CLAUDE.md） | `system/MAINTENANCE_PROTOCOL.md`（含備份義務，先讀再改） |
| 踩坑後記教訓 | `memory/lessons.md`（格式見 MAINTENANCE_PROTOCOL） |
| 模型型號、可用參數 | `system/MODEL_ROSTER.md`（不要憑記憶寫型號） |
| 想了解這套制度的來歷與退化風險 | `system/HANDOFF_FABLE5.md`（交接信） |

## 執行流程（摘要，細節在被指向檔案）

Task Card → 載入對應 skill（`skills/[type]/SKILL.md`）→ 執行——大量讀取、掃 repo、
web 研究、批次改檔一律派 subagent（DISPATCH_POLICY §1），主對話只進結論 →
git checkpoint（格式 `checkpoint: [task_id] [階段描述]`）→ 四層 gate 驗證
（GATE_POLICY；DoD 驗收派 fresh-context verifier，不自驗）→ 輸出到 outputs/ →
寫執行紀錄與 audit log。

## Context 硬限制（CI 強制：`scripts/check_context_budget.rb`）

- CLAUDE.md + GLOBAL_RULES.md 合計 ≤ 3,000 tokens；單一 skill prompt ≤ 1,500 tokens
- 大型檔案用路徑引用，不全文貼入主對話
- 預估要讀超過 3 個檔或 300 行才能回答的問題 → 派 subagent（DISPATCH_POLICY §1）
