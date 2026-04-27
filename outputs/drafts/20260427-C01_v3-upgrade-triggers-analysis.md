# v3（多 Agent 架構）升級觸發條件分析

**Task Card**：20260427-C01
**日期**：2026-04-27
**Skill**：analysis

---

## 結論與建議

**建議：維持 v2，但建立量化升級判準（UPGRADE_TRIGGERS.yaml 草稿）。**

依現有數據（19 筆完成任務、context 使用率 40%、零規則衝突、5% 錯誤率），v3 升級的所有條件都還很遠。但 D003 留下的「revisit_trigger」描述為自然語言（"持續 2 週"），缺乏量化基準。本任務補上判準，確保未來決策不靠主觀判斷。

**結論一句話**：**現在不升級**；待任一**P1 觸發條件連續 14 天成立**，或**任二 P2 條件同時成立**，再開新 analysis Task Card 重新評估。

---

## 現狀盤點（用於閾值設定）

| 維度 | 當前數據 | 來源 |
|------|---------|------|
| Context 使用 | ~1,197 / 3,000 tokens（40%）| `scripts/check_context_budget.rb` |
| 任務累積 | 19 筆完成（含今日 5 筆）| `logs/AUDIT_LOG.md` |
| 規則衝突 | 0 次（19 筆任務中無觀察）| 未在 audit log 紀錄 |
| 錯誤率 | 1/19 = 5.3%（COORD-02 web search rate limit）| `logs/errors/` |
| 單筆 tool_calls | 最高 9（20260409-001）| AUDIT_LOG `tools_called` 加總 |
| 平均 token | ~17K | retro-2026-Q2-01 |
| 最大 token | ~25K（20260404-S01）| retro |
| 單 session 跨 skill | 已觀察：今日 1 session 跑 5 種 skill | 本 PR |

---

## 選項比較

### 選項 A：維持 v2（不升級）

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 高 | 19 筆任務跑通，context 40% 使用率，無瓶頸 |
| 成本 | 0 | |
| 風險 | 中（長期）| 若任務類型增加快速，未來可能緊急升級 |
| 可行性 | 高 | 不變動 |
| 執行難度 | 0 | |
| 預期回報 | 中 | 維持穩定即價值 |
| 一人公司適配 | 高 | 一人公司哲學：不過早優化；單代理已足 |

### 選項 B：立即升級到 v3（拆分 bounded specialists）

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 低 | 解決尚未發生的問題；當前無觸發訊號 |
| 成本 | 高 | 多 agent 協調機制、context 共享協議、agent-to-agent routing 規則皆需新建 |
| 風險 | 高 | 引入跨 agent 一致性、版本不對齊、debug 難度上升等新失敗模式 |
| 可行性 | 中 | 技術可行但設計複雜 |
| 執行難度 | 高 | 估計 2 週投入，但無明確收益 |
| 預期回報 | 低（短期）| 任務不會跑得更快；只在 context 真的塞不下時才有差 |
| 一人公司適配 | 低 | 違反「不做沒有實際需求的架構升級」（D003）|

### 選項 C：建立量化判準，現在不升級（**推薦**）

新增 `outputs/drafts/UPGRADE_TRIGGERS.yaml` 草稿；不寫入 `system/`。

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 高 | 解決「何時升級」的決策模糊；保留判斷空間 |
| 成本 | 低 | 一份 yaml 草稿；下次 retro 評估 |
| 風險 | 低 | 不改執行行為 |
| 可行性 | 高 | 用 19 筆數據可推估閾值 |
| 執行難度 | 低 | 約 1 小時 |
| 預期回報 | 中-高 | 一次設定，未來重檢有依據 |
| 一人公司適配 | 高 | 可量化 = 可審計 = 可信 |

### 選項 D：擴大 v2 邊界（先補 sub-skill 而非分 agent）

例如：在 `skills/research/` 下細分 `research-academic.md`、`research-market.md`，仍在單代理內。

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 中 | 解決部分「規則衝突」問題，不需多 agent |
| 成本 | 中 | 每個子技能需自己的 prompt（合計可能超出 1.5K 限制）|
| 風險 | 中 | 子技能膨脹後，路由判斷成本上升 |
| 可行性 | 高 | 純文件層擴充 |
| 執行難度 | 中 | |
| 預期回報 | 中 | 適合特定業務場景 |
| 一人公司適配 | 中 | 若某類任務頻繁可採；目前未觀察到 |

> 選項 D 留作未來「沒到 v3 但需要更專精」時的中途方案。本任務不採。

---

## 推薦的量化升級觸發條件

### P1（單條成立 14 天 → 啟動 v3 評估）

| ID | 條件 | 閾值 | 量測方式 | 依據 |
|----|------|------|---------|------|
| **T1** | Context 經常超限 | `check_context_budget.rb` 顯示 > 80% 使用率（≥ 2,400 / 3,000）| 連續 5 次 commit 觸發 | 留 20% 緩衝；當前 40% 距離還遠 |
| **T2** | 任務類型衝突 | 同 session 內 ≥ 3 種 skill_type 切換 + audit log notes 出現「規則衝突」標記 | 連續 3 次 retro 期內出現 | 今日已觀察 1 次（D01/A01/B01/B02/C01 五 skill），未出現衝突 |
| **T3** | 單 session tool_calls 超標 | 單 session 累積 tool_calls > 50 | AUDIT_LOG 加總 + check 腳本 | 當前單筆最大 9，session 加總約 20-40 |
| **T4** | 錯誤率上升 | error log 30 天內新增同類錯誤 ≥ 3 次 | `logs/errors/` 計數 | 30 天 1 次（COORD-02），有 3× 餘裕 |

### P2（任二同時成立 → 啟動 v3 評估）

| ID | 條件 | 閾值 | 量測方式 | 依據 |
|----|------|------|---------|------|
| **T5** | 任務量加速 | 月度任務數連續 2 個月 > 30 筆 | 月度 audit 計數 | 上月 8 筆 → 本月 16 筆（含今日），趨勢但未過閾值 |
| **T6** | 跨 skill 依賴增加 | 單一任務 input_data 引用 ≥ 3 個其他 task 的 output | YAML 解析 input_data | 當前最高 1 個 |

### Rollback 條件（升級 v3 後反而劣化）

| ID | 條件 | 閾值 | 動作 |
|----|------|------|------|
| **R1** | 任務完成時間 ↑ | v3 平均 wall-clock 比 v2 慢 > 30%（同 skill）| 退回 v2，記錄 D00X |
| **R2** | 跨 agent 同步錯誤 | agent-to-agent 一致性失敗 ≥ 2 次 | 退回 v2 + retro |
| **R3** | 操作複雜度爆炸 | 使用者單次互動需處理 > 3 個 agent 的中間狀態 | 退回 v2，重新評估設計 |
| **R4** | 成本反向上升 | 月度 token 消耗較 v2 高 50% 以上（無對應產出增加）| 退回 v2 |

---

## v2 vs v3 6 維度對照

| 維度 | v2（單代理）| v3（bounded specialists）| 結論 |
|------|------------|-------------------------|------|
| **價值** | 19 筆驗證可行；零事故 | 假設能拆分 → 但拆分本身無新功能 | v2 ≥ v3（短期）|
| **成本** | 已建設完成 | 新建 agent 路由、context 共享協議、版本管理 | v2 << v3 |
| **風險** | 已知失敗模式 14 種，全可處理 | 引入 agent 同步、跨 context 一致性等新失敗模式（估 +5–8 種）| v2 < v3 |
| **可行性** | 100%（已運作）| 需重新設計 | v2 > v3 |
| **執行難度** | 維護現狀 | 估 2 週設計 + 2 週遷移 | v2 << v3 |
| **預期回報** | 持續穩定 | 只在 context 滿載時才能展現 | 取決於是否觸發 |
| **一人公司適配** | 高（D003 已驗證）| 低（複雜度與 owner 數量不成比例）| v2 > v3 |

**綜合**：v3 在「context 滿載 + 規則衝突頻繁」時才有正回報。當前距離兩條件均遠（40% 使用率、0 衝突），不應升級。

---

## 高風險假設

- **「Context 40% 是穩定值」**：若未來 CLAUDE.md 或 GLOBAL_RULES 大幅擴充，使用率會快速攀升。
  → 緩解：T1 閾值設 80% 而非 100%，留出反應時間。

- **「規則衝突 = 自我察覺即可記錄」**：目前沒有強制記錄機制；衝突可能被默默吞掉。
  → 緩解：在 retro 維度加「本期是否觀察到 skill 規則衝突」必填欄位。本任務不執行此修改，僅建議。

- **「單 session 跨 skill = 衝突訊號」**：今日 1 session 跑 5 種 skill 並未出現衝突，反而順暢，可能 T2 過度敏感。
  → 緩解：T2 要求「同 session ≥ 3 skill **+ 規則衝突標記**」雙條件，避免假陽性。

- **「14 天連續成立」是合適觀察期**：若快速擴張，14 天可能太慢。
  → 緩解：P2 路徑（任二同時）提供快速通道。

---

## 待驗證

- 多 agent 架構在 Claude Code CLI 上的具體實作模式（subagent 機制？或 task chaining？）
- v3 之後 v4（Graph orchestration）的觸發是否需要不同判準
- T2 的「規則衝突」如何在 audit log notes 中標記（需額外 schema 設計）

---

## UPGRADE_TRIGGERS.yaml 草稿

下列為 **outputs/drafts/UPGRADE_TRIGGERS.yaml** 的內容草案。**不直接寫入 system/**。
若使用者採納，需另開 ops Task Card 經人工確認後寫入 `system/UPGRADE_TRIGGERS.yaml`。

```yaml
# UPGRADE_TRIGGERS.yaml — v2 → v3 升級判準
# 草稿位置：outputs/drafts/UPGRADE_TRIGGERS.yaml
# 來源：Task Card 20260427-C01 分析

current_version: "v2"
target_version: "v3"
last_evaluated: "2026-04-27"
last_decision: "hold (D003 + this analysis)"

# === P1 觸發條件（任一連續 14 天成立 → 啟動評估）===
p1_triggers:
  - id: "T1"
    name: "context_overflow"
    description: "CLAUDE.md + GLOBAL_RULES 加總 token 使用率 > 80%"
    threshold: "tokens_total > 2400"
    measurement: "scripts/check_context_budget.rb 連續 5 次 commit 觸發"
    current_value: "1197 / 3000 (40%)"

  - id: "T2"
    name: "skill_rule_conflict"
    description: "單 session ≥ 3 skill_type 切換 + audit log 出現規則衝突標記"
    threshold: "session_skill_types >= 3 AND conflict_flag = true"
    measurement: "audit log notes 欄位掃描"
    current_value: "0 conflicts in 19 tasks"

  - id: "T3"
    name: "tool_calls_per_session"
    description: "單 session 累積 tool_calls > 50"
    threshold: "session_tool_calls > 50"
    measurement: "AUDIT_LOG tools_called 加總"
    current_value: "max 9 per task"

  - id: "T4"
    name: "error_rate_rising"
    description: "30 天內同類錯誤 >= 3 次"
    threshold: "same_error_code_count >= 3 in 30d"
    measurement: "logs/errors/ 分類計數"
    current_value: "1 occurrence (COORD-02) in 30d"

# === P2 觸發條件（任二同時成立 → 啟動評估）===
p2_triggers:
  - id: "T5"
    name: "task_volume_acceleration"
    description: "月度完成任務 > 30 筆，連續 2 個月"
    threshold: "monthly_done >= 30 for 2 consecutive months"
    measurement: "audit log 月度計數"
    current_value: "Apr 2026: 16 (incl. today)"

  - id: "T6"
    name: "cross_skill_dependency"
    description: "單一任務 input_data 引用 >= 3 個其他 task 的 output"
    threshold: "max_cross_task_inputs >= 3"
    measurement: "tasks/*.yaml input_data 解析"
    current_value: "max 1"

# === Rollback 條件（升級後若劣化）===
rollback_triggers:
  - id: "R1"
    description: "v3 平均 wall-clock 比 v2 慢 > 30%（同 skill）"
    action: "git revert v3 commits + Decision Log 記錄"

  - id: "R2"
    description: "agent-to-agent 一致性失敗 >= 2 次"
    action: "退回 v2 + 立即 retro"

  - id: "R3"
    description: "使用者單次互動需處理 > 3 個 agent 的中間狀態"
    action: "退回 v2 + 重新評估設計"

  - id: "R4"
    description: "月度 token 消耗較 v2 高 50% 以上（無對應產出增加）"
    action: "退回 v2"

# === 重新評估時機 ===
revisit_schedule:
  - "每次 retro（依 RETRO_FLOW.md 觸發條件）必檢"
  - "任一 P1 條件成立後立即"
  - "任二 P2 條件同時成立後立即"
```

---

## 建議下一步

1. **本分析的草稿存放於 outputs/drafts/**：本檔案 + UPGRADE_TRIGGERS.yaml 草稿（嵌在本檔案中，可另切出獨立檔）
2. **不修改 system/**：依使用者指示
3. **下次 retro 必檢 P1 / P2 條件**：將「v3 觸發條件檢查」加入 retro 維度
4. **若 P1 任一條件成立**：開新 analysis Task Card 進入 v3 設計階段（不直接遷移）

### 不在本任務範圍

- 修改 `system/` 寫入 UPGRADE_TRIGGERS.yaml（屬 ops + 人工確認）
- 在 retro 維度新增「v3 條件檢查」欄位（屬 system 修改）
- 設計 v3 實作細節（屬另一階段任務）

---

## DoD 逐條確認

| # | 條件 | 狀態 | 說明 |
|---|------|:---:|------|
| 1 | 列出至少 4 個量化觸發條件，每條含閾值與量測方式 | ✅ | P1×4（T1-T4）+ P2×2（T5-T6）= 6 條，全量化 |
| 2 | 提出降級（rollback）條件，若升級後反而劣化如何回退 | ✅ | R1-R4 共 4 條，附 action |
| 3 | 對比 v2 vs v3 的成本/收益（用 6 維度矩陣，符合 analysis skill 格式）| ✅ | 「v2 vs v3 6 維度對照」段 |
| 4 | 明確結論：是否建議現在升級 / 等待哪些訊號 | ✅ | 結論段：「現在不升級」；等 P1 連續 14 天 / P2 任二同時 |
| 5 | 附 UPGRADE_TRIGGERS.yaml 草稿（放 outputs/drafts/，不直接寫入 system/）| ✅ | 本檔案內嵌完整 yaml 草稿；明標「不直接寫入 system/」|

**5/5 通過**。

---

*產出時間：2026-04-27*
*依據：D003 / system/AGENT_CONTEXT.yaml / system/COST_POLICY.md / README.md（v3 規劃段落）/ logs/AUDIT_LOG.md（19 筆）/ logs/errors/*
