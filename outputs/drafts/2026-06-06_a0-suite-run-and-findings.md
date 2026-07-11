# A0 — 全套 CI 實跑與發現矩陣（實證基線）

> 草稿 ｜ 2026-06-06 ｜ Task Card `20260606-A01` ｜ skill ops
> 用途：把「靜態閱讀」轉成「實跑證據」，作為 Track A/B 的基礎。綜合敘事見
> `outputs/drafts/2026-06-06_agi-readiness-and-hardening-report.md`。

## 1. 既有 CI 全套實跑（基線，改動前）

完全照 `.github/workflows/spec-consistency.yml` 逐步本機執行，記錄 exit code：

| # | 步驟 | 結果 |
|---|------|:----:|
| 1 | `ruby -c check_spec_consistency.rb`（語法） | PASS |
| 2 | `ruby test_check_spec_consistency.rb`（單元，66 assertions） | PASS |
| 3 | `check_spec_consistency.rb`（spec 一致性） | PASS |
| 4 | 全庫 `YAML.load_file`（**/*.yaml） | PASS |
| 5 | `test_check_context_budget.rb` + `check_context_budget.rb`（~1197/3000） | PASS |
| 6 | `test_generate_frontend_manifest.py` | PASS |
| 7 | `generate_frontend_manifest.py --check`（漂移） | PASS |
| 8 | `test_permissions_guard.py`（11 tests） | PASS |
| 9 | `test_generate_audit_log.py`（6 tests） | PASS |
| 10 | `tests/e2e/test_dummy_task_smoke.py` | PASS |
| 11 | `tests/e2e/test_failure_drill.py` | PASS |
| 12 | `test_check_decision_revisit.rb` | PASS |

**基線結論：13/13 全綠。** harness 是生產級、CI 強健。

## 2. 被攔下的假陽性

- 探索 agent 宣稱「`analysis` 缺於 `GATE_POLICY.yaml:14` → critical bug」。
- **實跑反證**：`GATE_POLICY.yaml:14` 與 `validate_task_card.py:11` 皆含 `analysis`；4 張 analysis 卡 `validate_task_card.py` 全過；全庫 lint exit 0。→ **假陽性**。

## 3. 工具名稱碎片化（已證實的 HIGH）

`tasks/**` 之 `allowed_tools` 詞頻（YAML 解析計數，50 張卡有此欄）：

| token | 次數 | 在 PERMISSIONS.yaml？ | canonical |
|-------|:---:|:---:|------|
| `file_read` | 50 | ❌ | read_project_files |
| `git_commit_checkpoint` | 31 | ✅ allow | — |
| `file_search` | 30 | ✅ allow | — |
| `write_drafts` | 23 | ✅ allow | — |
| `create_output_files` | 16 | ✅ allow | — |
| `web_search` | 9 | ✅ allow | — |
| `file_write` | 8 | ❌ | create_output_files |
| `bash` | 7 | ❌ | run_command |
| `write_logs` | 5 | ✅ allow | — |
| `run_tests` | 3 | ❌ | run_tests（新登錄） |
| `modify_system_rules` | 3 | ✅ ask | — |
| `read_memory` | 2 | ✅ allow | — |
| `modify_settings_json` | 1 | ❌ | modify_system_rules |
| `modify_claude_md` | 1 | ✅ ask | — |
| `modify_skills` | 1 | ✅ ask | — |

- 5 個未對齊 token（`file_read`/`file_write`/`bash`/`run_tests`/`modify_settings_json`）。
- `check_spec_consistency.rb` 原始碼確認：對 `allowed_tools` **零驗證**。
- `permissions_guard.py` 是另一套 runtime 指令樣式 deny-list，與符號詞彙脫節。
- **處置**：`system/TOOL_REGISTRY.yaml`（單一真相）+ CI lint + 修 `TASK_CARD_TEMPLATE.yaml` 根因。別名涵蓋全部既有 token → 加 lint 後仍綠。

## 4. 驗證器分歧（LOW-MED，潛在非啟用）

- `validate_task_card.py`（Python，runtime gate）對 49 張真卡 **0 拒絕**。
- `check_spec_consistency.rb`（Ruby，CI）為嚴格超集（額外驗 task_id regex、date、location、status 必填、logs schema）。
- **處置**：`test_validator_parity.py` pin 住「Ruby ⊇ Python」，守「Python 不得比 CI 嚴」。

## 5. 文件落差（LOW）

| 項 | 現況 | 處置 |
|----|------|------|
| `GATE_POLICY.yaml:11` task_id `YYYYMMDD-###` | linter 實際接受 `-R01` | 改文件對齊 |
| 「連續失敗 3 次」 | 無定義 | GLOBAL_RULES 定義（同卡同 session、成功歸零） |
| DoD 顆粒度 | 未定義 | completion_check 加「單一可獨立驗證」 |

## 6. 改動後最終驗證

全套 CI-equivalent **19/19 exit 0**（13 既有 + 6 新 gate：validator parity、verify_completion 單元+--check、verify_audit_integrity 單元+--check、red-team suite）。
