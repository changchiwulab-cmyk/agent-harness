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

## 模型路由規則（v2 準備）

v1 先用單一模型（Claude）。未來如需降本：
- 分類、抽取、格式檢查 → 便宜模型（Haiku 等級）
- 規劃、推理、整合分析 → 強模型（Sonnet/Opus 等級）
- 路由判斷本身 → 便宜模型

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

## 下次校準操作 SOP

每次 retro 觸發時，依以下步驟更新校準係數，避免人工估算偏差：

### 1. 觸發條件（任一成立即執行）

- 自上次校準起累積 ≥ 5 筆新任務（不論 skill 類型）
- 任一 skill 類型新增 ≥ 3 筆實測（含未校準的 analysis）
- 單一任務 token 超出 skill 上限 ≥ 2 次（不需等 5 筆，立即重算該 skill）

### 2. 計算步驟

1. 從 `logs/AUDIT_LOG_<YYYY>-Q<n>.md` 抽取該 skill 自上次校準後的所有 `estimated_tokens`
2. 計算實測平均：`avg = sum(estimated_tokens) / count`
3. 計算新校準係數：`calibration_factor = avg / initial_estimate`
4. 計算建議上限：`limit = avg × 1.5`，向上取整至千位
5. 更新本檔「任務級預算」與「校準係數」兩張表
6. 在 `memory/active_projects/agent-harness/decisions/` 新增 D-XXX 紀錄理由

### 3. Analysis 樣本不足 fallback

當 analysis skill 累積樣本 < 3 筆時，不重算其係數：

- 維持原預估 12K + 上限 20K
- 在表格備註欄加註「樣本數 X，待 ≥ 3」
- 在下次 retro 報告中明確列出此狀態

### 4. 異常偏差處理

當新係數與舊係數差距 > 50%（例：1.5 → 2.5），不直接套用：

- 先檢查樣本是否含異常值（單筆超出平均 ×3）
- 若有，標記異常並暫不納入計算；於 retro 報告說明
- 若無異常但確實偏移，套用新係數並在 D-XXX 註明風險

### 5. 校準後驗證

- 套用新預算後，下一張 Task Card 的 `max_tool_calls` 與 `max_retries` 依新係數調整
- 連續 3 筆任務皆在新預算內 → 視為穩定
- 任一筆超出 → 立即啟動下一次校準（不等 5 筆）

## 升級觸發條件

當以下任一條件持續 2 週以上，考慮升級到 v2：

| 觸發條件 | 說明 |
|---------|------|
| Context 經常超限 | 單一代理的 context 頻繁需要壓縮，影響任務品質 |
| 規則衝突頻繁 | 不同任務類型間的規則互相干擾 |
| 單任務成本持續超標 | 任務級預算建議值被頻繁突破 |
| 錯誤率上升 | error log 中同類錯誤重複出現 |
