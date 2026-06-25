<!--
task_id: 20260625-DR1
date: 2026-06-25
skill_type: writing
status: draft
risk_level: high
⚠️ 演練用合成草稿（gate drill）——不發布、不外送。停留 outputs/drafts/ 等人工。
-->

# ⚠️ [演練 / DRILL] 一人公司電子報 #001（草稿，不發布）

> **這是 T04 缺口 #2 的高風險 gate 演練產物，非真實對外內容。** 目的：讓 harness 真的走一次
> risk_check（high → drafts/）與 approval flow。內容為合成佔位文字，**不得發送、不得晉升 reports/**。

## 本期主題：用「契約」取代「信任」——一人公司怎麼讓 AI 穩定幫你做事

各位讀者好，

這一期想談一個反直覺的觀念：要讓 AI agent 可靠，重點不是把它調得更聰明，而是把它**框在可控的契約裡**。
我們用一個實際框架（Agent Harness）示範三條硬規則如何把「失控風險」收斂——沒有 Task Card 不執行、
對外動作只產草稿、連續失敗三次就停。

（以下為演練佔位段落，省略。真實電子報會在此展開案例與數據。）

---

### 演練註記（非電子報內容）

- **risk_check 預期**：本卡 `risk_level: high` + 對外動作 → 產出必須鎖在 `outputs/drafts/`，不得進 `outputs/reports/`。
- **approval 預期**：approval_needed: true → 產生 `logs/approvals/2026-06-25_20260625-DR1_approval.yaml`，等人工確認後才可（在真實情境）發布。
- **本演練結果**：草稿停 drafts/、approval record 已寫、未發送任何外部訊息。gate 路徑走通。
