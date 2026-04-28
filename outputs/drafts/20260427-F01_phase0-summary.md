# Phase 0 Implementation Summary — `20260427-F01`

> Task Card：`tasks/2026-04-27_frontend-platform-phase0.yaml`
> 分支：`claude/frontend-phase0-F01`（base：`codex/create-dynamic-frontend-interface-o2shz6` aka PR #55）
> 狀態：草稿，待人工 review 後合併

## 變動清單

| 檔案 | 變動 | 目的 |
|---|---|---|
| `scripts/generate_frontend_manifest.py` | rewrite | PyYAML 解析後輸出 `frontend/data.json`（不再產 manifest.js）；多 project decisions glob；新增 `--check` 漂移模式 |
| `frontend/data.json` | new (generated) | 唯一資料來源；deterministic、sorted、`ensure_ascii=False`、indent=2 |
| `frontend/app.js` | rewrite | `fetch('./data.json')`；移除整套 regex YAML parser；加 `escapeHtml` 防 XSS；錯誤狀態顯示 |
| `frontend/manifest.js` | deleted | 由 `data.json` 取代 |
| `scripts/test_generate_frontend_manifest.py` | new | 4 case：empty / multi-project / idempotency / drift-check |
| `.github/workflows/spec-consistency.yml` | append | setup-python + pyyaml + 跑 manifest tests + `--check` 漂移檢查 |
| `scripts/run_frontend.sh` | minor | 版號 1.3.0 → 1.4.0；help 文案改稱 `data.json` |
| `README.md` | rewrite section | 「前端動態介面」章節改述 data.json 與 CI 漂移檢查 |
| `tasks/2026-04-27_frontend-platform-phase0.yaml` | from plan branch | 自帶 task card |

## DoD 對照

| # | DoD | 狀態 |
|---|---|---|
| 1 | generator 輸出 `frontend/data.json`，PyYAML 解析 | ✅ |
| 2 | `frontend/app.js` 改讀 data.json、移除 regex parser | ✅ |
| 3 | `frontend/manifest.js` 移除 | ✅ |
| 4 | decisions glob 改 `memory/active_projects/*/decisions/*.yaml` | ✅ |
| 5 | `scripts/test_generate_frontend_manifest.py`：empty / multi-project / idempotency 三 case | ✅（共 4 case，含 drift-check 額外 1 條） |
| 6 | spec-consistency CI 加 `--check` 漂移檢查 | ✅（並一併跑 unit tests） |
| 7 | `run_frontend.sh` CLI 介面（`--no-generate` / `--help` / `--version` / port）不變 | ✅（僅文案同步） |
| 8 | README「前端動態介面」章節同步更新 | ✅ |
| 9 | validate_task_card + pytest + spec-consistency CI 全綠 | 🟡 本地 pytest + drift check 全綠；CI 待 PR push 後驗證 |
| 10 | `outputs/drafts/20260427-F01_phase0-summary.md` 摘要 | ✅（本檔） |
| 11 | `logs/AUDIT_LOG.md` 新增 1 筆紀錄 | ✅ |

## 本地驗證

```bash
$ python3 scripts/generate_frontend_manifest.py --check
OK: frontend/data.json is up to date.

$ python3 scripts/test_generate_frontend_manifest.py
....
Ran 4 tests in 0.010s
OK

$ python3 system/validate_task_card.py tasks/2026-04-27_frontend-platform-phase0.yaml
✅ Task Card 驗證通過

$ ruby scripts/check_context_budget.rb   # CLAUDE.md + GLOBAL_RULES.md
554/3000 tokens (18.5%)  # 未變動，OK
```

## 仍存在的限制（留給 Phase 1+）

- UI 還沒呈現 `gate_results`、`approvals[]`、`tools_used[]`、`options_considered[]` —— Phase 1 範圍。
- 沒有 a11y / dark-mode / i18n。
- 沒有對 `outputs/drafts/` vs `outputs/reports/` 的視覺區分。
- generator 目前只取 task card 的「平面欄位」+ decision 的關鍵欄位；如要完整 round-trip 整份 YAML，未來可加 `?full=1` 模式。

## 風險與 rollback

- **風險**：CI 新增 PyYAML 安裝步驟可能因網路故障 flake；緩解：`pip install --no-cache-dir pyyaml`，失敗即重跑。
- **Rollback**：`git revert` 本 PR 即可，不影響其他系統。原 PR #55 的 manifest.js 可由 git 歷史救回。

## 後續

- 通過 review → merge 進 `codex/create-dynamic-frontend-interface-o2shz6` 或直接 retarget 到 `main`（看 PR #55 處理方式）。
- 開 Phase 1 task card：Gate / Approval / Failure 視覺化。
