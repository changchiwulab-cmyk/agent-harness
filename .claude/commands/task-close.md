---
description: 收尾 active task：gate 驗證 → 執行紀錄 → 卡片回填 → 解除綁定（執行流程步驟 7–9）
allowed-tools: Bash(python3 scripts/active_task.py:*), Bash(python3 scripts/gate_check.py:*), Bash(python3 scripts/verification_loop.py:*), Bash(bash scripts/sync_derived.sh:*), Bash(scripts/sync_derived.sh:*), Bash(git commit:*), Bash(git add:*), Bash(git log:*), Read, Write, Edit, Glob, Grep
---

# 收尾 active task

依 `CLAUDE.md` 執行流程步驟 7–9。

## 步驟

1. **取得 task_id**：`python3 scripts/active_task.py --get`。idle 就沒東西可收，直接回報。

2. **四層 gate 必須全綠**：`python3 scripts/gate_check.py <task_id>`。
   沒過就回去修，**不要**為了收尾放寬判定。

3. **執行紀錄（條件性）**：符合 `system/EXECUTION_LOG_SCHEMA.yaml` 使用範圍才寫
   `logs/runs/RUN-<...>.yaml`——即 status ∈ {failed, partial}、或 risk ≥ high、或 checkpoints ≥ 3。
   不符範圍就不寫，避免製造沒人讀的紀錄。
   ⚠️ risk ≥ high 且 status ∈ {done, review, failed} 且 date ≥ 2026-07-10 的卡**缺 run log 會直接 FAIL**
   （條件 fail-closed，見 `SECURITY.md`）。

4. **批准紀錄**：`approval_needed: true` 的卡，人工確認後寫 `logs/approvals/APR-<...>.yaml`。
   同一任務第 3 次請求批准 → 暫停並回報（`system/APPROVAL_POLICY.yaml`），不要反覆騷擾使用者。

5. **回填卡片**：`checkpoints`（真實 commit hash，不可造假）、`actual_tool_calls`、
   `result_summary`（逐條對照 DoD 的達成情況）、`completion_time`、`audit_log_ref`。
   status 轉 `review`（待人工確認）或 `done`。

6. **同步衍生物**：`scripts/sync_derived.sh` 重產 `frontend/data.json` + `logs/AUDIT_LOG.md`，
   再跑 `scripts/sync_derived.sh --check` 確認零漂移。

7. **解除綁定**：`python3 scripts/active_task.py --clear`。

8. **最後 checkpoint**：`git commit -m "checkpoint: [<task_id>] 收尾（gate＋紀錄＋回填＋解除綁定）"`

## 完成後

回報：DoD 達成 N/M、gate 結果、產出路徑、卡片新 status、還需要使用者做什麼。
