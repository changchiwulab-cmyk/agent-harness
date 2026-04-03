# 路由規則 ROUTING_RULES

## Skill 路由判斷

根據任務性質路由到對應 skill：

| 任務關鍵字 | Skill | 說明 |
|-----------|-------|------|
| 調查、研究、比較、查證 | research | 資料蒐集與事實查核 |
| 評估、決策、選擇、可行性、Go/No-Go | analysis | 決策支援與策略分析 |
| 撰寫、草稿、提案、報告、文案、SOP | writing | 內容產出 |
| 整理、清洗、轉換、排程、歸檔、組織 | ops | 營運操作 |
| 審查、校對、檢查、驗證、回測 | review | 品質審查 |

## 前置流程

需求不明確時，先走 `system/INTAKE_FLOW.md` 的 intake 流程釐清需求，再進入路由。

## 路由規則

1. 如果任務明確對應單一 skill → 直接路由
2. 如果任務跨兩個 skill（例如「研究後撰寫報告」）→ 拆成兩張 Task Card，依序執行
3. 如果無法判斷 skill 類型 → 詢問使用者，不要猜
4. 不做開放式的 agent-to-agent 對話路由
5. 路由判斷本身不應消耗大量 token（不需要 LLM 做複雜推理）

## 複合任務拆分原則

- 一張 Task Card 只對應一個 skill
- 如果一個需求需要多個 skill → 拆成多張 Task Card
- Task Card 之間用 output 檔案作為接力點
- 例如：research → outputs/drafts/research_note.md → writing 讀取並產出報告
