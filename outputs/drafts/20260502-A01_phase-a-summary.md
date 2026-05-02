# Phase A 實作摘要 — 20260502-A01

- 日期：2026-05-02
- Task Card：`tasks/2026-05-02_phase-a-enforcement-and-observability.yaml`
- 上游分析：`outputs/drafts/2026-05-02_project-completeness-analysis.md`
- 狀態：草稿（等人工審閱後決定 audit_log 落地與否）

## Phase A 目標回顧

針對「規格 ≠ 執行」「觀測性不對稱」「沒有 e2e 流程驗證」三大根本缺點，補：
- A1 — PreToolUse hook 把 `PERMISSIONS.yaml` deny 從自我約束變成 runtime 攔截
- A2 — Audit log 結構化欄位由 Task Card + git log 自動推導，去掉自我評分
- A3 — CI 跑 dummy Task Card 走完 4 個 gate，避免規格漂移

Phase B（metric loop）/ Phase C（trust gradient）刻意不在本卡涵蓋。

## 變動檔案

| 檔案 | 動作 | 說明 |
|------|------|------|
| `.claude/settings.json` | 新增 | PreToolUse hook 註冊 `Bash` matcher |
| `scripts/permissions_guard.py` | 新增 | Hook 主體：比對 deny 清單，預設 allow |
| `scripts/test_permissions_guard.py` | 新增 | 11 個 unit test（含 evaluate + main + 邊界） |
| `scripts/generate_audit_log.py` | 新增 | 從 Task Card + git log 推導；保留 `## 人工備註` 區段 |
| `scripts/test_generate_audit_log.py` | 新增 | 5 個 test（記錄推導 / git mock / 手寫保留 / drift） |
| `tests/__init__.py`、`tests/e2e/__init__.py` | 新增 | Python 套件占位 |
| `tests/e2e/test_dummy_task_smoke.py` | 新增 | 3 個 case：4 gate 全綠、risk gate 拒 reports/ 路徑、schema gate 拒缺 DoD |
| `.github/workflows/spec-consistency.yml` | 修改 | 新增 3 個 step：permissions_guard / audit_log / e2e |
| `tasks/2026-05-02_phase-a-enforcement-and-observability.yaml` | 新增 | 本卡 |
| `outputs/drafts/2026-05-02_project-completeness-analysis.md` | 新增 | 上游分析草稿 |
| `frontend/data.json` | 重生 | 因新增 task card 觸發 manifest 漂移檢查 |

## 測試結果

```
ruby scripts/check_spec_consistency.rb            → ok
ruby scripts/test_check_spec_consistency.rb       → 14 runs / 43 assertions / 0 failures
ruby scripts/check_context_budget.rb              → 1197/3000 tokens
python3 scripts/test_generate_frontend_manifest.py→ 4 runs / OK
python3 scripts/generate_frontend_manifest.py --check→ OK
python3 scripts/test_permissions_guard.py         → 11 runs / OK
python3 scripts/test_generate_audit_log.py        → 5 runs / OK
python3 tests/e2e/test_dummy_task_smoke.py        → 3 runs / OK
```

## 設計取捨

### 1. permissions_guard 採白名單外的「保守 deny-list」，不嘗試做 sandbox
- `rm` 不帶 `-r`/`-f` 不阻擋（rare 且第二層 git 可救）
- `git push --force` 直接擋（high blast radius）
- 對外 webhook（Slack / Telegram / LINE / Discord）統一擋
- 設計原則：False positive（誤擋正常工作）比 false negative（放過刁鑽指令）更傷害可用性，因為 LLM 仍是第一層自律

### 2. audit_log generator 不接管現有 `logs/AUDIT_LOG.md`
- 現有 13 筆紀錄含 `model_used`、`tools_called` 計數，**Task Card 不追蹤這些欄位**，硬轉會丟資訊
- 因此本卡不在 CI 加 `--check`，工具僅作為 opt-in
- 真正落地需另開 Task Card：(a) 擴 Task Card schema 加 `model_used` / `tools_called`、(b) 一次性把舊紀錄人工移到 `## 人工備註`
- 本卡先把工具與測試交付，遷移決策保留給後續

### 3. e2e smoke test 是 contract pinning，不是 LLM 行為驗證
- 4 個 gate 函式在測試裡是純 Python 化身，不呼叫 LLM
- 目的：當 `PERMISSIONS.yaml` / `GATE_POLICY.yaml` schema 被破壞、或 `validate_task_card.py` 退化時，CI 立刻紅
- LLM 真實執行 gate 的品質仍仰賴 Claude 對 `GATE_POLICY.yaml` 的遵守，由人工 review 把關

## DoD 對照

| # | DoD | 狀態 |
|---|-----|------|
| 1 | `.claude/settings.json` 含 PreToolUse hook 註冊 Bash matcher | ✅ |
| 2 | `scripts/permissions_guard.py` 對 stdin tool_input 輸出 JSON 決策 | ✅ |
| 3 | `scripts/test_permissions_guard.py` ≥ 4 case | ✅ 11 case |
| 4 | `scripts/generate_audit_log.py` 從 tasks + git log 推導，保留人工 notes | ✅ |
| 5 | 兩支 pytest 全綠 | ✅ |
| 6 | `tests/e2e/test_dummy_task_smoke.py` 4 gate 全觸發、輸出落 drafts/ | ✅ |
| 7 | `.github/workflows/spec-consistency.yml` 新增 step | ✅ |
| 8 | 本摘要產出 | ✅ |
| 9 | `logs/AUDIT_LOG.md` 新增 1 筆本卡紀錄 | ⏳ 待人工確認後 append（避免覆蓋既有手寫 entries） |
| 10 | `validate_task_card.py` 對本卡 exit 0；CI 整體綠 | ✅（local CI 全綠；雲 CI 待 PR push） |

## 剩餘風險與後續

### 風險
1. **Hook 在 Claude Code 真實 session 中是否觸發**：local 測試是模擬輸入，實際 session 需打開 `.claude/settings.json` 才生效；首次 session 觀察 1 週確認攔截事件數
2. **正則太保守**：`rm tempfile.txt` 不擋；若日後出現問題再收緊
3. **Audit log 雙軌期**：手寫 + 生成器並存可能讓人不確定該改哪份；下次任務先試跑 generator 到 `outputs/drafts/AUDIT_LOG_AUTO.md` 比對差異

### 後續 Task Card 候選
- `phase-a2-audit-log-migration`：擴 Task Card schema + 一次性遷移舊紀錄
- `phase-b-metric-loop`：從 audit log 自動算 retry 率、token 平均、approval 等待時間
- `phase-b-failure-taxonomy-instrumentation`：error_log → FAILURE_TAXONOMY observed_count

### 觀察指標（首週）
- permissions_guard 攔截事件數：若 = 0 持續 4 週，考慮將攔截縮小為 warning（避免過度設計）
- e2e smoke test 觸發次數：每次 PR 都跑，CI 紅燈率
- 人工是否還想手寫 `logs/AUDIT_LOG.md`：若 generator 跑通且資料夠用，遷移即可啟動

---

**End of summary**
