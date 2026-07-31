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
| CLAUDE.md + GLOBAL_RULES | 控制在 3K 以內 | 硬上限（CI blocking）；實測 ~2,340 tokens（1,106 + 1,234，2026-07-31 本次改動後量；改動前為 1,620） |
| 單一 skill prompt | 控制在 1.5K 以內 | 硬上限（CI blocking）；只計 SKILL.md（eval_examples 屬 eval 資產不計入），實測 baseline 521–985 tokens |
| 常駐 system prompt 快取 | 命中省 ~90% input | prompt caching：穩定前綴（CLAUDE.md+GLOBAL_RULES+PERMISSIONS）做 cache，可變後綴（Task Card+skill）後接 |
| 最小可快取前綴 | Opus 5：512 tokens<br>Opus 4.8：1,024 tokens | 低於門檻**不會報錯，只是靜默不快取**。本 repo 穩定前綴實測 ~2,340 tokens，兩個世代都在門檻之上 → 上一列的「載入順序 cache 友善」宣稱**成立且有量測支撐**（20260731-A01） |

> baseline 量測方式：`ruby scripts/check_context_budget.rb`（ASCII/4 + 非 ASCII ×1，保守上界）。
> 2026-07-31 校正前本表記載 ~400 / 200-600，與實測差 4.05× / 1.64×，且與 `CLAUDE.md` 的
> skill baseline 記載（480-990）互相矛盾——屬雙寫漂移。改動 CLAUDE.md 或 SKILL.md 後請重跑並回填，
> **包含同一次改動自己造成的增量**（本次 1,620 → 2,340 即為一例：先填了改動前的數，經 review 才補正）。

## 模型路由規則（2026-05-29 起：已落地於原生子代理）

以 `.claude/agents/*.md` 的 per-agent `model` 欄位落地分流（context 隔離另估省 ~67%）：

| 子代理 | model（alias→當代對映） | 對應 skill | 依據 |
|--------|------------------------|-----------|------|
| ops-specialist | haiku → Haiku 世代 | ops | 分類、抽取、格式檢查 → 便宜模型 |
| research-specialist | sonnet → Sonnet 世代 | research | 整合分析 |
| writing-specialist | sonnet → Sonnet 世代 | writing | 內容產出 |
| review-specialist | sonnet → Sonnet 世代 | review | 品質判斷 |
| analysis-specialist | opus → Opus 世代 | analysis | 規劃、推理、決策 → 強模型 |

- alias（haiku/sonnet/opus）會自動對映到當代各層級最新模型，無需追版本——**故本表刻意不寫死版本號**
  （2026-05-29 建表時寫的 Haiku 4.5 / Sonnet 4.6 / Opus 4.8 到 2026-07-31 已全部過期，即為教訓）。
  實際跑在哪個模型以執行紀錄的 `request_model` 為準（見 `system/EXECUTION_LOG_SCHEMA.yaml`）。
- 路由判斷本身改由原生 skill description 自動觸發，不再需要獨立的「路由模型」。
- 校準資料（下方各 skill 實測平均）回填時，可據以調整對應子代理的分層（成本長期偏高 → 升一層模型）。

## effort 維度（2026-07-31 新增；20260731-A01）

成本模型從**一維**（只有 model tier）升為**二維**（tier × effort）。上表選「哪一層模型」，
本節選「同一層模型花多少力氣」。兩者獨立，都會影響成本與品質。

| skill_type | 建議起始 effort | 依據 |
|-----------|:--------------:|------|
| ops | `low` | 分類、抽取、格式轉換等機械性工作，不吃推理深度 |
| research / writing / review | `medium` | 整合、產出、判斷；需要推理但非開放式規劃 |
| analysis | `high`（複雜決策可試 `xhigh`） | 規劃、多方案推理、決策整合 |

**方法：設起點後往下掃，掃到品質開始掉為止。** 不要沿用前代預設，也不要反射性選最高檔——
新世代模型的低檔位常已勝過前代高檔位（見下方註記 2），沿用舊直覺會多付錢買不到品質。

### 兩個反直覺註記（避免誤用）

1. **effort 不是縮短輸出的手段。** 降 effort 會改變思考量，**不會可靠縮短可見輸出**。
   要縮短交付物長度請改 prompt（見 `system/GLOBAL_RULES.md`「長度紀律」），不要調 effort。
2. **低 effort 已可能勝過前代高 effort。** 這動搖了上表「便宜任務用便宜模型」的分流前提——
   同一任務用「強模型 + low effort」可能比「便宜模型 + 預設 effort」更好又不見得更貴。
   2026-07-31 的決策是**先保留三層分流不動**，把這個張力記錄下來當觀察點：
   累積 ≥3 筆帶 effort 標註的樣本後，於下次 retro 重新評估是否改為單一模型 + effort 分層。
   理由是不能「同時改變數與量尺」——見下方校準係數表的時代標記。

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

> ⚠️ **本表所有樣本為 pre-Opus-5、effort 未標註（2026-07-31 標記）。**
> 這些樣本是在無 effort 概念的年代量的，不知道當時跑在哪個檔位，因此**不可與新樣本混算**。
> 表的殘餘價值是記錄了「原預估普遍低估 25%–100%」這個事實，可續用於粗估；
> 但要重建可分層解讀的成本模型，必須累積帶 effort 標註的新樣本。
> **新樣本必須記錄 effort**（欄位見 `system/EXECUTION_LOG_SCHEMA.yaml` 的 `effort`）。

| skill_type | 原預估 | 實測平均 | 校準係數 | 樣本數 | effort |
|-----------|------:|--------:|--------:|:-----:|:------:|
| research | 15K | 21.5K | **1.43** | 2 | 未標註 |
| writing  | 10K | 20K   | **2.00** | 1 | 未標註 |
| ops      | 8K  | 12.5K | **1.56** | 2 | 未標註 |
| review   | 12K | 15K   | **1.25** | 2 | 未標註 |
| analysis | 12K | —     | 待累積    | 0 | — |

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
