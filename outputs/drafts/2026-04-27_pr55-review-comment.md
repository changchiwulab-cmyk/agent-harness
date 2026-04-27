# PR #55 Review Comment（草稿，待人工確認後再發送）

> 預定發送目標：https://github.com/changchiwulab-cmyk/agent-harness/pull/55
> 規則依據：CLAUDE.md 規則 2「對外動作只產出草稿」
> 建議發文身分：本 repo 維護者（請使用者親自貼或授權貼）

---

感謝這版 dashboard，整體方向（純靜態 + python http.server + auto-gen manifest）很對齊本 repo「零安裝、可審核」的取向。在合進 `main` 之前，建議先解決下列四項，確保 baseline 不違反 CLAUDE.md 的「可審核」與「無漂移」原則。已對應建立 Task Card `tasks/2026-04-27_frontend-platform-phase0.yaml`（task_id `20260427-F01`），明列 DoD。

### 1. YAML 解析會在 v2 schema 上失真（影響「可審核」）
`frontend/app.js` 的 `pick()` 用單行 regex 抓 top-level key，碰到下列欄位會抓不到或抓錯：
- `goal: |` 多行字串（很多 task card 的 goal 都是 block scalar）
- `gate_results:` 巢狀物件（schema/rule/completion/risk 4 燈）
- `approvals: []`、`tools_used: []`、`options_considered: []` 陣列
- `decision_summary` 在某些舊 decision 寫成 `summary` 或缺欄

**建議**：把解析責任移到 generator（PyYAML 已是系統原生依賴），輸出 `frontend/data.json`，前端改 `fetch('./data.json')`，不再做 YAML 解析。

### 2. `frontend/manifest.js` 容易與檔案系統漂移
目前是 generator 寫死的路徑陣列，但 CI 沒有「跑一次 generator 後 diff 應為空」的檢查。新增/移除 task 或 decision 後忘記重跑，UI 就會無聲缺漏。

**建議**：在 `.github/workflows/spec-consistency.yml` 加：
```yaml
- run: python3 scripts/generate_frontend_manifest.py
- run: git diff --exit-code frontend/data.json
```

### 3. decisions glob 寫死單一 project
`scripts/generate_frontend_manifest.py` 第 30 行 hard-code `memory/active_projects/agent-harness/decisions/*.yaml`。未來新增 active project（系統設計上是支持多 project 的）就會漏。

**建議**：改為 `memory/active_projects/*/decisions/*.yaml`。

### 4. 缺少 generator 測試
對照 PR #49 / 任務 `20260424-O03` 把 `check_context_budget.rb` 連同 `test_check_context_budget.rb` 一起進 main 的標準，本次新工具也應附測試（至少：空輸入、多 project、idempotency 三 case）。

---

### 後續路線（FYI）
本次只是 Phase 0（baseline 收斂）。若上述補完，後續規劃：
- **Phase 1**：把 Gate Policy / Approval Trail / Failure Taxonomy 14 類視覺化（這是 v2 馬鞍工程的核心價值，目前 dashboard 完全沒呈現）
- **Phase 2**：Context Budget 進度條（接 `scripts/check_context_budget.rb`）+ token/cost 折線
- **Phase 3**：Decision Graph（用 `revisit_trigger`/`related_task`/`status` 連邊）

每階段獨立 Task Card，逐一過 Gate。

如果這個收斂方向 OK，可以把這個 PR 轉 draft，我這邊用 `20260427-F01` 在新分支補完後再開新 PR；或者直接 push 到本 PR head 也可以，看你偏好。
