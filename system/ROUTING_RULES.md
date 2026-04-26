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

## 量化拆分閾值（同一 skill 內）

當下列任一條件成立，建議將單張卡拆為 2 張或更多：

| 閾值 | 說明 | 建議行動 |
|------|------|---------|
| `definition_of_done` ≥ 8 條 | DoD 過長代表目標已雜湊 | 依語意分群，每群一張卡 |
| `max_tool_calls` 估 > 25 | 預期工具呼叫量逼近單任務上限 | 拆為前後段，前段 checkpoint 為後段輸入 |
| 預估 token > skill 校準上限 × 1.5 | 超出 COST_POLICY 任務級預算的安全邊界 | 縮 scope 或拆段 |
| 牽涉檔案 > 8 個（read + write 合計） | 上下文壓力升高，gate 驗證難覆蓋 | 按目錄/模組分卡 |

> 校準上限參考 `system/COST_POLICY.md` 任務級預算（research 32K / writing 30K / ops 19K / review 23K / analysis 20K）。
> 觸發任一閾值時，於 Task Card `context` 欄位註明拆分理由。
