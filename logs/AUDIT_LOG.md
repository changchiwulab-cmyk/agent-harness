# Audit Log — 索引

本檔為各季稽核紀錄的索引與格式說明。
**新紀錄請寫入當季的分檔**（如 `logs/AUDIT_LOG_2026-Q2.md`），而非本檔。

---

## 季度分檔

| 季度 | 檔案 | 任務筆數 | 狀態 |
|------|------|:------:|------|
| 2026-Q2 | [`AUDIT_LOG_2026-Q2.md`](AUDIT_LOG_2026-Q2.md) | 16+ | active |

> 分檔規則：每季開始建立新檔；上一季封存（不再新增），但原檔保留。
> 觸發新檔建立：每季首次寫入時建立，以日期判定。

---

## 紀錄格式（適用所有季度檔）

```yaml
- task_id: ""
  date: ""
  skill_type: ""           # research / analysis / writing / ops / review
  goal: ""                 # 一句話
  status: ""               # done / failed / partial
  model_used: ""           # claude-sonnet-4-20250514 等
  tools_called:            # 實際呼叫的工具清單
    - tool_name: ""
      call_count: 0
  checkpoints: 0           # checkpoint 次數
  approval_needed: false
  approval_given: false
  output_path: ""          # 輸出檔案路徑
  error_summary: ""        # 如有錯誤，簡述
  estimated_tokens: ""     # 預估 token（粗略即可）
  notes: ""                # 其他備註
```

## 與其他治理檔的關聯

- `system/EXECUTION_LOG_SCHEMA.yaml`：詳細執行紀錄（窄範圍：failed / partial / high-risk / 多 checkpoint 任務）的 schema 與寫入規則
- `system/GATE_POLICY.yaml`：稽核紀錄為驗證通過後的最終步驟
- Task Card 的 `audit_log_ref` 欄位：指向當季分檔路徑
