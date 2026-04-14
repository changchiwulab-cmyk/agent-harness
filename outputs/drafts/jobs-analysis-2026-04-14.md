# Agent Harness v2 — Jobs 視角完整度與優化診斷

**Task ID:** 20260414-A01  
**日期：** 2026-04-14  
**分析師：** Claude Sonnet 4.6（代入 Steve Jobs 標準）  
**對象：** Agent Harness v2.0（一人公司 AI Agent 執行框架）

---

## 診斷框架

> "Simple can be harder than complex. You have to work hard to get your thinking clean to make it simple."  
> — Steve Jobs

Jobs 管理哲學的核心不是「做得多」，而是「做得對、做得精、真正出貨」。  
以下用他最重視的 8 個標準，逐項評審 Agent Harness v2。

---

## 評分總覽

| 標準 | 評分 | 一句話診斷 |
|------|------|-----------|
| 1. Simplicity | ❌ 不及格 | 複雜偽裝成完整 |
| 2. Focus | ⚠️ 部分及格 | 方向正確，但邊界模糊 |
| 3. Customer Experience First | ❌ 不及格 | 沒有入口，只有迷宮 |
| 4. Insanely Great Quality | ⚠️ 部分及格 | 骨架精良，收尾殘破 |
| 5. Vertical Integration | ⚠️ 部分及格 | 有流水線，但有斷點 |
| 6. Real Artists Ship | ❌ 不及格（最嚴重） | Approval Pipeline 是紙上建築 |
| 7. Say No | ⚠️ 輕微問題 | 有死碼，政策無執行力 |
| 8. A-Player Standard | ⚠️ 部分及格 | 程式碼品質高，但有 regression bug |

**綜合評分：60 / 100**

---

## 1. Simplicity — ❌ 不及格

### Jobs 標準
> "iPhone 開箱，3 步驟就能打電話。"

### 現況
使用者要完成一個新任務，需要理解：
- `CLAUDE.md`（9 個段落，5 個規則層）
- `system/`（12 個治理檔案）
- `skills/`（5 個技能目錄）
- `tasks/`（TASK_CARD_TEMPLATE + examples/）
- `logs/`（4 個子目錄）
- `outputs/`（2 個子目錄）

**這是「複雜偽裝成完整」。** 文件越多，不代表系統越好。Jobs 會問：「如果你要把這個給你媽媽用，她看完 CLAUDE.md 知道下一步嗎？」

### 具體問題
- `CLAUDE.md` 有 9 個段落、多層規則，閱讀時間約 8-10 分鐘
- 執行流程 9 個步驟（載入 → 確認 → 載入 context → 執行 → commit → 驗證 → 輸出 → 寫紀錄 → 寫 audit）— 正確但過於詳細，應藏在系統內部
- 新使用者不知道從哪裡開始：README 有架構圖，但沒有「第一步」

### 優化行動
- **建立 `QUICKSTART.md`**（1 頁，3 步驟）：「有任務 → 複製 Task Card → 告訴 Claude 執行」
- **`CLAUDE.md` 瘦身**：只保留 3 條硬規則 + 快速入口連結，其餘細節留在 system/
- **System/ 整合**：12 個檔案合併為最多 5 個（核心規則 / 流程 / 權限 / 品質標準 / Schema）

---

## 2. Focus — ⚠️ 部分及格

### Jobs 標準
> "Focus means saying no to the hundred other good ideas."

### 優點
明確聲明「職責不是展現最強能力，而是穩定完成任務」— 這是 Jobs 式聚焦。

### 問題

**邊界模糊：`analysis/` vs `review/`**  
- `skills/analysis/SKILL.md` 定義：決策支援、策略分析、六維評估框架  
- `skills/review/SKILL.md` 定義：品質審查、邏輯查核、風險評估  
- 問題：一個市場進入決策，應該用 `analysis` 還是 `review`？兩者均有道理。邊界不清會導致路由猶豫。

**FAILURE_TAXONOMY 有 14 個分類**  
- 分類粒度過細（spec/coordination/validation/security 共 14 項）
- Jobs 會問：「這 14 個你真的都用到了嗎？還是因為怕漏掉才列這麼多？」

**ROUTING_RULES.md 與 INTAKE_FLOW.md 功能重疊**  
- 兩者都在回答「接到任務後，第一步做什麼」
- 使用者需要讀兩個檔案才能理解完整流程

### 優化行動
- **明確劃清 analysis vs review**：analysis = 「幫我做決定」；review = 「幫我查對錯」
- **FAILURE_TAXONOMY 縮減到 5 大類**：Spec / Context / Validation / Permission / External
- **合併 ROUTING_RULES.md 進 INTAKE_FLOW.md**，刪掉一個檔案

---

## 3. Customer Experience First — ❌ 不及格

### Jobs 標準
> "You've got to start with the customer experience and work backwards to the technology."

### 現況
**使用者是誰？就是你自己（一人公司）。**  
第一次打開這個框架，你的體驗是什麼？

1. 打開 README — 看到漂亮的架構圖，但不知道下一步
2. 打開 CLAUDE.md — 看到規則，但不知道如何開始一個任務
3. 找到 tasks/ — 看到 TASK_CARD_TEMPLATE.yaml，但不知道填完後要做什麼
4. 找到 tasks/examples/ — 這才是正確入口，但沒有任何地方指向這裡

**這是一個沒有入口的迷宮。** 你必須先理解整個系統，才能使用它。這與 Jobs 的原則完全相反。

### 優化行動
- **建立 `HOW_TO_START.md`**：
  ```
  有新任務？3 步驟：
  1. 複製 tasks/TASK_CARD_TEMPLATE.yaml
  2. 填寫 goal + definition_of_done + skill_type
  3. 告訴 Claude：「請執行 tasks/你的任務.yaml」
  
  範例：tasks/examples/ 目錄有 4 個真實案例
  ```
- **CLAUDE.md 最頂部加「快速入口」區塊**（3 行內完成）

---

## 4. Insanely Great Quality — ⚠️ 部分及格

### Jobs 標準
> "Details matter. It's worth waiting to get it right."

### 優點
- `scripts/check_spec_consistency.rb`：完整、邊界處理周全、中文錯誤訊息清晰 — A 級品質
- `skills/*/eval_examples.md`：明確的好壞對比範例 — 這是 Jobs 要的「demo quality」

### 問題

**7 個任務沒有 execution log**  
`logs/runs/` 只有 1 個執行日誌（20260409-001），8 個任務中的 7 個沒有對應記錄。  
AUDIT_LOG.md 有記錄，但 execution log 缺失代表「細粒度追蹤」完全沒有運作。

**Execution log 本身是殘破的**  
`logs/runs/20260409-001_system-validation.yaml` 有 3 個 checkpoint 標記為 `"pending"` 而非真實 commit hash。  
一個「完成」的任務，留下未完成的記錄，這不是 Jobs 標準。

**`logs/approvals/` 完全空白**  
審批流程有設計、有政策（APPROVAL_POLICY.yaml），但從未執行。

**`skills/analysis/` 缺少 eval_examples.md**  
4 個 skill 都有 eval_examples.md，v2 新增的 `analysis/` 沒有 — 這是殘缺的交付。

### 優化行動
- `check_spec_consistency.rb` 加入規則：status=done 的任務不能有 `"pending"` checkpoint
- 補齊 `skills/analysis/eval_examples.md`
- 補齊 7 個缺失任務的 execution log（或接受 AUDIT_LOG.md 為唯一記錄並刪除 runs/ schema）

---

## 5. Vertical Integration — ⚠️ 部分及格

### Jobs 標準
> "The whole widget. We own the whole thing."

### 優點
- GATE_POLICY → APPROVAL_POLICY → EXECUTION_LOG → AUDIT_LOG 有明確流水線
- CI/CD 驗證 Task Card schema — 垂直整合的好例子，確保品質從 push 時就開始

### 問題

**`memory/` 和 `logs/` 完全平行，沒有交叉引用**  
- 決策記錄在 `memory/active_projects/*/decisions/`
- 執行記錄在 `logs/runs/`
- 這兩者描述的是同一件事的不同面向，但彼此沒有引用。3 個月後你要查一個決策，需要同時找兩個地方。

**Retro 建議採納了，但沒有更新對應系統檔案**  
Retro 報告說「採納 5 條建議」，但 git history 顯示 COST_POLICY.md 的 token 數字更新了，其他系統檔案沒有對應修改記錄。這是「人工採納」而非「系統採納」— 下一次 Retro 後相同的斷層會再次發生。

**兩個驗證系統各自為政**  
- `scripts/check_task_card_skill_type.py`：CI 用，只驗 skill_type
- `system/validate_task_card.py`：手動用，驗全欄位  
但這兩個的 skill_type 白名單不同步（CI 缺 `analysis`），這已造成 regression bug（已修復）。

### 優化行動
- AUDIT_LOG 每筆記錄加入 `memory_ref:` 欄位，指向相關記憶或決策檔案
- Retro 輸出格式中加入「需修改的系統檔案清單（帶路徑）」，讓採納可追蹤
- 合併兩個驗證器邏輯，或讓 CI 直接調用 `system/validate_task_card.py`

---

## 6. Real Artists Ship — ❌ 不及格（最嚴重問題）

### Jobs 標準
> "Real artists ship."（不是 Real artists write drafts.）

### 現況

| 目錄 | 狀態 | 說明 |
|------|------|------|
| `outputs/drafts/` | 有內容 | 2 個草稿：retro + Elon Musk 分析 |
| `outputs/reports/` | **完全空白** | 從未有任何輸出「畢業」 |
| `logs/approvals/` | **完全空白** | 審批流程設計精美，從未執行 |

**這代表什麼？**  
整個 Approval Pipeline 是紙上建築。Approval Policy 寫了 3 頁，列了觸發條件、審批方法、升格流程。但從 Day 1 到今天（Day 10），沒有任何一個輸出走完這個流程。

所有輸出永遠停在草稿狀態。「草稿」的本質是「未完成」。這個框架交付了 8 個任務，但沒有一個真正完成。

這是 Jobs 最不能接受的：**一個從不出貨的工廠。**

### 優化行動（P0 優先）
- **立刻執行一次完整 Approval 流程**：選一個現有草稿，走完 draft → approval record → reports/
- **建立 `logs/approvals/TEMPLATE.yaml`**，讓審批記錄有標準格式
- **在 AUDIT_LOG 加入 `output_status: draft | approved`** 欄位，讓「出貨」狀態可追蹤

---

## 7. Say No — ⚠️ 輕微問題

### Jobs 標準
> "I'm as proud of many of the things we haven't done as the things we have done."

### 問題

**COST_POLICY 無執行力**  
`system/COST_POLICY.md` 定義了各 skill 的 token 預算，但 Week 1 數據顯示：
- Writing：預估 ~10K，實際 ~20K（+100%）
- Research：預估 ~15K，實際 ~22K（+47%）

這個政策從未阻止任何任務繼續執行。一個沒有觸發行為的預算，不是預算，是裝飾。

**`system/OPERATING_CONTEXT.yaml` 可能是死碼**  
描述系統自身 metadata（名稱、版本、執行環境），但在 CLAUDE.md 和 system/ 其他檔案中沒有任何地方引用它。如果沒有被讀取，它的存在只是增加複雜度。

### 優化行動
- COST_POLICY 加入「超支觸發行為」：任務 token 超過 1.5x 預估時，自動 checkpoint + 詢問使用者是否繼續
- 確認 OPERATING_CONTEXT.yaml 是否被引用；若沒有，刪除或整合進 AGENT_CONTEXT.yaml

---

## 8. A-Player Standard — ⚠️ 部分及格

### Jobs 標準
> "A players hire A players. B players hire C players."

### 優點
- `scripts/check_spec_consistency.rb`（161 行）：結構清晰、正確的 nil 處理、CI 整合 — A 級
- `system/validate_task_card.py`（83 行）：單一職責、清晰的錯誤訊息 — A 級
- `skills/*/eval_examples.md`：好壞對比範例完整 — A 級

### 問題

**Regression Bug（已修復）**  
`scripts/check_task_card_skill_type.py` 的 skill_type 白名單是 `{research, writing, ops, review}`，但 v2 新增了 `skills/analysis/`，白名單沒有同步更新。這意味著任何使用 `skill_type: analysis` 的 Task Card 在 CI 中會失敗。

**已修復：** 白名單現已加入 `"analysis"`。

**`TASK_CARD_TEMPLATE.yaml` 注釋也已更新：**  
`# research / writing / ops / review / analysis`

**驗證邏輯重複**  
`check_task_card_skill_type.py` 和 `validate_task_card.py` 都在驗 skill_type，但前者跑在 CI、後者只能手動調用。兩個獨立維護的白名單是 regression 的根源。

### 優化行動
- 讓 CI workflow 直接調用 `system/validate_task_card.py`，廢棄 `check_task_card_skill_type.py`（DRY）
- 或在 `validate_task_card.py` 中用常數定義白名單，讓 `check_task_card_skill_type.py` import 這個常數

---

## 優先行動清單

### P0 — 立刻修（今天）
| # | 行動 | 目標 | 狀態 |
|---|------|------|------|
| 1 | 修復 skill_type 白名單 regression bug | `scripts/check_task_card_skill_type.py` | ✅ 已完成 |
| 2 | 更新 TASK_CARD_TEMPLATE 注釋 | `tasks/TASK_CARD_TEMPLATE.yaml` | ✅ 已完成 |
| 3 | 執行一次完整 Approval 流程 | `outputs/reports/` + `logs/approvals/` | ⬜ 待執行 |

### P1 — 本週修（框架完整性）
| # | 行動 | 目標 |
|---|------|------|
| 4 | 補齊 `skills/analysis/eval_examples.md` | 讓 analysis skill 交付完整 |
| 5 | 修復 20260409-001 的 pending checkpoints | 用真實 commit hash 填入 |
| 6 | `check_spec_consistency.rb` 加新規則 | done 任務不能有 pending checkpoint |
| 7 | 補齊或整合 7 個缺失的 execution logs | 決定 runs/ 是否為必要層 |

### P2 — 下週修（體驗優化）
| # | 行動 | 目標 |
|---|------|------|
| 8 | 建立 `QUICKSTART.md` | 1 頁，3 步驟，新使用者入口 |
| 9 | CLAUDE.md 瘦身 | 只保留 3 條硬規則 + 快速入口 |
| 10 | 確認並整合或刪除 OPERATING_CONTEXT.yaml | 消除死碼 |
| 11 | 明確劃清 analysis vs review 邊界 | 更新 ROUTING_RULES 或 INTAKE_FLOW |

### P3 — 下次 Retro 前（深度優化）
| # | 行動 | 目標 |
|---|------|------|
| 12 | COST_POLICY 加入超支觸發行為 | 讓預算有執行力 |
| 13 | Retro 輸出加入「需修改系統檔案清單」 | 讓採納可追蹤、可驗證 |
| 14 | AUDIT_LOG 加入 output_status 欄位 | 追蹤「出貨」狀態 |
| 15 | 合併或廢棄重複驗證邏輯 | DRY 原則，消除 regression 根源 |

---

## Jobs 式總評

> 這個框架是一部精心設計但從未真正出貨的產品。

文件完美，流程優雅，Ruby 腳本品質一流。**但：**

- Approval Pipeline 是空的
- Reports 目錄是空的  
- 7 個任務沒有 execution log
- Validation 邏輯是重複的，導致 regression bug

設計的複雜度（12 個 system/ 檔案、2 個驗證器、2 個日誌系統）已經超過了它解決問題的複雜度。

Jobs 會說：**「砍掉 30% 的文件，逼自己跑完一次完整 Approval 流程，這個系統就會從 60 分跳到 90 分。」**

**不是要你做更多。是要你把已經設計的，真正跑起來。**

---

*生成日期：2026-04-14 | Task ID：20260414-A01 | Status：Draft - Pending Human Approval*
