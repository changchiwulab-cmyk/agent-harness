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
| CLAUDE.md + GLOBAL_RULES | 控制在 3K 以內 | 軟性上限；實測 2,130 tokens（20260725-A01 後，`check_context_budget.rb`；舊註記「~400」已過期逾 5 倍） |
| 單一 skill prompt | 控制在 1.5K 以內 | 軟性上限；**只計執行期載入的 SKILL.md**，eval_examples 屬 eval 資產不計入（20260711-A01 口徑對齊）。實測 483–985 tokens |
| 常駐 system prompt 快取 | 命中省 ~90% input | prompt caching：穩定前綴（CLAUDE.md+GLOBAL_RULES+PERMISSIONS）做 cache，可變後綴（Task Card+skill）後接。前綴須達最小可快取長度才會生效，見 `CONTEXT_ENGINEERING.md` §一 |

## 模型路由規則（2026-05-29 起落地於原生子代理；20260725-A01 補 effort 維度）

以 `.claude/agents/*.md` 的 per-agent `model` 欄位落地分流（context 隔離另估省 ~67%）：

| 子代理 | model（alias→當代層級首選） | 建議 effort | 對應 skill | 依據 |
|--------|---------------------------|------------|-----------|------|
| ops-specialist | haiku → Haiku 4.5 | low | ops | 分類、抽取、格式檢查 → 便宜模型 |
| research-specialist | sonnet → Sonnet 5 | medium | research | 整合分析 |
| writing-specialist | sonnet → Sonnet 5 | medium | writing | 內容產出 |
| review-specialist | sonnet → Sonnet 5 | medium–high | review | 品質判斷；漏抓比多抓貴 |
| analysis-specialist | opus → Opus 5 | high | analysis | 規劃、推理、決策 → 強模型 |

- alias（haiku/sonnet/opus）會自動對映到當代各層級最新模型，無需追版本。**上表右欄只是當下的對映結果，非設定值**；不要把具體版本寫死進 `.claude/agents/*.md`。
- 路由判斷本身改由原生 skill description 自動觸發，不再需要獨立的「路由模型」。
- 校準資料（下方各 skill 實測平均）回填時，可據以調整對應子代理的分層（成本長期偏高 → 降 effort 或降一層模型）。

### effort：成本路由的第二維（20260725-A01 新增）

成本路由過去只有「選哪個模型」一維。當代模型另有 `effort`（`low` / `medium` / `high` / `xhigh` / `max`），
控制思考深度與整體 token 花費，**且它是比換模型更細緻的槓桿**：

- 同一模型降一級 effort，通常比降一層模型更能保住品質。**先調 effort，再考慮換模型。**
- Opus 5 世代的 `low` / `medium` 表現相對前代異常強，routine 工作不需預設高 effort。
- 反向陷阱：**effort 不是控制輸出長度的旋鈕**。要縮短產出用 prompt（見 `GLOBAL_RULES.md` 的產出篇幅段），
  調 effort 可能只改變思考量而不改變可見輸出長度。
- 高 effort（`xhigh` / `max`）需搭配足夠的 `max_tokens`，否則思考佔滿預算、答案被截斷。

設定位置與取捨：

| 方式 | 範圍 | 取捨 |
|------|------|------|
| `/effort` 指令 | 當前 session | 臨時調整，不入庫 |
| `.claude/settings.json` 的 `effortLevel` | 專案全域 | **本專案刻意不設**：會蓋掉使用者的當下判斷，屬個人偏好而非治理規則 |
| 本表「建議 effort」欄 | 契約層 | 現行做法：寫成建議值供人工與子代理參照，不強制 |

> 為什麼不寫進 `settings.json`：`model` / `effortLevel` 一旦寫死，使用者在該 repo 內就失去 `/model`、
> `/effort` 的臨場調整空間。成本路由是**建議**，不是 deny 級的硬規則，維持在文件層是正確的執法強度。

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
| writing | ~10K | ~20K（1 筆）| **30K** | ⚠️ pending stabilization：僅 1 筆、變異大；暫定硬天花板 40K，累積 ≥3 筆前從嚴估 |
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
- ⚠️ writing 係數 2.00 僅來自 1 筆，標 pending stabilization；累積 ≥3 筆前從嚴估、暫定硬天花板 40K
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
