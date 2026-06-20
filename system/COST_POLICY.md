# 成本控制策略 COST_POLICY

## 當前方案（v1）

v1 階段採用「粗略護欄 + 事後量測」策略：

- **硬上限**：透過 Anthropic API dashboard 的 spending limit 設定月度/日度上限
- **軟上限**：透過 CLAUDE.md 規則限制單一任務的工具呼叫次數與重試次數
- **事後追蹤**：每次任務完成後在 audit log 記錄預估 token 消耗

## 行為規則

### 節省 token 的做法
- 能讀檔解決的不做 web search
- 單次查詢能解決的不拆多次
- 大型檔案用路徑引用，不全文貼入
- 重複內容用摘要取代
- Context 接近上限時主動壓縮

### 工具呼叫限制
- 單一任務最多 5 次外部工具呼叫後需 checkpoint
- 單一任務最多 3 輪 web search
- 連續失敗重試上限 3 次

### 超限行為
- 工具呼叫達上限 → checkpoint，通知使用者決定是否繼續
- 連續失敗達上限 → 停止執行，記錄到 error log
- 發現任務範圍遠超預期 → 暫停，建議拆分任務

## Context 量化基準（參考值）

| 項目 | Token 消耗 | 備註 |
|------|-----------|------|
| 工具定義（完整載入） | 55K–134K | 工具越多越肥 |
| 工具定義（按需載入） | 省 ~85% | Tool Search 模式 |
| 子代理 context 隔離 | 省 ~67% | vs 單一代理塞所有 context |
| Programmatic Tool Calling | 省 ~37% | 中間結果不進 context |
| CLAUDE.md + GLOBAL_RULES | 控制在 3K 以內 | 硬限制 |
| 單一 skill prompt | 控制在 1.5K 以內 | 硬限制 |

## 模型路由規則（2026-06 落地，最新模型）

依任務階段把工作分派到對應等級的模型，用便宜模型做確定性／重複工，用強模型做規劃／推理。模型事實經 `claude-api` skill 校準（價格＝input/output，每 1M tokens）：

| 用途 | 模型 | model id | 價格 |
|------|------|----------|------|
| 規劃、analysis、review 推理、整合判斷 | Claude Opus 4.8 | `claude-opus-4-8` | $5 / $25 |
| 預設執行、writing、一般 ops、高量產 | Claude Sonnet 4.6 | `claude-sonnet-4-6` | $3 / $15 |
| 分類、抽取、格式/schema 檢查、lint、路由判斷 | Claude Haiku 4.5 | `claude-haiku-4-5` | $1 / $5 |
| 最難的長程 agentic／一次到位的複雜實作 | Claude Fable 5 | `claude-fable-5` | $10 / $50 |

規則：
- 確定性、可機械驗證的步驟（schema 檢查、lint、分類、**eval-judge 評分**）一律下放 Haiku 4.5，不佔強模型額度。（L5 `scripts/run_skill_evals.py` 預設 `claude-haiku-4-5`。）
- 規劃/推理/最終整合用 Opus 4.8（預設）；只有當任務複雜度超出 Opus 且值得時才升 Fable 5。
- 路由判斷本身屬 Haiku 等級，不應消耗重 token（見 `ROUTING_RULES.md` 複雜度原則）。
- 切換模型會使 prompt cache 失效（快取是 model-scoped）；同一會話內盡量固定主模型，子任務再隔離。

## Prompt Caching 策略（2026-06 新增）

快取是 2026 最大成本槓桿：cache 讀 ~0.1× input 價、寫 1.25×（5 分鐘 TTL）/ 2×（1 小時 TTL），穩定前綴可省 ~90%。快取是**前綴比對**——前綴任一 byte 改變即讓其後全部失效。

落地原則（本 harness 的穩定前綴＝CLAUDE.md + GLOBAL_RULES + AGENT_CONTEXT + 載入的 skill）：
- **穩定內容置前、動態內容置後**：boot prompt 與載入的 skill 放最前；Task Card 具體內容、時間戳、每輪查詢放最後一個 cache 斷點之後。
- **凍結前綴**：不要把「今天日期 / session id」插進 system 段（會每次失效）；動態 context 改放後段訊息。
- **斷點放在穩定／易變邊界**：`cache_control: {type: "ephemeral"}`（5 分鐘）為預設；跨較長間隔的批次用 `ttl: "1h"`。單一請求最多 4 個斷點。
- **最小可快取前綴（model-scoped）**：Opus 4.8 / Haiku 4.5 = 4096 tokens；Sonnet 4.6 / Fable 5 = 2048 tokens。前綴過短會靜默不快取。
- **驗證**：看回應 `usage.cache_read_input_tokens`；若重複同前綴請求仍為 0，代表有隱性失效源（system 內的時間戳/UUID、未排序 JSON、變動的工具集）。
- **損益平衡**：5 分鐘 TTL 兩次請求即回本；1 小時 TTL 需三次以上。

## Context Engineering 原則（2026-06 新增）

對標 2026 context-engineering 最佳實踐，把既有慣例形式化：

- **Just-in-time（JIT）載入**：不預先把所有資料塞進 context；維持輕量識別子（檔案路徑、查詢、URL），用工具在執行時動態載入。大型檔案一律路徑引用（呼應「節省 token」段）。
- **關鍵規則須存活壓縮**：壓縮/摘要會丟棄細節，因此硬規則必須留在 boot prompt（CLAUDE.md / GLOBAL_RULES），不可只存在於易被壓掉的對話歷史。長對話 20 輪後的摘要壓縮只壓「過程」，不壓「規則」。
- **memory 為獨立架構元件**：`memory/` 是與 context window 分離的持久層，非「更長的 prompt」；只有經人工確認才寫入（見 GLOBAL_RULES 記憶規則）。跨 session 狀態走 memory，session 內狀態走 context。
- **隔離優於塞滿**：子任務以子代理隔離 context（省 ~67%），中間結果不回主 context；與 prompt caching「凍結前綴」配合。

## 事後量測流程（每週）

1. 查看 Anthropic dashboard 的當週用量
2. 對照 audit log 中的任務紀錄
3. 計算每種任務類型的平均消耗
4. 累積 4 週後，設定任務級別的 token 預算建議值
5. 寫入本文件的「任務級預算」區塊

## 任務級預算（2026-04-15 依首次 RETRO 校正，基於 8 筆 audit log）

| 任務類型 | 預估 token | 實測平均 | 建議上限 | 備註 |
|---------|-----------|---------|---------|------|
| research | ~15K | ~21.5K（2 筆）| **32K** | 含 web search 結果解析；實測超估 43% |
| analysis | ~12K | 待累積 | 20K | 尚無實測；下次 retro 再校正 |
| writing | ~10K | ~20K（1 筆）| **30K** | 實測超估 100%；視輸出長度浮動 |
| ops | ~8K | ~12.5K（2 筆）| **19K** | 實測超估 56% |
| review | ~12K | ~15K（2 筆）| **23K** | 含原文載入 + 逐條檢查；實測超估 25% |

> **校正規則**：累積 10 筆以上同類任務後，用實測平均 × 1.5 作為建議上限。  
> **下次校正**：再累積 5 筆任務後觸發第二次 retro。

## 校準係數（2026-04-17 首次建立）

目的：在建立 Task Card 時，若原預估偏離歷史實測過多，可依該 skill 的係數調整 `max_tool_calls` 與 `max_retries`。資料來源：`outputs/reports/token-calibration-v1.md`（2026-04-24 晉升自 drafts/）。

**定義**：`calibration_factor = actual_avg / initial_estimate`

| skill_type | 原預估 | 實測平均 | 校準係數 | 樣本數 |
|-----------|------:|--------:|--------:|:-----:|
| research | 15K | 21.5K | **1.43** | 2 |
| writing  | 10K | 20K   | **2.00** | 1 |
| ops      | 8K  | 12.5K | **1.56** | 2 |
| review   | 12K | 15K   | **1.25** | 2 |
| analysis | 12K | —     | 待累積    | 0 |

**使用方式**：
- 建立 Task Card 時，若 skill 係數 ≥ 1.5，將 `max_tool_calls` 與 `max_retries` 上調 1 檔作為緩衝
- 係數 < 1.3 視為穩定，依原設定值
- analysis 係數未知，至少 3 筆實測後再更新

**下次校準觸發**：再累積 5 筆任務（含至少 1 筆 analysis）後，於下次 retro 重算。

## 升級觸發條件

當以下任一條件持續 2 週以上，考慮升級到 v2：

| 觸發條件 | 說明 |
|---------|------|
| Context 經常超限 | 單一代理的 context 頻繁需要壓縮，影響任務品質 |
| 規則衝突頻繁 | 不同任務類型間的規則互相干擾 |
| 單任務成本持續超標 | 任務級預算建議值被頻繁突破 |
| 錯誤率上升 | error log 中同類錯誤重複出現 |
