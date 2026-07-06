# Error Log 格式

當任務連續失敗 3 次或遭遇規則違反時，在此目錄建立 error log。
命名規則：`[task_id]_error.md`（task_id 已含日期 YYYYMMDD-###，避免重複日期前綴）

> 註：`2026-04-04_20260404-S01_error.md` 為早期格式之歷史檔，保留原名以維持外部引用。

---

## 紀錄格式

```yaml
error_id: ""                    # 格式：ERR-YYYYMMDD-001
task_id: ""                     # 對應的 Task Card ID
date: ""                        # 發生日期
time: ""                        # 發生時間（約略即可）
skill_type: ""                  # research / analysis / writing / ops / review

# === 錯誤描述 ===
error_type: ""                  # tool_failure / rule_violation / schema_failure / timeout / unknown
error_summary: ""               # 一句話描述
failure_count: 0                # 連續失敗次數
last_action: ""                 # 失敗前的最後動作

# === 診斷 ===
root_cause: ""                  # 已知原因（如能判斷）
attempted_fixes: []             # 嘗試過的修復方式
related_rule: ""                # 觸犯的規則（如適用）

# === 處置 ===
resolution: ""                  # stopped / escalated / retried_success
user_notified: false            # 是否已通知使用者
follow_up: ""                   # 後續行動建議
```

---

## 錯誤分類速查

| error_type | 觸發條件 | 預設處置 |
|------------|---------|---------|
| tool_failure | 工具呼叫回傳錯誤 | 重試 1 次，仍失敗則停止 |
| rule_violation | 違反 GLOBAL_RULES 或 PERMISSIONS | 立即停止 |
| schema_failure | Task Card 或輸出格式不合規 | 重試 1 次，仍失敗則停止 |
| timeout | 工具呼叫或任務逾時 | 記錄後停止 |
| unknown | 無法分類的錯誤 | 記錄後停止，等待人工判斷 |
