# 成本控制策略 COST_POLICY

## 成本護欄

- **硬上限**：Anthropic dashboard 的 spending limit（月／日）。
- **任務級上限**：Task Card 的 `max_tool_calls` / `max_retries` / `max_web_searches`，逐卡設定；不設全域次數規則（20261031-P02：原「5 次呼叫／3 輪查詢」全域規則與實測不符，已移除）。
- **失敗熔斷**：連續失敗 3 次由 `scripts/failure_counter.py` hook 自動攔阻。
- **超限行為**：達上限 → checkpoint 並通知使用者決定是否繼續；範圍遠超預期 → 暫停、建議拆卡。

## Context 量化基準（參考值）

| 項目 | Token 消耗 | 備註 |
|------|-----------|------|
| 工具定義（完整載入） | 55K–134K | 工具越多越肥 |
| 工具定義（按需載入） | 省 ~85% | Tool Search 模式 |
| 子代理 context 隔離 | 省 ~67% | vs 單一代理塞所有 context |
| Programmatic Tool Calling | 省 ~37% | 中間結果不進 context |
| CLAUDE.md + GLOBAL_RULES | 控制在 3K 以內 | 軟性上限；實測 baseline ~400 tokens |
| 單一 skill prompt | 控制在 1.5K 以內 | 軟性上限；只計執行期載入的 SKILL.md（eval_examples.md 不計），實測 baseline 480-990 tokens（與 CLAUDE.md 同口徑） |
| 常駐 system prompt 快取 | 命中省 ~90% input | prompt caching：穩定前綴（CLAUDE.md+GLOBAL_RULES）做 cache，可變後綴（Task Card+skill）後接 |

## 模型路由規則（2026-05-29 起：已落地於原生子代理）

以 `.claude/agents/*.md` 的 per-agent `model` 欄位落地分流（context 隔離另估省 ~67%）：

| 子代理 | model（alias→實際，2026-10-31 校正） | 對應 skill | 依據 |
|--------|--------------------|-----------|------|
| ops-specialist | haiku → Haiku 5.5 | ops | 分類、抽取、格式檢查 → 便宜模型 |
| research-specialist | sonnet → Sonnet 5.5 | research | 整合分析 |
| writing-specialist | sonnet → Sonnet 5.5 | writing | 內容產出 |
| review-specialist | sonnet → Sonnet 5.5 | review | 品質判斷 |
| analysis-specialist | opus → Opus 5.5 | analysis | 規劃、推理、決策 → 強模型 |

- alias（haiku/sonnet/opus）會自動對映到當代各層級最新模型，無需追版本；上表「實際」欄僅供成本估算參考，以官方 alias 對映為準（[待驗證] 每次主版本升級時隨 NATIVE_OVERLAP 一併複核）。
- Claude 5 世代另有 Fable 5.1；本 harness 目前未分配子代理，需有實測成本／品質資料再評估是否納入分層。
- 路由判斷本身改由原生 skill description 自動觸發，不再需要獨立的「路由模型」。
- 校準資料（下方各 skill 實測平均）回填時，可據以調整對應子代理的分層（成本長期偏高 → 升一層模型）。

## 任務級預算（2026-04-15 依首次 RETRO 校正，基於 8 筆 audit log）

> **歷史數據**：每類僅 1–2 筆樣本，2026-04 後未再重算（20261031-P02 盤點）。僅供建卡時參考，不作為硬上限。

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
