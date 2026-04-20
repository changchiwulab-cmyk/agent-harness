# Weekly Review — 2026-04-08 ~ 2026-04-15

> 本週為首次執行 Weekly Review。驗證 RETRO_FLOW 與決策日誌串接是否可運作。
> 資料來源：`logs/AUDIT_LOG.md`、`logs/runs/`、`outputs/drafts/retro-2026-04-15.md`、`memory/active_projects/agent-harness/`、該週 Task Card YAML。
> 狀態：draft，待人工確認。

---

## 本週概況

- 期間：2026-04-08 ~ 2026-04-15（8 天）
- 執行任務數：**2**（經交叉比對 tasks/、logs/runs/、outputs/drafts/ 後）
- 完成：2 ／ 失敗：0 ／ 部分完成：0
- 另有 1 份系統性產出（首次 Retro 報告）未掛 Task Card

---

## 任務清單

| Task ID | Skill | 結果 | 備註 |
|---------|-------|------|------|
| 20260409-001 | review | done | v2 系統全流程驗證；DoD 7/7；發現並補正 FAILURE_TAXONOMY 漏 SEC-04 |
| 20260415-A01 | analysis | done | create_task_card 權限升級評估；首個 analysis skill 真實任務；已執行 PERMISSIONS + APPROVAL_POLICY 更新 |
| *(無 Task Card)* | review | done | `outputs/drafts/retro-2026-04-15.md` — 首次 Retro，依 RETRO_FLOW 觸發條件（累積 8 筆）執行 |

**週內決策日誌**：
- `20260415-D003_v3-upgrade-hold.yaml` — 不觸發 v3 升級
- `20260415-D004_create-task-card-promoted-to-allow.yaml` — 升為 allow

---

## 成本追蹤

- 本週 Anthropic dashboard 用量：**未提供**（本 review 無 web 查閱權限）
- 對照 audit log 任務數：**AUDIT_LOG 未補上本週 2 筆任務**（見下方問題 1）
- 平均每任務消耗趨勢：**無可靠資料**

> 2026-04-15 Retro 已上修各 skill token 預算建議（research 32K / writing 30K / ops 19K / review 23K）。
> 本週 20260409-001 的 execution log token_estimate 三欄皆 `0`，未實測回填。

---

## 問題與學習

### 問題 1 — AUDIT_LOG 是壞的 source of truth（**最大缺口**）
- `logs/AUDIT_LOG.md` 最後一筆是 `20260404-O02`，之後 3 筆任務（20260409-001、20260415-A01、Retro）全數未補上
- CLAUDE.md 執行流程第 9 步「寫 audit log」未被實際落實
- Retro 報告依賴 AUDIT_LOG 為資料來源，若 AUDIT_LOG 漏記 → 後續所有統計失真
- **具體行動**：產生 D005 決策草稿，建議將 AUDIT_LOG append 納入 GATE_POLICY completion_check 的驗證項

### 問題 2 — RETRO 觸發延遲
- RETRO_FLOW 規則：累積 5 筆觸發；實際在 8 筆才跑（延遲 3 筆）
- 沒有自動監控計數 → 仰賴使用者注意，注定會延遲

### 問題 3 — Execution Log token 欄位從未回填
- `logs/runs/20260409-001_system-validation.yaml` 的 token_estimate 三個欄位都是 0
- 這是 EXECUTION_LOG_SCHEMA 的結構性缺陷：沒人在閉幕時強制填

### 問題 4 — meta：本 Weekly Review 晚 5 天
- RETRO_FLOW 寫「每週一次，週五下班前」；04-15 是週三，理想週五 04-17 應做
- 實際 04-20（週一）才由 Task Card 20260420-003 補跑
- 意味著：Weekly Review 的 time-trigger 機制也失效

### 本週學到什麼（可寫入 memory/ 標記）
- 首次 Retro 真的跑起來了：RETRO_FLOW 不是死文件
- 決策日誌首度實際寫入（D003/D004）：治理層從紙面走到紀錄
- write_reports 與 risk_level 之間的矛盾是在 PR #33 review 過程才被 Codex 點出的（見 Task 20260420-002 的 inline 註解）

### 需要調整的規則
- **CLAUDE.md 第 9 步**「寫 audit log」語意模糊，應改為「**追加一筆到 `logs/AUDIT_LOG.md`**」且列為硬性驗證項
- **GATE_POLICY.yaml completion_check** 加一條 check：「AUDIT_LOG 內存在對應 task_id 的紀錄」
- **RETRO_FLOW + Weekly Review 的時機**：應有一個實際觸發機制（每次 Task Card 建立時檢查距離上次 retro 的任務數 / 日數）

---

## 下週計畫

### 待執行任務
- **20260420-001**（ops / medium）— 錯誤處理壓力測試
- **20260420-002**（review / medium）— draft → report 審核鏈驗證
- （視 D005 採納情形）補寫本週 3 筆漏記的 AUDIT_LOG 紀錄

### 系統調整項
| 調整 | 對象 | 優先度 |
|------|------|--------|
| 將 AUDIT_LOG append 納入 GATE_POLICY completion_check | system/GATE_POLICY.yaml | 高 |
| 補齊 AUDIT_LOG 漏記的 3 筆 | logs/AUDIT_LOG.md | 高 |
| CLAUDE.md 執行流程第 9 步用字精確化 | CLAUDE.md | 中 |
| Execution Log token 回填提醒 | system/EXECUTION_LOG_SCHEMA.yaml 註解 | 中 |
| Weekly Review 時機制度化 | system/RETRO_FLOW.md | 中 |

---

## 系統健康度 Checklist

- [x] COST_POLICY 的任務級預算是否需要更新？→ **是**，Retro 已給出建議值，待人工採納
- [x] 有重複出現的錯誤模式嗎？→ **有**：AUDIT_LOG 漏記是重複行為（本週 3 筆、歷史累積疑慮需查）
- [ ] 有需要新增或修改的 Skill 嗎？→ 否
- [x] memory/ 有過時內容需要清理嗎？→ **否**，但 `vietnam-expansion/` 仍是骨架，需評估是否移出 active_projects
- [x] GATE_POLICY 的驗證項是否需要調整？→ **是**，completion_check 增加 AUDIT_LOG 存在性檢查

---

## Meta-Review（本次 Weekly Review 自身的可改善點）

- **資料掃描成本偏高**：讀 6 個 input_data 用掉 8 個工具呼叫，撞到 Task Card 的 `max_tool_calls: 8` 上限；實際完成全流程共 ~13 次呼叫
  - 建議 review 類型任務預算至少 12，或將 Weekly Review 作為特例
- **模板欄位與實際需求不完全對齊**：WEEKLY_REVIEW_TEMPLATE 的「成本追蹤」預設有 Anthropic dashboard 用量，但 agent 無 web 權限取得
  - 建議模板註明「若 agent 無 dashboard 存取，填『未提供』」
- **Retro 與 Weekly Review 界線模糊**：兩者都回看執行、都產出建議清單。本週 Retro 已完成，Weekly Review 無法避免重複其內容
  - 建議：Retro = 事件觸發（按量），Weekly Review = 時間觸發（按週）；Weekly Review 應聚焦在「時間維度」特有觀察（時序、趨勢、跨任務依賴）而非重做 Retro 的分析

---

## Definition of Done 逐條確認

- [x] **#1 依 WEEKLY_REVIEW_TEMPLATE.md 填完所有欄位**：pass
- [x] **#2 盤點該週任務數、狀態分布、token 使用、失敗次數**：pass（token 使用註明未實測）
- [x] **#3 指出至少一項下週應調整的規則、skill 或流程**：pass（列出 5 項）
- [x] **#4 若產生新決策，建立 D005+ 決策日誌草稿**：pass（已產生 `20260420-D005_audit-log-discipline.yaml`）
- [x] **#5 紀錄本次 Weekly Review 自身的可改善點（meta-review）**：pass

---

*產出時間：2026-04-20*
*任務：20260420-003*
*狀態：草稿，待人工確認後納入規則調整或建立子任務*
