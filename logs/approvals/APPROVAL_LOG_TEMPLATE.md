# Approval Log Template

當任務觸發 `system/APPROVAL_POLICY.yaml` 中的審批條件時，依此模板記錄。

檔名格式：`YYYY-MM-DD_{task_id}_approval.md`
存放位置：`logs/approvals/`

---

## 使用範圍

不是每個任務都需要寫 approval log。下列情境**必寫**：

1. `risk_level >= high`（high / critical）
2. 對外動作（email、發文、API call）
3. 修改 `system/` 或 `skills/` 下任何檔案
4. 寫入 `memory/` 長期記憶
5. 寫入 `outputs/reports/`（從 drafts/ 晉升）

`risk_level: low/medium` 的一般任務只寫 `logs/AUDIT_LOG.md` 即可，不需要單獨的 approval log。

---

## 模板（以下整段複製到新檔）

```yaml
approval:
  approval_id: "APR-YYYYMMDD-###"   # 唯一識別碼，與 task_id 相關
  task_id: ""                       # 對應的 Task Card ID
  date: "YYYY-MM-DD"
  risk_level: ""                    # low / medium / high / critical

  # --- 觸發條件 ---
  trigger: ""                       # 對應 APPROVAL_POLICY.yaml 哪一條 trigger
  # 範例：
  # trigger: "修改 system/ 目錄下任何檔案"

  # --- 擬定動作 ---
  proposed_action:
    type: ""                        # file_modify / file_create / external_send / report_publish
    target: ""                      # 受影響的檔案路徑或外部目標
    summary: ""                     # 一句話描述要做什麼

  # --- 審批方法（依 APPROVAL_POLICY.yaml）---
  approval_method: ""               # human_confirm / draft_first / deny_by_default

  # --- 審批結果 ---
  approval:
    status: ""                      # approved / rejected / superseded
    approved_by: "human"
    timestamp: "YYYY-MM-DD HH:MM"
    comments: ""                    # 使用者附註（若有）

  # --- 後續追蹤 ---
  resulting_commit: ""              # 動作落地的 git commit hash
  audit_log_ref: ""                 # logs/AUDIT_LOG.md 中對應的條目位置
```

---

## 範例（高風險任務示意）

```yaml
approval:
  approval_id: "APR-20260427-001"
  task_id: "20260427-X01"
  date: "2026-04-27"
  risk_level: "high"
  trigger: "修改 system/ 目錄下任何檔案"
  proposed_action:
    type: "file_modify"
    target: "system/PERMISSIONS.yaml"
    summary: "新增 v3 升級觸發條件至 risk_levels 區段"
  approval_method: "human_confirm"
  approval:
    status: "approved"
    approved_by: "human"
    timestamp: "2026-04-27 14:30"
    comments: "確認觸發條件可量化即可"
  resulting_commit: "abc1234"
  audit_log_ref: "logs/AUDIT_LOG.md#20260427-X01"
```

---

## 與其他 log 的關係

- `logs/AUDIT_LOG.md`：每張 Task Card 都寫一條（happy-path 也寫）
- `logs/runs/*.yaml`：依 EXECUTION_LOG_SCHEMA.yaml，僅失敗 / partial / 高風險 / 多 checkpoint 寫
- `logs/approvals/*.md`：本格式，僅觸發審批條件寫
- `logs/errors/*.md`：依 ERROR_LOG_TEMPLATE.md，失敗才寫

四種日誌彼此互補，不重複。

---

*建立日期：2026-04-27*
*來源：Task Card 20260427-A01*
*Schema 對齊：system/EXECUTION_LOG_SCHEMA.yaml 的 approvals 區段*
