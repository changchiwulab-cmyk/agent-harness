# Drafts 盤點審查 — outputs/drafts/

**Task Card**：20260427-D01
**日期**：2026-04-27
**Skill**：review
**目的**：盤點 outputs/drafts/ 6 份檔案，分類處置建議

---

## 總體評估

**有條件通過**。
6 份草稿中，**2 份已晉升但未從 drafts/ 撤除**（O02 已建立晉升標記但檔案仍在 drafts/），形成「同份內容兩處存在」的重複；其餘 4 份為**任務執行摘要**（per-task summary），本質上不適合 graduate，建議改變使用語意，視為「執行收據」而非「待審草稿」。

---

## 通過項

- 全部 6 份檔案皆有清楚的 task_id 或日期標記，可追溯來源
- 已晉升的 2 份（retro / token-calibration）皆在檔尾留有「已晉升」回指註記，引用鏈未斷
- drafts/ 命名一致使用 `YYYYMMDD-{task_id}_{slug}.md` 或語意檔名

---

## 6 份檔案分類

| # | 檔名 | 大小 | 類型 | 對應 task_id / decision | **建議分類** |
|---|------|-----:|------|-----------------------|-------------|
| 1 | `20260424-O01_cleanup-summary.md` | 1.7K | 任務執行摘要 | `20260424-O01` | **keep-as-draft（語意修正）** |
| 2 | `20260424-O02_restructure-summary.md` | 1.8K | 任務執行摘要 | `20260424-O02` | **keep-as-draft（語意修正）** |
| 3 | `20260424-O03_guardrails-summary.md` | 2.5K | 任務執行摘要 | `20260424-O03` | **keep-as-draft（語意修正）** |
| 4 | `analysis-create-task-card-permission.md` | 3.4K | 決策分析（已落為 D004） | `20260415-A01` / `D004` | **archive**（決策已採納） |
| 5 | `retro-2026-04-15.md` | 4.7K | retro 草稿（已晉升） | `20260417-O02` | **archive**（已有 reports 版） |
| 6 | `token-calibration-table-v1.md` | 3.6K | 校準表草稿（已晉升） | `20260424-O02` | **archive**（已有 reports 版） |

---

## 必須修改（依優先度）

### M1（高）：5 號、6 號 — 已晉升但仍佔 drafts/ 位置

- **位置**：`outputs/drafts/retro-2026-04-15.md`、`outputs/drafts/token-calibration-table-v1.md`
- **問題**：兩份皆已在 `outputs/reports/` 有完整對應版本，drafts/ 裡的副本透過檔尾註記指向 reports/ 版。但保留在 drafts/ 內會被誤讀為「待審」。
- **建議**：移至 `outputs/archived/drafts/`（建立此目錄）或 `outputs/drafts/archived/`，保留歷史可追溯但不再列在「進行中」視野。
- **理由**：drafts/ 應只存「真正待人工確認的內容」，已 graduate 的草稿應退場。

### M2（中）：4 號 — 決策分析已落地，留在 drafts 失去語意

- **位置**：`outputs/drafts/analysis-create-task-card-permission.md`
- **問題**：此分析已經由 D004（`20260415-D004_create-task-card-promoted-to-allow.yaml`）採納並寫入 `system/PERMISSIONS.yaml`。決策已生效，分析報告失去「待審」性質。
- **建議**：移至 `outputs/archived/drafts/` 或在檔頭加「已採納」標記（仿 retro 晉升標記），點出 D004 為落地依據。
- **理由**：與 5/6 號同樣的「已落地草稿」問題。

---

## 建議修改（中低優先）

### S1：1–3 號 — 任務執行摘要的語意定位

- **位置**：`20260424-O01/O02/O03_*-summary.md` 三份
- **問題**：這三份本質是「任務完成後的對照清單與驗證輸出」，不是待人工審閱的「草稿」。它們既不會 graduate（沒有 reports 版的需求），也不應 archive（仍是當期 reference）。
- **建議**：採方案 B（保留但語意正名），二選一：
  - **方案 A（簡單）**：保留現狀，但在 drafts/ 加 README 說明「per-task summary 屬於執行收據，不會 graduate」
  - **方案 B（清晰）**：建立 `outputs/task_summaries/` 資料夾，將 1–3 號移入；drafts/ 之後只放真正的「待審草稿」
- **本任務建議採方案 A**：避免一次動太多目錄結構；待第二份「執行收據」累積到 5 份以上，再評估是否分目錄。

### S2：drafts 盤點納入 retro 標準項目

- **位置**：`system/RETRO_FLOW.md`
- **建議**：在 retro 維度檢查清單中新增「drafts 盤點」一項（即本任務 D01 的工作）。觸發條件：drafts 內檔案 ≥ 5 份，或最舊檔案 > 30 天。
- **理由**：避免下次又靠人工巡檢才想到清理。可由本任務的觀察寫成第二個 PR（B02 的 retro 觸發條件可一併納入此提案）。

---

## Definition of Done 逐條確認

| # | 條件 | 狀態 | 說明 |
|---|------|:---:|------|
| 1 | 列出 outputs/drafts/ 全部 6 份檔案 | ✅ | 上表第 1 節已列 |
| 2 | 每份分類為 graduate / keep-as-draft / archive | ✅ | 「建議分類」欄；其中 graduate 為 0 份（已實際 graduate 過的不在此分類），archive 為 3 份，keep-as-draft 為 3 份 |
| 3 | 每筆分類附依據（task_id / decision_id） | ✅ | 「對應 task_id / decision」欄 |
| 4 | 建議是否將「drafts 盤點」納入 retro 標準項目 | ✅ | S2 條目，建議納入 |
| 5 | 不直接搬移檔案 | ✅ | 本檔僅產出建議，搬移動作另開 ops Task Card |

**5/5 通過**。

---

## 後續動作建議（不在本任務範圍）

| # | 動作 | 任務類型 | 建議 task_id |
|---|------|---------|-------------|
| 1 | 建立 `outputs/archived/drafts/` 目錄並搬移 4/5/6 號 | ops | 20260428-O01（待開） |
| 2 | RETRO_FLOW.md 新增「drafts 盤點」維度 | 視為 system 變更 → ops + 人工確認 | 20260428-O02（待開） |
| 3 | 評估方案 B（task_summaries 分目錄）| 待第 5 份執行摘要累積後再做 | — |

---

## 高風險假設

- **「已 graduate 的 drafts 應該 archive」**：若未來流程需要對比 drafts vs reports 兩個版本（例如審計），archive 路徑也需可訪問。建議保留在 `outputs/archived/`，不要刪除。
- **「per-task summary 不 graduate」**：本判斷基於目前 1–3 號的內容性質。若未來某份 summary 內容變得有對外引用價值，仍可走標準 graduate 流程。

---

*產出時間：2026-04-27*
*依據：outputs/drafts/ 全部 6 份檔案 + outputs/reports/ 對照 + memory/active_projects/agent-harness/decisions/*
