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

## 模型路由（見 system/MODEL_ROUTING.yaml）

skill 路由決定「用哪個 skill」，模型路由決定「用哪個模型」，兩者平行：

| 階段 phase | tier | 模型 | 對應子代理 |
|-----------|------|------|-----------|
| explore / retrieve（讀取、搜尋） | fast | Haiku 4.5 | fast-reader |
| test / review（測試、驗證、審查） | test | Sonnet 4.6 (high) | tester |
| synthesize / plan（統整、規劃、策略） | strategy | Opus 4.8 (max) | synthesizer |

- phase 優先於 skill_type；未標 phase 時用 `by_skill_default`（research/ops→fast、review→test、analysis/writing→strategy）。
- 同卡多階段可用不同模型：於 Task Card 的 `model_routing.phase_overrides` 宣告，或依「一卡一 skill」拆卡。
- 以 Claude Code sub-agent 的 `model` 參數落實（查 MODEL_ROUTING.yaml 帶出 id）；固定查表式派工，非開放 agent-to-agent 對話（符合上方規則 4）。
- `reasoning_effort`（high/max）為意圖宣告，非程式強制。
