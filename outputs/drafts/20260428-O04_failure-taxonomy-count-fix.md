# 20260428-O04 — FAILURE_TAXONOMY 計數收斂｜執行摘要（草稿）

- 任務 ID：`20260428-O04`
- 完成日期：2026-04-28
- 風險等級：low（approval_needed=true，因觸及 `system/`）
- 分支：`claude/go-setup-zu6Dw`（合進 PR #60）
- 對應 Task Card：[`tasks/2026-04-28_failure-taxonomy-count-fix.yaml`](../../tasks/2026-04-28_failure-taxonomy-count-fix.yaml)

## 1. 背景

20260428-F02 Phase 1 實作期間發現預存不一致：

| 來源 | 計數 |
|---|---|
| `system/FAILURE_TAXONOMY.yaml` 實際 IDs | 15（spec×4 / coordination×4 / validation×3 / security×4）|
| `system/FAILURE_TAXONOMY.yaml` header 註解 | 14 |
| `system/GLOBAL_RULES.md` line 48 | 14 |

Git 歷史溯源：`git log -p --follow system/FAILURE_TAXONOMY.yaml` 顯示僅一次 commit
（`f99223f`，2026-04-09 v1.5→v2.0 upgrade）。從一開始就是 header 14 vs 內容 15。
當時 `RUN-20260409-001` 紀錄寫「漏 SEC-04，已補正至 14 種」是計數誤判（4+4+3+4=15）。

## 2. 變動清單

```diff
# system/FAILURE_TAXONOMY.yaml:1
-# Failure Taxonomy — 14 種 Agent 常見失敗模式
+# Failure Taxonomy — 15 種 Agent 常見失敗模式

# system/GLOBAL_RULES.md:48
-14 種常見失敗模式（規格 42% / 協調 37% / 驗證 21% / 安全獨立維度）。
+15 種常見失敗模式（規格 42% / 協調 37% / 驗證 21% / 安全獨立維度）。

# frontend/data.json
-system_meta.failure_taxonomy 第一行 comment 由 14 → 15
（重新產生，無實質欄位變動）
```

百分比 `42% / 37% / 21%` 維持不動 — 那些是研究數據比例，不是計數比例。
ID 與條目內容（name / description / mitigation）皆不動。

## 3. DoD 對照

| # | 條目 | 狀態 | 證據 |
|---|---|---|---|
| 1 | `FAILURE_TAXONOMY.yaml` header 14→15 | ✅ pass | line 1 已改 |
| 2 | `GLOBAL_RULES.md` 14→15 | ✅ pass | line 48 已改 |
| 3 | 兩檔以外不動 | ✅ pass | git diff 範圍只有 system/ 兩檔 + frontend/data.json（自動重產）+ task card 執行紀錄 + audit log + 本檔 |
| 4 | 本地 CI 等價檢查全綠 | ✅ pass | `check_spec_consistency.rb` OK / `test_check_spec_consistency.rb` 14 runs 0 fail / `check_context_budget.rb` ~1197/3000 / `test_generate_frontend_manifest.py` 9/9 / `--check` OK |
| 5 | `frontend/data.json` 重新產生並 commit | ✅ pass | 18 tasks（含新 Task Card）+ system_meta header 同步 |
| 6 | `AUDIT_LOG.md` 新增 1 筆 | ✅ pass | logs/AUDIT_LOG.md 已追加 |
| 7 | 本檔（O04 summary） | ✅ pass | 即本檔 |

## 4. 連動考慮：是否更新 RUN-20260409-001 historical log？

**建議：不動。** 該紀錄是當時的事實（agent 確實補了 SEC-04，且當時誤判總數），保留作為
歷史誤判案例反而是 SEC-04（幻覺驅動行動 / 計數錯誤）的真實 instance。修改會破壞
audit trail 的不可竄改性。

## 5. Gate Policy 4 層自驗

| Gate | 結果 | 說明 |
|---|---|---|
| schema_check | pass | Task Card `task_id 20260428-O04`、goal、DoD 7 條、skill_type=ops、risk_level=low、allowed_tools 皆完整；`validate_task_card.py` 通過 |
| rule_check | pass | 工具使用全在白名單；修改 `system/` 屬 ask 級，已在前一 turn 出示 diff 並取得使用者「按你的建議處理」綠燈；外部查詢 0 次 |
| completion_check | pass | 7 條 DoD 全 pass |
| risk_check | pass | low risk × 純文檔同步 × 無 runtime 行為改變 × 無對外動作；輸出存 `outputs/drafts/` |

四 gate 全 pass。

## 6. 後續建議

- 完成此 PR 合併後，FAILURE_TAXONOMY 計數一致性問題正式關閉。
- 未來新增 ID 時：請同時更新 `system/FAILURE_TAXONOMY.yaml` header 與 `GLOBAL_RULES.md` 的計數，或考慮將計數從文字描述改為自動計算（會違反「文檔即事實」原則，需另起決策）。
