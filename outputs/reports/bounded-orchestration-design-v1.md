# 設計：有界編排（Bounded Orchestration）（正式版）

---

## 晉升標記

| 項目 | 內容 |
|------|------|
| **原始 draft** | `outputs/drafts/2026-06-14_bounded-orchestration-design.md` |
| **晉升日期** | 2026-06-15 |
| **晉升任務** | Task Card `20260615-001`（tasks/2026-06-15_promote-fable5-reports.yaml） |
| **審閱者** | 人工確認（使用者明示晉升） |
| **原始產出日期** | 2026-06-14（gap 報告 A1 後續） |
| **狀態** | 設計定案，**尚未實作**。實作前須先寫決策 D009 正式反轉 D003 與 ROUTING_RULES。 |

### 晉升理由
此為 A1（多代理/編排）落差的正式設計依據。內容已定案可作為未來實作 PR 的規格；
晉升不代表開始實作——反轉 D003（v3-hold）與「不做 agent-to-agent」明文規則屬架構級決策，須另經人工核可。

---

## 問題

目前 `ROUTING_RULES.md` 規定複合任務只能「拆多張 Task Card、依序執行、用 output 檔接力」，
且明文禁止 agent-to-agent。對照 Fable 5 + 原生子代理（可並行 fan-out、context 隔離省 ~67%），
這讓框架無法：並行執行獨立子任務、表達子任務依賴（DAG）、fan-in 彙整。

## 設計原則（為什麼叫「有界」）

不引入開放式自由對話的多代理，而是**受 Task Card 治理的編排**：每個子任務仍是一張獨立
Task Card，仍各自走 schema/rule/completion/risk 四層 gate、各自 checkpoint。編排層只負責
依賴排程與彙整，不繞過任何既有治理。

## 提案結構

### 1. 父卡（orchestration Task Card）
新增 `skill_type: orchestration`（或沿用既有 + 加 `subtasks:` 區塊），欄位：

```yaml
task_id: "YYYYMMDD-O01"
goal: "一句話描述整體目標"
skill_type: "orchestration"
subtasks:
  - id: "s1"
    card: "tasks/..._research.yaml"   # 各子任務仍是獨立 Task Card
    depends_on: []                     # DAG 邊；空 = 可立即啟動
  - id: "s2"
    card: "tasks/..._writing.yaml"
    depends_on: ["s1"]                 # s1 完成才啟動，吃 s1 的 output
fan_in:
  into: "outputs/drafts/..._final.md"  # 彙整點
```

### 2. 排程語意
- `depends_on` 為空的子任務 → 可**並行** fan-out（經原生 Agent tool 平行子代理）。
- 有依賴者 → 依 DAG 拓樸序；上游 output 檔作為下游 input（沿用現有接力機制）。
- 全部完成 → 父卡執行 fan-in 彙整 + 父卡層級的四層 gate。

### 3. 與原生 Agent tool 的對應
- 每個無依賴子任務 = 一次 `Agent`（子代理）呼叫，prompt 綁定該子任務 Task Card。
- 子代理回傳寫入該子任務的 output 檔；編排層只讀 output、不做自由對話。
- context 隔離由原生子代理提供（成本優勢）。

### 4. 治理（維持框架哲學）
- 每個子任務 Task Card 照常驗證（`run_gates.py` 已可逐卡跑）。
- 父卡新增 schema 檢查：`subtasks[].card` 路徑存在、DAG 無環、依賴指向存在的 id。
- 連續失敗 3 次規則：以子任務為單位計數；任一子任務達上限 → 暫停整個編排。
- 成本：父卡的 max_tool_calls 為各子卡加總上限的護欄。

### 5. 失敗處理
- 子任務失敗 → 該分支停、寫 error log；不影響無依賴的並行分支既有結果（已 checkpoint 保留）。
- 父卡標記 partial，彙整已完成分支，產出進 drafts/ 等人工。

## 需要的變更（若決定實作）
1. 新決策 D009：反轉 D003 + 改寫 ROUTING_RULES「不做 agent-to-agent」為「有界專家編排，須明確 Task Card」。
2. `tasks/TASK_CARD_TEMPLATE.yaml`：加 `subtasks` / `fan_in` 選填區塊。
3. `system/validate_task_card.py` + `scripts/run_gates.py`：父卡 schema（路徑存在、DAG 無環）。
4. 新 `scripts/validate_orchestration.py`（DAG 檢查）+ 測試。
5. `ROUTING_RULES.md` 複合任務段更新。

## 風險與待驗證
- **高風險假設**：原生子代理的成本/品質在本框架實際工作負載下是否真優於序列接力 → 待一輪實測。
- **待驗證**：DAG 編排的 checkpoint/恢復語意（RECOVERY_RUNBOOK 場景 C 尚未對多分支實測）。
- 反轉 D003 是架構級決策，須人工核可，不可由 agent 自行為之。

## 建議下一步
1. 由使用者裁示是否進入實作。
2. 若實作：先寫 D009，再做 §「需要的變更」1–5，分獨立 PR。
