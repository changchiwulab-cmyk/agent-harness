# Task 20260427-B01 — Audit Log Integrity Report

## 執行結果

**DoD 5/5 通過。**
- 腳本與單元測試已建立並通過
- CI workflow 已加入新步驟
- 首次掃描發現 **3 筆歷史 audit log 缺漏**，已補登 4 筆（含今日 D01 與 A01）
- 補登後完整性檢查綠燈

---

## 變更清單

### 新增

| 檔案 | 內容 |
|------|------|
| `scripts/check_audit_completeness.rb` | 主腳本。掃描 status ∈ {done, failed, partial} 的 Task Card，比對 AUDIT_LOG.md 是否有對應條目。 |
| `scripts/test_check_audit_completeness.rb` | 16 runs / 28 assertions。涵蓋 DoD 三情境：齊全、漏記、task_id 格式不符。 |

### 修改

| 檔案 | 變更 |
|------|------|
| `.github/workflows/spec-consistency.yml` | 新增 "Audit log integrity check" step（先跑 test，再跑 check），與既有 context-budget 段落同層 |
| `logs/AUDIT_LOG.md` | 補登 4 筆條目（D01、A01、20260415-A01 歷史補登、20260409-001 歷史補登） |
| `tasks/2026-04-27_docs-completion-pack.yaml` | status: review → done（A01 已完成 + 已補 audit）|

---

## 首次掃描結果（19+ 張 Task Card）

### 補登前

```
Completed Task Cards (done/failed/partial): 12
AUDIT_LOG entries (unique task_id):         13
FAILED: 3 Task Card(s) missing from AUDIT_LOG:
  - 20260409-001 (status=done)  → 系統驗證任務
  - 20260415-A01 (status=done)  → permission 分析
  - 20260427-D01 (status=done)  → 今日 drafts 盤點
```

### 補登後

```
Completed Task Cards (done/failed/partial): 13
AUDIT_LOG entries (unique task_id):         17
OK: every completed Task Card has an AUDIT_LOG entry
```

> 說明：補登 4 筆條目（D01 + A01 + 兩筆歷史）後，audit 條目數 13 → 17；完成任務數 12 → 13（A01 從 review → done）。

---

## DoD 逐條驗證

| # | 條件 | 狀態 | 證據 |
|---|------|:---:|------|
| 1 | scripts/check_audit_completeness.rb 已建立 | ✅ | 81 行；含 collect_completed_task_ids / collect_audit_log_task_ids 兩個可測試函式 |
| 2 | 腳本能掃描所有 done/failed/partial Task Card，回報是否有對應 audit log 條目 | ✅ | 補登前掃出 3 筆缺漏；補登後綠燈 |
| 3 | scripts/test_check_audit_completeness.rb 單元測試覆蓋至少 3 種情境 | ✅ | 16 runs，含齊全（test_scenario_齊全_no_missing）/ 漏記（test_scenario_漏記_one_missing）/ format 不符（test_scenario_task_id_format_invalid_skipped）|
| 4 | .github/workflows/spec-consistency.yml 已加入此腳本的執行步驟 | ✅ | 新增 "Audit log integrity check" step，與 context-budget 段落同層 |
| 5 | 本次掃描現有 19 張 Task Card 的結果列入產出 | ✅ | 上節「首次掃描結果」 |

---

## 設計選擇

### 1. 反向缺漏不視為錯誤

腳本只檢查 **task → audit** 方向（任務完成但未記錄）。**audit → task**（log 有但 task 檔案沒有對應）僅為資訊，不視為錯誤。

理由：
- AUDIT_LOG 中可能存在已被重新整理 / 重命名的 task_id（如 `20260404-W01`、`20260404-S01`）
- 強制雙向一致會在歷史紀錄整理時製造 CI 噪音
- 真正要防的是「做了但忘了記」（task → audit 缺漏），這個方向已守住

### 2. 跳過 review / pending 狀態

`status: review` 表示「完成但等人工審閱」，理論上產出已存在，但因尚未確認，可能還會調整。
此時要求進 audit log 過於嚴格 — 等使用者明確 approve 後改 done 再記。

### 3. 跳過 examples/ 與 TEMPLATE

與 `check_spec_consistency.rb` 規則一致，避免範例任務造成假陽性。

---

## 影響範圍

- **新風險守住**：未來任何 Task Card 進 done 但忘了寫 audit log，CI 立即紅燈
- **歷史債清完**：3 筆缺漏中，2 筆是真正的歷史漏記，1 筆是今日的（順手補上）
- **CI 多 1 step，~3 秒成本**：可忽略

---

## 延伸觀察

- **A01 從 review 改 done 的時機**：本任務確認 A01 產出齊全且使用者已 inline_confirm（"執行1.ok 2.直接改 3.好"），故同步 done 並補 audit。未來其他任務同模式可參照。
- **20260415-A01 的 audit_log_ref 欄位空值**：原任務卡的 `audit_log_ref` 欄位為空字串，本次補登後可考慮回填。但此屬資料一致性整理，非 B01 範圍 — 留下次 retro 處理。
- **是否該延伸到 decision log 的反向檢查**：目前 decision log 沒有對應的「執行了 → 應有 decision」要求，故無需類似腳本。

---

## 後續建議（不在本任務範圍）

| # | 建議 | 任務類型 | 優先度 |
|---|------|---------|--------|
| 1 | 回填 20260415-A01 的 audit_log_ref 欄位（指向新補的 audit 條目）| ops | 低 |
| 2 | 考慮 audit log 條目 schema 化驗證（目前是寬鬆 markdown）| ops + system | 低，待累積到 50 筆再做 |
| 3 | 把「audit log 完整性檢查 OK」納入 retro 標準項目 | system | 中（與 D01 的「drafts 盤點」一同納入）|

---

*產出時間：2026-04-27*
*Task Card：20260427-B01*
*依據：tasks/**/*.yaml + logs/AUDIT_LOG.md + .github/workflows/spec-consistency.yml*
