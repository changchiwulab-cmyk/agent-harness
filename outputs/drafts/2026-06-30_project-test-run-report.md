# 專案測試報告 — 三次測試 campaign

- **Task Card**：`tasks/2026-06-30_project-test-run.yaml`（`20260630-T01`）
- **日期**：2026-06-30
- **skill_type**：ops　**risk_level**：low　**approval_needed**：false
- **測試依據**：`.github/workflows/spec-consistency.yml`（專案唯一事實來源）+ `scripts/run_frontend.sh`（前端開機）
- **狀態**：草稿（依硬規則 #2 與 GATE_POLICY risk_check，輸出留存於 `outputs/drafts/`）

---

## 1. 總判定

> **✅ 測試結果 PASS — 三次測試全綠，無任何失敗、無 flaky。**
> **⚠️ 治理：rule_check 升級（記為 fail）— 前端煙霧觸及 deny 邊界，詳見 §7／§8。**

- 驗證套件 12 步（拆解為 13 個可執行子步）× 3 次 = **39/39 子步全部通過**。
- 底層自動化測試案例 **63 個**（Ruby 35 runs / 103 assertions + Python 28 tests），三次皆 **0 failures / 0 errors**。
- 前端開機煙霧測試 **3/3** 回 HTTP 200（`index.html` + `data.json`），`data.json` 為合法 JSON。
- 四層 Gate：schema / completion / risk **pass**；**rule_check 據實記為 fail 並升級**（前端煙霧啟動瞬時 `http.server`，屬 PERMISSIONS deny 的 `spawn_background_process`；經使用者明示授權、即起即關、無殘留）。
- 連跑三次結果完全一致，**可重現性 100%**。

---

## 2. 測試環境（已實測）

| 項目 | 版本 |
|------|------|
| ruby | 3.3.6 (2024-11-05 revision 75015d4c1f) [x86_64-linux] |
| python3 | 3.11.15 |
| PyYAML | 6.0.1 |
| git | 2.43.0 |
| 平台 | Linux 6.18.5 |
| 執行日期 | 2026-06-30 |
| 工作分支 | claude/gracious-goldberg-j7j734 |

CI（`spec-consistency.yml`）所需的 ruby 3.2 / python 3.11 / pyyaml 皆齊備，本機環境與 CI 相容。

---

## 3. 12 步 × 3 次結果矩陣

`spec-consistency.yml` 的 Context budget 步驟含兩道指令（單元測試 + 實檢），故拆為 05a/05b 共 13 個子步。

| # | 步驟 | 指令 | Run 1 | Run 2 | Run 3 |
|---|------|------|:---:|:---:|:---:|
| 01 | Ruby 語法檢查 | `ruby -c scripts/check_spec_consistency.rb` | ✅ | ✅ | ✅ |
| 02 | Ruby 單元（spec consistency）| `ruby scripts/test_check_spec_consistency.rb` | ✅ | ✅ | ✅ |
| 03 | Spec 一致性檢查 | `scripts/check_spec_consistency.rb` | ✅ | ✅ | ✅ |
| 04 | YAML 全解析 | `ruby -e '...YAML.load_file...'` | ✅ | ✅ | ✅ |
| 05a | Context budget 單元 | `ruby scripts/test_check_context_budget.rb` | ✅ | ✅ | ✅ |
| 05b | Context budget 實檢 | `ruby scripts/check_context_budget.rb` | ✅ | ✅ | ✅ |
| 06 | 前端 manifest 單元 | `python3 scripts/test_generate_frontend_manifest.py` | ✅ | ✅ | ✅ |
| 07 | 前端 manifest 漂移 | `python3 scripts/generate_frontend_manifest.py --check` | ✅ | ✅ | ✅ |
| 08 | Permissions guard 單元 | `python3 scripts/test_permissions_guard.py` | ✅ | ✅ | ✅ |
| 09 | Audit log generator 單元 | `python3 scripts/test_generate_audit_log.py` | ✅ | ✅ | ✅ |
| 10 | E2E dummy task smoke | `python3 tests/e2e/test_dummy_task_smoke.py` | ✅ | ✅ | ✅ |
| 11 | E2E failure-drill 回歸 | `python3 tests/e2e/test_failure_drill.py` | ✅ | ✅ | ✅ |
| 12 | Decision revisit 單元 | `ruby scripts/test_check_decision_revisit.rb` | ✅ | ✅ | ✅ |
| | **每次小計** | | **13/13** | **13/13** | **13/13** |

---

## 4. 底層測試案例數（單次）

| 測試檔 | 框架 | 案例 / assertions |
|--------|------|------|
| `scripts/test_check_spec_consistency.rb` | Ruby Test::Unit | 20 runs / 66 assertions |
| `scripts/test_check_context_budget.rb` | Ruby Test::Unit | 10 runs / 13 assertions |
| `scripts/test_check_decision_revisit.rb` | Ruby Test::Unit | 5 runs / 24 assertions |
| `scripts/test_generate_frontend_manifest.py` | Python unittest | 4 tests |
| `scripts/test_permissions_guard.py` | Python unittest | 11 tests |
| `scripts/test_generate_audit_log.py` | Python unittest | 6 tests |
| `tests/e2e/test_dummy_task_smoke.py` | Python unittest | 4 tests |
| `tests/e2e/test_failure_drill.py` | Python unittest | 3 tests |
| **合計** | | **Ruby 35 runs / 103 assertions + Python 28 tests = 63 案例** |

每次執行：**0 failures、0 errors、0 skips**。三次累計 **189 個案例執行（63 × 3）零失敗**。

---

## 5. 各步耗時（wall-clock, ms）與穩定度

| # | 步驟 | Run 1 | Run 2 | Run 3 | 平均 |
|---|------|---:|---:|---:|---:|
| 01 | ruby_syntax_check | 14 | 16 | 14 | 15 |
| 02 | ruby_unit_spec_consistency | 168 | 114 | 118 | 133 |
| 03 | spec_consistency_check | 114 | 95 | 90 | 100 |
| 04 | yaml_parse_check | 160 | 119 | 144 | 141 |
| 05a | context_budget_unit | 132 | 104 | 110 | 115 |
| 05b | context_budget_check | 63 | 81 | 66 | 70 |
| 06 | frontend_manifest_tests | 94 | 79 | 88 | 87 |
| 07 | frontend_manifest_drift | 165 | 171 | 169 | 168 |
| 08 | permissions_guard_tests | 53 | 53 | 54 | 53 |
| 09 | audit_log_generator_tests | 140 | 112 | 127 | 126 |
| 10 | e2e_dummy_task_smoke | 138 | 138 | 145 | 140 |
| 11 | e2e_failure_drill | 100 | 110 | 108 | 106 |
| 12 | decision_revisit_tests | 1021 | 1055 | 1051 | 1042 |
| | **套件總計** | **2362** | **2247** | **2284** | **2298** |

**穩定度判讀**：

- **可重現性 100%**：每一步在三次都 PASS，無紅燈、無 flaky、無順序相依。
- **耗時穩定**：套件總時長 2247–2362ms，全距僅 115ms（≈5%），屬正常系統雜訊範圍。
- **熱點單一**：`decision_revisit_tests`（~1.04s）占套件約 45%，因其反覆 spawn 子程序解析；三次間僅 ±1.7% 抖動，穩定。其餘各步皆 < 200ms。
- 無「首次較慢、後續轉快」之顯著快取效應，代表測試不依賴可變外部狀態。

---

## 6. 前端開機煙霧測試（3 次）

每次以 `scripts/run_frontend.sh <port>` 啟動（預設路徑：先重新產生 `data.json` 再 `python3 -m http.server`），
就緒後 `curl` 探測兩個關鍵資產，**探測完立即關閉伺服器**（瞬時、不留背景常駐）。

| Run | Port | `index.html` | `data.json` | data.json 合法 JSON | 拆除 |
|-----|------|---|---|:---:|:---:|
| 1 | 8091 | 200（1387 B）| 200（27041 B）| ✅ | ✅ |
| 2 | 8092 | 200（1387 B）| 200（27041 B）| ✅ | ✅ |
| 3 | 8093 | 200（1387 B）| 200（27041 B）| ✅ | ✅ |

- 三次回應位元組數完全一致 → 啟動腳本的 `data.json` 重新產生為**冪等**（不造成漂移；測試後 `git status` 對 `frontend/data.json` 無變更）。
- 測試後查無 `python3 -m http.server` 殘留程序，8091–8093 埠皆未在監聽 → **無背景常駐外洩**。

---

## 7. 四層 Gate 驗證（`system/GATE_POLICY.yaml`）

| Gate | 結果 | 依據 |
|------|:---:|------|
| **schema_check** | ✅ pass | `python3 system/validate_task_card.py` rc=0；`check_spec_consistency.rb` 對新卡 `OK`。task_id 格式/日期一致、DoD 4 條、`expected_output` 三欄齊全。 |
| **rule_check** | ⚠️ **fail（升級）**| 工具白名單、web search 0 次、checkpoint 紀律皆符合；惟前端煙霧啟動了瞬時 `http.server`，屬 PERMISSIONS deny 的 `spawn_background_process`，而 rule_check 要求「動作不在 deny 清單中」。為維護審計完整性，**據實記為 fail 並升級**（非乾淨 pass）：該動作經使用者於規劃階段明示授權、即起即關、已實證無殘留（見 §6），依 GATE_POLICY `on_fail` 已寫 `logs/errors/2026-06-30_20260630-T01_error.md` 並通知使用者。測試交付物不受影響。 |
| **completion_check** | ✅ pass | DoD 逐條：①12 步×3 次擷取完成；②前端煙霧×3 皆 200；③本報告含全部規定章節；④四層 gate 已記錄且報告留在 drafts/。 |
| **risk_check** | ✅ pass | risk=low 與實際動作（純讀取 + 跑專案自身測試 + 寫草稿/logs）一致；無對外/正式資料變更；報告位於 `outputs/drafts/` 而非 `reports/`。 |

---

## 8. 異常與備註

- **測試零異常**。三次 campaign 無任何步驟失敗，未觸及硬規則 #3（連續失敗 3 次停下）。
- **治理升級（rule_check）**：前端開機煙霧的瞬時 `http.server` 觸及 deny 項 `spawn_background_process`。本報告初版將 rule_check 記為 pass（含註記），經 PR #119 Codex review（P2）指出會使 dashboard/audit 把此 run 誤計為規則合規。依使用者裁示**改記 fail 並升級**，補 `logs/errors/2026-06-30_20260630-T01_error.md`（error_type: rule_violation, resolution: escalated）。後續建議：在 PERMISSIONS/GATE_POLICY 釐清「經人工明示授權的瞬時 deny 動作」之記錄語意，避免落入 pass/fail 二選一。
- 測試本身全部讀取/自包含（tempfile、`--check` 模式），未變更 repo 受管內容。
- 設置階段曾新增 Task Card 並重新產生 `frontend/data.json`（避免步驟 07 漂移檢查失敗）；此為提交所需的正常維護，非測試失敗。
- 本次未涵蓋：對 GitHub 遠端 CI 的實跑（本機等效執行 CI 全套指令）、跨 Python/Ruby 版本矩陣（僅本機既有版本）。

---

## 9. 結論

專案在本機依其自身規範（CI 套件 + 前端開機）連續測試三次，**測試全數通過、結果可完全重現**。
四層 Gate 中 schema / completion / risk pass；**rule_check 據實記為 fail 並升級**（前端煙霧之 deny-boundary，
經人工授權、無殘留），以維護治理數據的審計完整性。測試交付物本身不受影響。
提交狀態（含本次新增的 Task Card、run log、error log 與重生的 `data.json`）可通過專案 CI。
