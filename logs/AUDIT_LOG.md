# Audit Log

每次任務完成後，在此檔案底部新增一筆紀錄。
格式嚴格遵守以下結構。

---

## 紀錄格式

```yaml
- task_id: ""
  date: ""
  skill_type: ""           # research / writing / ops / review
  goal: ""                 # 一句話
  status: ""               # done / failed / partial
  model_used: ""           # claude-sonnet-4-20250514 等
  model_tier: ""           # lite / standard / strong
  routing_reason: ""       # 為何選這個模型層級
  upgrade_reason: ""       # 若有升級，填原因；無則空字串
  downgrade_reason: ""     # 若有降級，填原因；無則空字串
  tools_called:            # 實際呼叫的工具清單
    - tool_name: ""
      call_count: 0
  checkpoints: 0           # checkpoint 次數
  verify_outcome: ""       # pass / fail_schema / fail_rules / fail_completion / fail_risk
  execution_trace_ref: ""  # 對應 Task Card 內 execution_trace 摘要或路徑
  approval_needed: false
  approval_given: false
  output_path: ""          # 輸出檔案路徑
  error_summary: ""        # 如有錯誤，簡述
  estimated_tokens: ""     # 預估 token（粗略即可）
  notes: ""                # 其他備註
```

---

## 紀錄（依時間倒序）

<!-- 新紀錄加在這裡 -->

### 欄位填寫規範（必填 / 可空）

- **必填**：`task_id`、`date`、`skill_type`、`goal`、`status`、`model_used`、`model_tier`、`routing_reason`、`verify_outcome`、`output_path`
- **條件必填**：`upgrade_reason`（有升級時）、`downgrade_reason`（有降級時）
- **可空**：`error_summary`（無錯誤時）、`execution_trace_ref`（未使用 execution_trace 時）
- `estimated_tokens` 建議填實際估值；若無法估算可填 `"unknown"`
- 可用 `python scripts/check_audit_log_fields.py` 做必要欄位快速檢查

### 範例紀錄（含路由/驗證欄位）

```yaml
- task_id: "20260407-002"
  date: "2026-04-07"
  skill_type: "research"
  goal: "整理競品定價並輸出草稿摘要"
  status: "done"
  model_used: "example-model-strong"
  model_tier: "strong"
  routing_reason: "任務包含跨來源整合與高風險結論段落"
  upgrade_reason: "首次輸出未通過 completion 驗證"
  downgrade_reason: ""
  tools_called:
    - tool_name: "web_search"
      call_count: 2
    - tool_name: "file_read"
      call_count: 3
  checkpoints: 2
  verify_outcome: "pass"
  execution_trace_ref: "tasks/2026-04-07_competitor-pricing.yaml#execution_trace"
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/competitor-pricing-summary.md"
  error_summary: ""
  estimated_tokens: "4200"
  notes: "第二輪輸出後通過四層驗證"
```
