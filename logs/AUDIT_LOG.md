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

---

## 紀錄（依時間倒序）

<!-- 新紀錄加在這裡 -->

```yaml
- task_id: "20260403-001"
  date: "2026-04-04"
  skill_type: "research"
  goal: "調查越南市場 2026 年主流 AI 生產力工具的採用現況與趨勢"
  status: "done"
  model_used: "claude-sonnet-4-6"
  tools_called:
    - tool_name: "web_search"
      call_count: 3
    - tool_name: "file_read"
      call_count: 4
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/vietnam-ai-tools-research.md"
  error_summary: ""
  estimated_tokens: "~8000"
  notes: "涵蓋 8 個主流工具（5 國際 + 3 本地）；DoD 全部通過四層驗證。台越合作線索（FPT x Startup Island TAIWAN）已收錄。"
```
