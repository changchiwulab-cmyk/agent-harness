# Phase 1：三條硬規則機制化 — 實作摘要

- **Task Card**: `tasks/2026-05-15_enforce-hard-rules.yaml` (`20260515-004`, ops, risk=medium, approval_needed=true)
- **計畫**: `ticklish-dazzling-crescent.md` Phase 1；承接 Phase 0 (`20260515-003` done, `APR-20260515-001`)
- **狀態**: 待人工審閱（`status: review`）

## 設計取向

三條硬規則本質是 agent 行為治理。真正危險的兩件事已被機制硬擋
（PERMISSIONS deny-list → `permissions_guard.py`；AUDIT_LOG drift →
`audit_drift_guard.py`）。Phase 1 依計畫「預設 warn、避免新抽象、沿用
既有 schema」把其餘規則做成**可觀測/可機檢**，而非脆弱的 runtime daemon：

- **規則 1/2 → PreToolUse warn**（`harness_guard.py`，永不擋、fail-open）。
- **規則 3 → schema 欄位 + CI validator**（harness 既有「schema+validator+CI」
  範式，如 `validate_task_card.py` / `generate_*--check`）。

## 變動檔案

| 檔案 | 變動 | 權限層 |
|------|------|--------|
| `scripts/harness_guard.py` | 新增：規則1/2 warn PreToolUse | scripts |
| `scripts/test_harness_guard.py` | 新增：9 tests | scripts |
| `scripts/check_failure_policy.py` | 新增：規則3 機檢 | scripts |
| `scripts/test_check_failure_policy.py` | 新增：6 tests | scripts |
| `system/EXECUTION_LOG_SCHEMA.yaml` | +`retry_policy`(consecutive_failures, failure_policy_action) | **ask** |
| `.claude/settings.json` | +Write\|Edit matcher → harness_guard | **ask** |
| `.github/workflows/spec-consistency.yml` | +2 測試 step +規則3 gate step | **ask** |

## 規則對應與行為

- **規則 1（無 Task Card 不執行）**：寫 `outputs/|system/|skills/|scripts/|.github/|.claude/|frontend/|memory/|tests/` 但 git working tree/HEAD 無 Task Card 活動 → `decision: allow` + warning。普遍適用（draft 也需 Task Card）。寫 `tasks/` 本身永不觸發。
- **規則 2（對外只出草稿）**：寫 `outputs/` 下非 `outputs/drafts/`（如 `outputs/reports/`）→ allow + warning（draft-first 提醒）。
- **規則 3（連續失敗 3 次停）**：`check_failure_policy.py` 掃 `logs/runs/*.y{a,}ml`，`consecutive_failures>=3` 之 run 必須 `failure_policy_action==stopped` 且 `logs/errors/` 有同 task_id；違反 exit 1。無 `logs/runs/` → exit 0（vacuous）；舊檔無 `retry_policy` → 視為 0（向後相容）。

## warn 範例

```
WARNING harness_guard: 規則2 提醒：outputs/reports/retro-x.md 不在 outputs/drafts/。
WARNING harness_guard: 規則1 提醒：正在寫 system/PERMISSIONS.yaml，但 ... 看不到 Task Card 活動。
```

## 規則 3 機檢示範（DoD 要求）

人工構造違規 fixture（3 連敗、未 stopped、無 error log）：

```
FAIL: 規則3（連續失敗 3 次須停 + error log）違反：
  - logs/runs/demo.yaml: consecutive_failures=3 但 failure_policy_action='warned'（規則3 應為 'stopped'）
  - logs/runs/demo.yaml: consecutive_failures=3 但 logs/errors/ 無 task_id='DEMO-999' 的紀錄
exit=1
```

真實 repo：`OK: 規則3 失敗政策檢查通過` exit 0。

## 唯二 hard-block 不變（且已驗證為活體）

實作過程中 `rm -rf $TMP` 被 `permissions_guard` 即時擋下
（`shell_delete` deny）——Phase 0/既有 hook chain 為**活的硬擋**的第一手證據。
Phase 1 新增機制全為 warn 或 CI-artifact 檢查，**不在 runtime 擋使用者**。

## 測試與 CI

- `test_harness_guard` 9 / `test_check_failure_policy` 6 全綠；既有套件全綠。
- 兩 drift `--check` exit 0；ruby spec-consistency / context-budget / YAML 通過。

## 剩餘風險

- 規則1/2 為啟發式 warn：可能漏報（lenient by design）；不誤擋（fail-open）。
- 規則3 是 artifact 機檢非 runtime 強制停：仍仰賴 agent 誠實寫 `logs/runs/`；
  但一旦寫了就**不能瞞報**（CI 硬擋），把「自律」變「可稽核」。

## 回滾

```
git revert <Phase 1 commit>
# settings.json 移除 Write|Edit matcher 即停用 harness_guard
# EXECUTION_LOG_SCHEMA.yaml retry_policy 為新增欄位，移除不影響舊檔
```

## ask 變更清單（待人工核准）

1. `system/EXECUTION_LOG_SCHEMA.yaml` — 新增 `retry_policy` 區塊
2. `.claude/settings.json` — 新增 Write|Edit matcher → `harness_guard.py`
3. `.github/workflows/spec-consistency.yml` — 新增 2 測試 step + 規則3 gate

## 下一步

Phase 2：approval backlog 可視化 + 批次人工核准（另開 Task Card）。
