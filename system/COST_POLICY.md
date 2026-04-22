# 成本控制策略 COST_POLICY

## 當前方案（v1，Opus 4.7 baseline 更新 2026-04-20）

v1 階段採用「粗略護欄 + 事後量測」策略：

- **硬上限**：透過 Anthropic API dashboard 的 spending limit 設定月度/日度上限
- **軟上限**：透過 CLAUDE.md 規則限制單一任務的工具呼叫次數與重試次數
- **事後追蹤**：每次任務完成後在 audit log 記錄預估 token 消耗

## Opus 4.7 觀測能力（2026-04-20 已知 / 待驗證）

D002 (2026-04-03) 假設「Claude Code CLI 不提供即時 token 計數 API」。
D005 覆寫此假設，改以「known unknowns」方式處理：

**已知**：
- Opus 4.7 context window 與先前世代同級（用於限制估算不需變更）
- CLAUDE.md 的 3K / 1.5K 硬限制仍有效

**待驗證（下次 retro 實測）**：
- Opus 4.7 在 Claude Code CLI 內是否提供 per-turn token 統計
- 若可用，是否能納入 hook，讓任務中途能觸發成本告警
- fallback 到 Sonnet 4.6 / Haiku 4.5 的自動判斷（目前僅手動）

**處置**：在確認觀測能力前，維持事後量測；MODEL_POLICY 的 fallback 仍為手動觸發。

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

## 模型路由規則（v2 — 2026-04-20 更新）

本區塊的模型選擇與 fallback 策略已提升為獨立檔案 `system/MODEL_POLICY.yaml`（D005）。
COST_POLICY 僅保留「節省 token 的做法」，模型路由細節不在此重複。

摘要（完整內容見 MODEL_POLICY.yaml）：
- 預設 Opus 4.7（分析 / 寫作）或 Sonnet 4.6（研究 / 審查 / 操作）
- Fallback chain：Opus 4.7 → Sonnet 4.6 → Haiku 4.5
- 降級時需在 audit log 的 `model_used` 欄位記錄實際模型與原因

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

## 升級觸發條件

當以下任一條件持續 2 週以上，考慮升級到 v2：

| 觸發條件 | 說明 |
|---------|------|
| Context 經常超限 | 單一代理的 context 頻繁需要壓縮，影響任務品質 |
| 規則衝突頻繁 | 不同任務類型間的規則互相干擾 |
| 單任務成本持續超標 | 任務級預算建議值被頻繁突破 |
| 錯誤率上升 | error log 中同類錯誤重複出現 |
