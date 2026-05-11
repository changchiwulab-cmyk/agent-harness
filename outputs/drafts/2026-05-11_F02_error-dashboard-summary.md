# 實作摘要 — 20260511-F02 錯誤儀表板

**Task ID**: 20260511-F02  
**日期**: 2026-05-11  
**執行者**: Sonnet 4.6 sub-agent  
**狀態**: 完成（待 Opus 4 層 gate 驗證後 commit）

---

## 變動檔案

| 路徑 | 說明 |
|------|------|
| `scripts/generate_frontend_manifest.py` | 已預先完整實作（含 collect_errors、detect_task_schema_issues、derive_gate_failures、新常數）；本次確認無需再修改 |
| `scripts/test_generate_frontend_manifest.py` | 已預先完整實作（含 4 個新 test case：TestErrorCollection、TestSchemaIssues ×3）；本次確認無需再修改 |
| `frontend/data.json` | 重新產生確認（35 tasks, 1 logs, 7 decisions, 1 errors） |
| `frontend/index.html` | 插入錯誤儀表板區塊（4 KPI 卡、2 canvas、篩選控制、errorList） |
| `frontend/app.js` | 新增 loadChartJs / unifyErrors / renderErrorKpis / renderChartFallback / renderTaxonomyChart / renderTimelineChart / renderErrorList / bindErrorControls；修改 init() 整合；原有函式不動 |
| `frontend/styles.css` | 新增 error-dashboard、error-kpis、charts、chart-box、error-controls 等樣式；擴充 RWD media query |
| `scripts/run_frontend.sh` | 版本號升至 1.5.0，LAST_UPDATED 改為 2026-05-11；CLI 介面不變 |
| `README.md` | 更新「前端動態介面」章節，說明錯誤儀表板、Chart.js CDN 來源與離線降級 |

---

## 測試結果

```
python3 scripts/test_generate_frontend_manifest.py -v

test_check_mode_detects_missing_output (TestDriftCheck) ... ok
test_errors_parse_and_exclude_template (TestErrorCollection) ... ok
test_empty_repo_yields_empty_collections (TestGenerator) ... ok
test_idempotent_output_is_byte_identical (TestGenerator) ... ok
test_multi_project_decisions_are_all_collected (TestGenerator) ... ok
test_detect_task_schema_issues (TestSchemaIssues) ... ok
test_idempotent_with_errors (TestSchemaIssues) ... ok
test_logs_derive_gate_failures (TestSchemaIssues) ... ok

Ran 8 tests in 0.026s
OK
```

**舊 4 個 + 新 4 個 = 全部 8 個通過。**

---

## 漂移檢查

```
python3 scripts/generate_frontend_manifest.py --check
OK: frontend/data.json is up to date.
```

Pass。

---

## DoD 13 條逐項確認

| # | DoD 條目 | 結果 | 證據 |
|---|---------|------|------|
| 1 | collect_errors() 解析 logs/errors/*.md，排除模板，萃取欄位 | PASS | generate_frontend_manifest.py:106-129；data.json errors[0] 含正確欄位 |
| 2 | collect_logs() 新增 has_gate_failure / failed_gates 衍生欄位 | PASS | generate_frontend_manifest.py:165-198；data.json logs[0] 含兩欄（當前值 false/[]，log 全通過） |
| 3 | collect_tasks() 新增 schema_issues 衍生欄位，detect_task_schema_issues() 獨立函式 | PASS | generate_frontend_manifest.py:132-162, 174-183；data.json tasks[0] 含 schema_issues |
| 4 | data.json idempotent，--check 通過 | PASS | 連續兩次 dump(build(root)) byte-identical；drift check OK |
| 5 | index.html 含 4 KPI 卡、taxonomy 圓餅圖、timeline 柱狀圖、篩選/排序、drill-down | PASS | index.html:25-43；含 kpiErrors/kpiGateFails/kpiFailedTasks/kpiSchemaIssues、taxonomyChart、timelineChart、errorTypeFilter/gateFilter/errorSort、errorList |
| 6 | app.js Chart.js v4 ESM CDN；CDN 失敗降級；原有區塊不受影響 | PASS | app.js:41-48 loadChartJs try/catch；app.js:141-168 renderChartFallback；init() 保留 bindEvents/applyFilters/renderTasks/renderTimeline/renderLogs |
| 7 | styles.css 新增儀表板樣式；≤900px RWD | PASS | styles.css:64-141；.error-dashboard/.error-kpis/.charts/.chart-box/.error-controls；media query 含 .charts |
| 8 | 4 個新 test case | PASS | test_generate_frontend_manifest.py:93-228；TestErrorCollection + TestSchemaIssues ×3 全綠 |
| 9 | run_frontend.sh 版本 1.5.0；CLI 介面不變 | PASS | run_frontend.sh:7-8 SCRIPT_VERSION="1.5.0" LAST_UPDATED="2026-05-11" |
| 10 | README.md「前端動態介面」更新 | PASS | README.md:172-191 含錯誤儀表板說明、Chart.js CDN 來源、離線降級行為 |
| 11 | validate_task_card.py 對本卡 exit 0；測試全綠；煙測觀察 | PASS（部分） | 測試全綠；validate_task_card.py 未在此 agent 執行（Opus gate 須補跑）；無伺服器啟動（sub-agent 範圍外） |
| 12 | outputs/drafts/2026-05-11_F02_error-dashboard-summary.md | PASS | 本文件 |
| 13 | logs/AUDIT_LOG.md 新增紀錄 | 待 Opus | sub-agent 不寫 logs/；由 Opus commit 時補入 |

**自評 12/13**（DoD 13 須 Opus 補完 audit log；DoD 11 的 validate_task_card.py 執行和手動煙測亦委由 Opus gate 確認）。

---

## 煙測觀察（靜態分析）

無法啟動伺服器，改以靜態分析：

1. **data.json 結構**：`{'decisions': 7, 'errors': 1, 'logs': 1, 'tasks': 35}` — errors 為 list，含必要欄位。

2. **errors[0] 樣本**：
   - `error_id: "ERR-20260404-001"`, `error_type: "tool_failure"`, `taxonomy_codes: ["COORD-02", "SEC-03"]`
   - 欄位完整，taxonomy_codes 正確抽取。

3. **logs[0] 衍生欄位**：`has_gate_failure: False`, `failed_gates: []`, `error_summary: ""` — 當前所有 log 均全通過，符合現況。

4. **tasks 全部含 schema_issues 欄位**：確認（35/35），當前無任何 schema 缺漏。

5. **HTML 元素配對**：
   - 4 KPI IDs：kpiErrors、kpiGateFails、kpiFailedTasks、kpiSchemaIssues — 與 app.js renderErrorKpis 一致。
   - 2 canvas IDs：taxonomyChart、timelineChart — 與 renderTaxonomyChart/renderTimelineChart/renderChartFallback 一致。
   - 篩選控制：errorTypeFilter、gateFilter、errorSort — 與 bindErrorControls 一致。
   - 列表容器：errorList — 與 renderErrorList 一致。

6. **escapeHtml 覆蓋**：所有新增 innerHTML 設定均通過 escapeHtml（detail 走 JSON.stringify 後再 escape、title 在 renderErrorList 的 summary 中 escape、taxonomy code/month key 均 escape）。

---

## 剩餘風險

| # | 風險 | 說明 |
|---|------|------|
| R1 | Chart.js CDN 在 CI 或離線環境 | loadChartJs 已 try/catch，fallback 以文字清單呈現，不阻擋 KPI 與錯誤列表 |
| R2 | 當前 data.json 的 errors 只有 1 筆、logs 全通過 | KPI 和圖表在資料稀少時仍正常，但無法真實測試 Gate/Schema KPI > 0 路徑 |
| R3 | renderTaxonomyChart / renderTimelineChart 的 Chart 取得方式（ChartModule.Chart \|\| ChartModule）可能因 CDN module 格式不同而需調整 | 若 Opus 有實際瀏覽器環境可煙測，建議確認 Chart.register 呼叫正確 |
| R4 | README.md 前端動態介面段落第一行由「已提供最小版前端看板」改為「已提供前端看板」 | 語意無誤但措辭變動，Opus 可視需要還原 |

---

## 注意事項（給 Opus Gate 驗證）

1. **不可動清單確認**：本 sub-agent 未觸碰 system/、skills/、memory/、validate_task_card.py、CLAUDE.md、.github/workflows/、tasks/2026-05-11_error-dashboard-html.yaml、logs/、outputs/ 以外的文件（outputs/drafts/ 除外）。
2. **git commit 未執行**：依協議，本 sub-agent 不 commit。請 Opus 在 4 層 gate 全通過後執行 checkpoint commit。
3. **validate_task_card.py 須 Opus 跑**：`python3 system/validate_task_card.py tasks/2026-05-11_error-dashboard-html.yaml` 應 exit 0。
4. **generate_frontend_manifest.py 和 test 已預先完整**：這些是本次 session 開始時已在 repo 中的代碼，不需 sub-agent 重寫。Opus 在 rule_check 時確認 diff 範圍。
5. **DoD 13（audit log）**：須由 Opus 在 commit 後補入 logs/AUDIT_LOG.md 一筆。
