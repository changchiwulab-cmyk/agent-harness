# Phase 0 止血：審計可信度 — 實作摘要

- **Task Card**: `tasks/2026-05-15_audit-integrity.yaml` (`20260515-003`, risk=medium, approval_needed=true)
- **計畫**: `/root/.claude/plans/ticklish-dazzling-crescent.md` Phase 0
- **狀態**: 待人工審閱（approval_needed=true → status=review）

## 做了什麼

把 `logs/AUDIT_LOG.md` 從手寫格式（31 筆、agent 自評、無 marker）遷移為
`generate_audit_log.py` 維護的 **AUTO 區（機檢）+ ## 人工備註（人工維護）** 結構，
並接上 Task Card↔AUDIT_LOG 的 commit-time drift 守門。

## 變動檔案

| 檔案 | 變動 | 權限層 |
|------|------|--------|
| `scripts/migrate_audit_log.py` | 新增：一次性遷移（抽不可推導欄位、idempotent 守門） | scripts |
| `scripts/test_migrate_audit_log.py` | 新增：4 unit tests | scripts |
| `scripts/audit_drift_guard.py` | 新增：PreToolUse 守門，commit 時跑 `--check` | scripts |
| `scripts/test_audit_drift_guard.py` | 新增：6 unit tests | scripts |
| `logs/AUDIT_LOG.md` | 遷移：AUTO 37 筆 + 31 筆人工備註 | logs (allow) |
| `.claude/settings.json` | 追加 drift guard hook（permissions_guard 之後） | **ask** |
| `.github/workflows/spec-consistency.yml` | +migrate/guard 測試 +`--check` gate | **ask** |
| `tasks/2026-05-15_audit-integrity.yaml` | Task Card + 執行紀錄 | allow |

## 遷移前後 diff 摘要

- 來源解析：**31 entries / 31 unique task_id**，格式範例（task_id 空）正確跳過。
- AUTO 區：`generate_audit_log.py` 由 `tasks/20*.yaml` + git 推導 **37 筆**。
- `git diff logs/AUDIT_LOG.md`：888 insertions / 801 deletions（結構重排，非資料刪除）。

## 驗證（零遺失）

- 對照 `git show HEAD:logs/AUDIT_LOG.md` 解析原始 31 筆，逐一比對
  `notes`/`error_summary`：**33 個保留欄位字串，0 遺失**（逐字可追溯）。
- `python3 scripts/generate_audit_log.py --check` → **exit 0**。
- 31 個 `### <task_id>` 人工備註區塊全在；spot-check 多筆 notes 逐字命中。
- 全測試綠：migrate 4 / drift-guard 6 / generate 既有 / permissions 既有 / e2e 4；
  ruby spec-consistency、context budget(1197/3000)、YAML parse 全通過。

## 覆蓋率差集（回報，不自動補卡）

- **AUDIT-ONLY（有手寫紀錄但無 Task Card）**：無。
- **CARD-ONLY（有 Task Card 但從未手寫 audit）**：6 筆 —
  `20260409-001`, `20260415-A01`, `20260509-N09`, `20260509-N10`,
  `20260509-N11`, `20260515-003`。
  → 即 self-reporting gap 的具體證據：先前 audit 靜默漏 6/37（~16%），
  比 N05 自評「2 卡漏」更嚴重；改自動生成後全數納入。**不自動補卡，僅回報。**

## drift 守門：rollout 模式

依使用者決策（warn 一輪再切 block）+ 計畫風險緩解：

- `.claude/settings.json` 已掛 `audit_drift_guard.py`，**預設 warn 模式**
  （`AUDIT_DRIFT_GUARD` 未設 → drift 時 stderr 警告但放行 commit）。
- 觀察無誤報後，設環境變數 `AUDIT_DRIFT_GUARD=block` 即切硬擋（exit 2）。
- **CI 端為硬擋**：`spec-consistency.yml` 的 `Audit log drift check` step
  drift 即 fail（非互動、不影響本地工作流，符合決策 2）。
- guard fail-open：generator 自身錯誤時不擋 commit，永不因守門 bug 卡死流程。

## 已知 footgun（重要工作流提醒）

新增/改 Task Card 或新增 `checkpoint: [task_id]` commit 後，AUDIT_LOG 即落後
（本次實作親歷，與 0515-001/002 data.json drift 同源）。
**正解：完成前 `python3 scripts/generate_audit_log.py`，並把 `logs/AUDIT_LOG.md`
納入最後一個 commit；最後 commit 用非 `checkpoint:` 主旨，避免擾動 grep 集。**

## 剩餘風險

- warn 模式下首輪 drift 不會被真擋（使用者已知情選擇）；CI 為後盾。
- guard 的 `git commit` 偵測為啟發式 token-walk，極端 shell 引號情境可能漏判；
  fail-open + CI backstop 使影響可控。

## 回滾

```
git revert <遷移 commit>           # 還原 AUDIT_LOG 結構
# 或單檔：git checkout <pre-migration>~ -- logs/AUDIT_LOG.md
# settings.json 移除 audit_drift_guard hook 即停用守門
```
遷移前已 checkpoint（`c728339` 卡片 / `791a157` 工具），原始 31 筆永存 git 史。

## 下一步（另開 Task Card）

- Phase 1：三條硬規則機制化（warn 預設，deny-list + drift 為僅有硬擋）。
- Phase 2：approval backlog 可視化 + 批次人工核准。
