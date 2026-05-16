# Phase 2：Approval backlog 可視化 + 批次核准記錄 — 實作摘要

- **Task Card**: `tasks/2026-05-15_approval-backlog.yaml` (`20260515-005`, ops, risk=medium, approval_needed=true)
- **計畫**: `ticklish-dazzling-crescent.md` Phase 2；承接 Phase 0/1（`20260515-003/004` done, `APR-20260515-001/002`）
- **狀態**: 待人工審閱（`status: review`）

## 設計取向

計畫定調「可視化 + 批次人工核准，**不自動核准**，人工簽核保留」。
`approval_backlog.py` 兩模式，純讀取掃描 + 操作者批次記錄器；
與 Phase 0/1 既有 `logs/approvals/` schema 及 `RETRO_FLOW.md` 消費路徑對齊。

## 變動檔案

| 檔案 | 變動 | 權限層 |
|------|------|--------|
| `scripts/approval_backlog.py` | 新增：scan + --approve 批次記錄 | scripts |
| `scripts/test_approval_backlog.py` | 新增：8 tests | scripts |
| `.github/workflows/spec-consistency.yml` | +approval_backlog 測試 step | **ask** |

## 行為

- **scan（預設）**：列出 Pending 簽核 = `tasks/20*.yaml` 中 `approval_needed==true` 且 `status==review` 且 `logs/approvals/` 無同 task_id，附等待天數；加上 drafts 數/最舊檔齡、已核准數/最新 approval_id。Backlog 非空為正常，**非 CI gate**。
- **--approve TASKID[,...] --by NAME [--note]**：操作者執行以記錄一批人工決策。對每個 task_id 寫 `logs/approvals/<date>_<tid>_approval.md`（schema 同 APR-20260515-001/002，`approval_id` 為 `APR-YYYYMMDD-NNN` sequential）。已有 approval 的 task_id 拒絕（不重複簽核，非零退出）。**不翻 Task Card status**（狀態轉換仍為獨立明確動作）。缺 `--by` 直接拒絕（人工簽核必須有歸屬）。

> Agent 僅在轉達**明確人工批次決策**時才呼叫 `--approve`（與 Phase 0/1 現行流程一致：人在對話核准 → 記錄 approval log）。絕不自我核准。

## scan 實跑（真實 repo，--today 2026-05-16）

```
Pending 簽核：5 筆
  - 20260427-F01 [medium] 等待 19d：收斂 PR #55 為前端平台的最小可審核 baseline...
  - 20260502-A01 [medium] 等待 14d：Phase A：補齊規則 enforcement 與觀測自動化...
  - 20260509-A01 [medium] 等待 7d：規劃 Harness v3 重構範圍...
  - 20260509-N03 [medium] 等待 7d：skills/research/SKILL.md 加原生 Skills frontmatter...
  - 20260509-N06 [high]   等待 7d：依 N4 skeleton 真正建立 agent-governance plugin repo...
草稿 outputs/drafts/：27 個（最舊 7d）
已核准 logs/approvals/：2 筆（最新 APR-20260515-002）
```

→ **即時揭露 0515-002 審查指出的「卡塞 review」症狀**（先前不可見）：5 張卡（含 1 high）卡在 review 無 sign-off，最久 19 天。Phase 0/1 卡因已 done+approved 正確排除。

## 批次記錄示範

```
$ approval_backlog.py --approve 20260509-A01,20260509-N03 --by user --note "batch"
RECORDED 20260509-A01 -> logs/approvals/2026-05-16_20260509-A01_approval.md (APR-20260516-001)
RECORDED 20260509-N03 -> logs/approvals/2026-05-16_20260509-N03_approval.md (APR-20260516-002)
$ approval_backlog.py --approve 20260509-A01 --by user      # 重複
REFUSED 20260509-A01: 已有 approval 紀錄，不重複簽核   (exit 1)
```

## 與 APPROVAL_POLICY / RETRO_FLOW 對齊

- 寫出的 approval log 結構與 Phase 0/1 手寫者一致（`approval_id/task_id/date/method/decision/approved_by`）→ `RETRO_FLOW.md`「資料蒐集」讀 `logs/approvals/` 不受影響。
- `APPROVAL_POLICY.yaml` 的 `human_confirm` 語義不變：仍是人決定、工具只記錄。**無 system/ 變更**。

## 剩餘風險

- scan 的「pending」僅涵蓋 `status==review` 的卡；其他狀態的待辦不在此視圖（刻意聚焦可簽核項）。
- `--approve` 機制上 agent 可呼叫；防線同 Phase 0/1：人工先決策、流程約束、`--by` 強制歸屬、重複拒絕。非自動核准。

## 回滾

```
git revert <Phase 2 commit>
# 純新增檔；移除 scripts/approval_backlog*.py 與 1 個 CI step 即還原，無資料破壞
```

## ask 變更清單（待人工核准）

1. `.github/workflows/spec-consistency.yml` — 新增 approval_backlog 測試 step

## 計畫完成度

Phase 0（審計可信度）/ 1（三條硬規則）/ 2（approval backlog）全部交付。
治理從「文件」轉為「機制」：drift + deny-list 硬擋；規則1/2 warn；規則3 CI 機檢；
backlog 可視化 + 批次記錄。人工簽核全程保留。
