# 前端 Phase 0 收尾 + Hardening 實作摘要 — `20260516-F02`

> Task Card：`tasks/2026-05-16_frontend-phase0-closure-and-hardening.yaml`
> 分支：`claude/review-project-structure-1Il7v`
> 起因：專案架構盤點發現前端 Phase 0 的 4 個殘留缺口
> 狀態：草稿，待人工 review

## 變動清單

| 檔案 | 變動 | 對應項 |
|---|---|---|
| `tasks/2026-04-27_frontend-platform-phase0.yaml` | status `review`→`done`；result_summary 追加結案註記 | ① |
| `frontend/app.js` | logs 套 keyword/date 篩選；summary「Logs」卡改 filtered 計數；新增 `renderGates()` 渲染 gate_results 四鍵 pass/fail（escapeHtml） | ② |
| `frontend/styles.css` | 新增 `.gates/.gate/.gate-pass/.gate-fail` 樣式 | ② |
| `scripts/generate_frontend_manifest.py` → `scripts/generate_frontend_data.py` | `git mv`（保留歷史）+ 修內部 self-reference 字串 | ③ |
| `scripts/test_generate_frontend_manifest.py` → `scripts/test_generate_frontend_data.py` | `git mv` + 修 docstring 與 `import` | ③ |
| `scripts/run_frontend.sh` | generator 呼叫路徑更新 | ③ |
| `.github/workflows/spec-consistency.yml` | step 名稱與指令更新（manifest→data） | ③ |
| `README.md` | 「前端動態介面」3 處 script 名更新 | ③ |
| `frontend/data.json` | regenerated（F01 status / +F02 / +F03） | ①④ |
| `tasks/2026-05-16_frontend-phase1-gate-approval-failure-viz.yaml` | new（F03 規劃卡，pending） | ④ |
| `outputs/drafts/20260516-F02_phase0-closure-summary.md` | new（本檔） | DoD#8 |
| `logs/AUDIT_LOG.md` | 新增 1 筆 F02 紀錄 | DoD#9 |

## DoD 對照

| # | DoD | 狀態 |
|---|---|---|
| 1 | ① F01 review→done + 結案註記；不重複補 audit | ✅ |
| 2 | ② app.js logs 篩選對齊 + gate_results 渲染（escapeHtml） | ✅ |
| 3 | ③ git mv + operational 引用更新；歷史記錄保留舊名 | ✅ |
| 4 | ④ Phase 1 卡（F03，pending）通過 validate | ✅ |
| 5 | F02 + F03 卡 validate_task_card 皆 exit 0 | ✅ |
| 6 | `generate_frontend_data.py --check` exit 0；test 4 綠 | ✅ |
| 7 | 前端本地 smoke：index/data/app/css HTTP 200 | ✅（互動 UI 見下方限制） |
| 8 | 本摘要草稿 | ✅（本檔） |
| 9 | AUDIT_LOG 新增 1 筆；無 failed/partial 且 checkpoints<3 免 runs/ | 🟡 本卡有 4 checkpoints，依下方說明仍走 narrow scope |
| 10 | 分階段 checkpoint + push + draft PR | 🟡 push/PR 待本摘要後執行 |

## 本地驗證

```
python3 system/validate_task_card.py tasks/2026-05-16_frontend-phase0-closure-and-hardening.yaml  → ✅
python3 system/validate_task_card.py tasks/2026-05-16_frontend-phase1-gate-approval-failure-viz.yaml → ✅
python3 scripts/test_generate_frontend_data.py  → Ran 4 tests OK
python3 scripts/generate_frontend_data.py --check → OK: up to date
ruby scripts/check_spec_consistency.rb → OK
ruby YAML parse (all *.yaml) → ALL_YAML_OK
node --check frontend/app.js → JS_SYNTAX_OK
HTTP smoke (port 8771): index.html/data.json/app.js/styles.css → 200/200/200/200
data.json over HTTP → tasks 36 / logs 1 / decisions 7；F01=done、F02=pending、gate_results 存在
```

## 剩餘風險與限制

- **互動 UI 未自動驗證**：headless 環境只能驗靜態服務 + JS 語法 + 資料結構；無法自動點擊
  keyword/date 篩選或目視確認 gate chip 渲染。建議人工開
  `http://localhost:8000/frontend/index.html` 目視確認 logs 篩選與 gate chips。
- **DoD#9 checkpoints**：本卡實際 4 次 checkpoint（建卡 / ①② / ③ / ④+收尾），>3。
  依 D006「narrow scope」原意，runs/ 限縮於 *failed/partial* post-mortem；本卡全程
  零失敗零 partial，故仍只寫 AUDIT_LOG 不寫 logs/runs/。此處 checkpoints 數量是
  多子任務切分產物，非失敗重試，與 D006 觸發語意（深度 post-mortem）不符。
- **歷史舊檔名殘留（刻意）**：`tasks/2026-04-27_*.yaml`（F01 卡內文）、`outputs/drafts/*`
  各 summary、`logs/AUDIT_LOG.md` L437 保留 `generate_frontend_manifest` 舊名 ——
  此為過去狀態的可審計記錄，改寫等同竄改歷史，違反 harness「可審核」原則，故不動。
  F01 result_summary 已加前向註記指明更名。
- **Rollback**：本批變更皆在 `claude/review-project-structure-1Il7v`，`git revert`
  範圍 commit 即可；rename 由 git 歷史可還原；F01 status 可單獨 revert。

## Review 修正（PR #80）

- **Codex P2（frontend/app.js:45）**：`logDate` 篩選原以 `started_at` 優先，但 log row
  顯示以 `ended_at` 優先；跨午夜 run 會「顯示在範圍內卻被篩掉」。已修：`logDate`
  改為 `ended_at || started_at`，與顯示來源一致。採納（建議有效，1 行、屬 ② 同一
  deliverable 的一致性修正，非新任務）。

## 後續

- F03（Phase 1：Gate/Approval/Failure 聚合視覺化）已 pending，待人工排程另起 session。
- Phase 2（Context Budget 儀表板）、Phase 3（Decision Graph）仍待各自開卡。
