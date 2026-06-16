# 路由規則 ROUTING_RULES

## Skill 路由判斷

根據任務性質路由到對應 skill：

| 任務關鍵字 | Skill | 說明 |
|-----------|-------|------|
| 調查、研究、比較、事實查核 | research | 資料蒐集與分析 |
| 決策、評估、Go/No-Go、方案比較、可行性 | analysis | 決策支援與策略分析 |
| 撰寫、草稿、提案、報告、文案、SOP | writing | 內容產出 |
| 整理、清洗、轉換、排程、歸檔、組織 | ops | 營運操作 |
| 審查、校對、檢查、驗證、回測 | review | 品質審查 |
| 多步驟依賴、並行子任務、fan-out/fan-in、跨 skill 編排 | orchestration | 有界編排（父卡 + 子任務 DAG） |

## 路由規則

1. 如果任務明確對應單一 skill → 直接路由
2. 如果任務跨兩個 skill 且為單純線性接力（例如「研究後撰寫報告」）→ 拆成兩張 Task Card，依序執行
3. 如果無法判斷 skill 類型 → 詢問使用者，不要猜
4. **不做開放式 agent-to-agent 自由對話**；需要多代理時改用「有界編排」（orchestration 父卡 + 子任務 Task Card DAG），見決策 D009 與 `outputs/reports/bounded-orchestration-design-v1.md`
5. 路由判斷本身不應消耗大量 token（不需要 LLM 做複雜推理）

## 複合任務拆分原則

- 一張子任務 Task Card 只對應一個 skill
- 如果一個需求需要多個 skill → 拆成多張 Task Card
- **線性接力**：Task Card 之間用 output 檔案作為接力點
  - 例如：research → outputs/drafts/research_note.md → writing 讀取並產出報告
- **有界編排（orchestration）**：當子任務有依賴關係或可並行時，用 orchestration 父卡表達 DAG
  - 父卡 `subtasks` 宣告每個子任務卡與 `depends_on`；無依賴者可經原生 Agent tool 並行 fan-out
  - 每個子任務仍是獨立 Task Card，各自走四層 gate 與 checkpoint
  - 父卡 `fan_in.into` 為彙整點；編排層不繞過任何既有治理
