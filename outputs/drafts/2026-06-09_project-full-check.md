# 審查報告：專案完整檢查（agent-harness）

- **Task Card**：`20260609-R02`（skill_type: review, risk_level: low）
- **檢查日期**：2026-06-09　**branch**：`claude/busy-ramanujan-4espn8`
- **範圍**：全套 CI-equivalent + 全部 Task Card schema 驗證 + 結構一致性

---

## 總體評估

**通過（健康）。** 全部 17 項自動化檢查綠、53 張 Task Card schema 全數有效、CLAUDE.md 宣告之 system/ 檔案與必要目錄齊備。本次另把前端深度測試（`20260609-F04`）納入檢查範圍，generator 與 UI 渲染的邊界/安全行為皆有自動化覆蓋。未發現需修正項。

| 維度 | 結果 |
|------|------|
| 自動化檢查（test/check/e2e/node） | ✅ 17 / 17 |
| Task Card schema 驗證 | ✅ 53 / 53（0 invalid） |
| 結構一致性（system 檔 + 目錄） | ✅ 全齊 |
| 前端 drift | ✅ data.json 與實況同步（49 tasks / 2 logs / 7 decisions） |
| 待修正項 | 無 |

---

## 通過項：自動化檢查（17/17）

| # | 檢查 | 指令 | 結果 |
|---|------|------|------|
| 1 | spec consistency 語法 | `ruby -c scripts/check_spec_consistency.rb` | ✅ |
| 2 | spec consistency 單元測試 | `ruby scripts/test_check_spec_consistency.rb` | ✅ |
| 3 | spec consistency 檢查 | `ruby scripts/check_spec_consistency.rb` | ✅ |
| 4 | context budget 單元測試 | `ruby scripts/test_check_context_budget.rb` | ✅ |
| 5 | context budget 檢查 | `ruby scripts/check_context_budget.rb` | ✅ |
| 6 | decision revisit 單元測試 | `ruby scripts/test_check_decision_revisit.rb` | ✅ |
| 7 | decision revisit 檢查 | `ruby scripts/check_decision_revisit.rb` | ✅ |
| 8 | 全 YAML 可解析 | `ruby -e '...YAML.load_file...'` | ✅ |
| 9 | frontend manifest 單元測試 | `python3 scripts/test_generate_frontend_manifest.py`（13） | ✅ |
| 10 | frontend drift | `python3 scripts/generate_frontend_manifest.py --check` | ✅ |
| 11 | permissions guard 測試 | `python3 scripts/test_permissions_guard.py` | ✅ |
| 12 | audit log generator 測試 | `python3 scripts/test_generate_audit_log.py` | ✅ |
| 13 | governance metrics 測試 | `python3 scripts/test_governance_metrics.py` | ✅ |
| 14 | e2e happy-path 煙測 | `python3 tests/e2e/test_dummy_task_smoke.py` | ✅ |
| 15 | e2e failure-drill | `python3 tests/e2e/test_failure_drill.py` | ✅ |
| 16 | app.js 語法 | `node --check frontend/app.js` | ✅ |
| 17 | 前端深度渲染測試 | `node frontend/test_app_render.mjs`（6 情境） | ✅ |

> 註：#13 governance_metrics、#17 前端深度渲染測試屬本次擴充覆蓋；其餘 15 項與 `.github/workflows/spec-consistency.yml` 的 CI 步驟一致。建議把 #13 也補進 CI workflow（目前 CI 未含 governance_metrics 測試）。

## 通過項：Task Card 與結構

- **Task Card schema**：`tasks/`（含 examples/、archived/，排除 TEMPLATE）共 **53 張全數通過** `system/validate_task_card.py`。
- **結構一致性**：CLAUDE.md 宣告之 6 個 system 檔（PERMISSIONS / GLOBAL_RULES / AGENT_CONTEXT / APPROVAL_POLICY / GATE_POLICY / EXECUTION_LOG_SCHEMA）皆存在；`check_spec_consistency.rb` 另已驗證 `logs/runs`、`logs/approvals`、`logs/errors`、`outputs/drafts`、`outputs/reports`、`memory/active_projects` 必要目錄存在。

## 前端深度測試覆蓋（本次擴充，20260609-F04）

- **generator（Python, 13 tests）**：欄位白名單、`execution_log` 解包/flat、decisions project 萃取、`load_yaml` 非 mapping、`build_overview` 分佈與 gate tally、budget 估算與缺檔、drift 偵測 missing/changed、idempotent。
- **app.js（Node, 6 情境）**：7-panel 契約、**XSS 跳脫**（`<img onerror>`/`<script>`/`<b>` 皆被 escape）、空資料 fallback、**超預算 ⚠ 告警**、**Decision Graph matched/external/orphan 三態 + legend + 邊數**、**keyword/date 篩選 + reset**。

---

## 必須修改

無。

## 建議修改（非阻斷）

- **CI 補測**：`.github/workflows/spec-consistency.yml` 目前未含 `python3 scripts/test_governance_metrics.py`；建議補一步，使 CI 與本完整檢查一致。
- **沿用前次 review 之後續**：前端 open PR 收斂（#77/#80/#94/#90/#81）、F01 卡片 status review→done（人工 merge 決策）。

---

## Definition of Done 逐條確認

- [x] 全套 CI-equivalent 逐項 pass/fail：通過 — 上表 17/17 綠
- [x] 驗證所有 Task Card schema：通過 — 53 valid / 0 invalid
- [x] 結構一致性（system 檔 + 目錄）：通過 — 6 檔齊 + 必要目錄齊
- [x] 彙整健康報告：通過 — 本檔
- [x] 結論明確、fail 列出位置與建議：通過 — 無 fail；列 1 項 CI 補測建議

**結論**：專案處於健康狀態，無阻斷性問題；唯一建議是把 governance_metrics 測試補進 CI 以對齊完整檢查範圍。
