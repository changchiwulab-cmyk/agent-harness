# Agent-Harness 快速上手

Agent-Harness 是一人公司的 AI 任務執行框架，核心設計原則是「穩定可控」而非「功能最多」。第一步：建立 Task Card。

## 三件事先記住

**Task Card 是唯一入口。** 沒有 Task Card，任何任務都不執行。Task Card 定義目標（goal）與完成標準（definition_of_done），讓 agent 知道做什麼、做到什麼程度算完成。

**權限分三層。** `allow`（直接執行）涵蓋讀檔、搜尋、寫草稿、git commit。`ask`（需確認）涵蓋修改規則、寫正式報告、寫長期記憶。`deny`（絕對禁止）涵蓋刪除、對外發送、金流操作。不確定屬哪層，查 `system/PERMISSIONS.yaml`。

**輸出先到 `outputs/drafts/`。** 所有產出都是草稿，等人工確認後才視需要移至正式位置。不需要的草稿不刪除，保留供查核。

## 第一個動作

閱讀 `tasks/TASK_CARD_TEMPLATE.yaml`，照格式建立第一張 Task Card。

字數：127
