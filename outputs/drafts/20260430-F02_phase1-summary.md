# Phase 1 前端平台實作摘要 — 20260430-F02

- **Task Card**: `tasks/2026-04-30_frontend-platform-phase1.yaml`
- **Branch**: `claude/build-web-app-S1xzJ`
- **Risk**: medium · approval_needed: true · skill_type: ops

## 變動檔案

| 檔案 | 動作 | 說明 |
|---|---|---|
| `frontend/lib.js` | 新增 | 純函式 helpers（escapeHtml / decisionDate / inDateRange / filterTasks / filterDecisions / aggregateTasks / gateState / uniqueValues） |
| `frontend/lib.test.mjs` | 新增 | node:test 單元測試，8 個 case |
| `frontend/app.js` | 改寫 | 引用 `lib.js`；新增 facets / pipelines / gate matrix / decision link 互動；統一 loading/error/empty 三態 |
| `frontend/index.html` | 改寫 | filter 多 4 個 select；新增 `pipeline` section（status / risk）；aria-live 提示 |
| `frontend/styles.css` | 改寫 | 新增 chip / gate / bar / pipeline / kv 樣式；色彩變數放 `:root` |
| `frontend/data.json` | 重生成 | 因新增 task card 觸發 generator；資料 schema 不變（17 tasks / 1 logs / 6 decisions） |
| `tasks/2026-04-30_frontend-platform-phase1.yaml` | 新增 | 本任務的 Task Card |

未動：`scripts/generate_frontend_manifest.py`、`scripts/run_frontend.sh`、`scripts/test_generate_frontend_manifest.py`、`.github/workflows/`、generator 的資料 schema。

## 測試結果

- `node --test frontend/lib.test.mjs` → 8/8 pass（escapeHtml / decisionDate / inDateRange / filterTasks / filterDecisions / aggregateTasks / gateState / uniqueValues）
- `python3 -m unittest scripts/test_generate_frontend_manifest.py` → 4/4 pass（既有測試未受影響）
- `python3 scripts/generate_frontend_manifest.py --check` → OK（無 drift）
- 本機 `python3 -m http.server` smoke：`/frontend/index.html`、`app.js`、`lib.js`、`data.json` 全部 200

## DoD 對應

| # | DoD | 狀態 |
|---|---|---|
| 1 | logs 卡片呈現 gate_results 四燈號 + N/A fallback | ✅ `renderGateMatrix` + `gateState` |
| 2 | filters 新增 status / skill_type / risk_level / approval_needed 四 facet | ✅ `<select>` × 4，`filterTasks` AND 組合 |
| 3 | summary cards 增加 by-status pipeline / by-risk | ✅ `renderPipelines` 兩個橫條圖 |
| 4 | decision card 內 related_task 可點擊回過濾 task | ✅ `.related-task` button → 套 keyword + scrollIntoView |
| 5 | decision card 補 revisit_trigger | ✅ kv 區塊呈現 |
| 6 | loading / error / empty 三態統一 | ✅ `setLoading` / `showError` / 各 panel 空集合提示 |
| 7 | 拆 lib.js + node:test 至少 8 case | ✅ 8/8 |
| 8 | run_frontend.sh CLI 不變、generator 不動、data.json schema 不動 | ✅ 完全沒動 |
| 9 | generator --check pass | ✅ |
| 10 | node test 全綠 + 既有 python test 全綠 | ✅ |
| 11 | outputs/drafts 摘要 | ✅ 本檔 |
| 12 | AUDIT_LOG 加 1 筆 | ✅（同 commit） |

## 後端訊號利用度（before → after）

| 訊號 | Phase 0 | Phase 1 |
|---|---|---|
| `tasks[].task_id/goal/status/skill_type/date` | ✅ | ✅ |
| `tasks[].risk_level` | ❌ | ✅（chip + pipeline） |
| `tasks[].approval_needed` | ❌ | ✅（chip + facet） |
| `logs[].run_id/task_id/status/started_at/ended_at` | ✅ | ✅ |
| `logs[].gate_results.{schema/rule/completion/risk}` | ❌ | ✅（四燈號 + N/A fallback） |
| `decisions[].decision_id/decision/reasoning/_date` | ✅ | ✅ |
| `decisions[].related_task` | ❌ | ✅（可點擊回過濾） |
| `decisions[].revisit_trigger` | ❌ | ✅（kv 呈現） |

## 剩餘風險

1. **單一 log 樣本**：目前 `logs/runs/` 只有 1 筆 RUN-20260409-001 且四燈全 pass，UI 對 fail / N/A 的呈現只在單元測試中驗證；待未來真實 fail/partial run 出現時再人工複驗一次外觀。
2. **無視覺回歸測試**：CSS/HTML 沒有 snapshot 測試，後續若改樣式需手動 smoke。Phase 2/3 若繼續疊加可考慮引入 Playwright，但本 phase 不引入新 dep。
3. **i18n 未抽出**：UI 文字硬寫繁中（與 Phase 0 一致），多語言屬未來範圍。
4. **client-only**：所有過濾在前端做。資料量級若 > 數千筆需要分頁/虛擬滾動，目前 17 筆遠未達閾值。

## 後續

- Phase 2（Context Budget 儀表板）：需要 generator 把 `scripts/check_context_budget.rb` 的輸出帶進 data.json，是 schema 異動，建議另開 task card。
- Phase 3（Decision Graph）：純前端，可在不動 generator 的前提下做，但會引入 SVG 渲染，視需求再評估。

## Gate 自驗

- schema_check: pass（task card 通過 `validate_task_card.py`）
- rule_check: pass（僅用 task card allowed_tools 內工具，2 次 checkpoint）
- completion_check: pass（DoD 12/12）
- risk_check: pass（risk=medium，輸出在 `outputs/drafts/`，未直接寫入 reports/）
