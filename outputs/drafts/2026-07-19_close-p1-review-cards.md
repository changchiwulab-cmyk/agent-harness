# 收案摘要：關閉 3 張 P1 review 卡（20260719-O01）

## 結論
3 張已完成、卡在 review 的 P1 卡收斂為 `done`。三者 PR 皆已合併、`result_summary` 皆 DoD 5/5，純缺人工翻 done。同步補齊 20260712-P11 缺漏的 `approval` 紀錄與 `completion_time`。

## 處置表

| task_id | 卡片 | PR | DoD | completion_time | approval | 處置 |
|---------|------|----|-----|-----------------|----------|------|
| 20260712-P11 | P1-1 allowed_tools runtime enforcement | #134（已合併） | 5/5 | 空 → **補 2026-07-17** | 無 → **補 APR-20260719-001** | review → **done** |
| 20260716-P12 | P1-2 failure_counter 自動記錄 | #137（已合併） | 5/5 | 2026-07-16（已填） | APR-20260716-...（已存） | review → **done** |
| 20260716-P13 | P1-3 注入偵測器佈線 | #138（已合併） | 5/5 | 2026-07-17（已填） | APR-20260717-001（已存） | review → **done** |

## 落差記錄
- **20260712-P11 缺 approval**：其 `date`（2026-07-12）≥ approval cutoff（2026-07-01），依 `check_approval_coverage` 翻 done 需有 `status: approved` 紀錄，先前漏記。本輪補批次 approval 檔 `logs/approvals/2026-07-19_close-p1-review-cards_approval.yaml`（APR-20260719-001）。
- **20260712-P11 缺 completion_time**：`check_spec_consistency.rb` 要求 `done/failed` 卡 `completion_time` 非空，補為 2026-07-17（其 C4 checkpoint 與 PR #134 合併時序）。
- P1-2 / P1-3 欄位齊備，僅翻 status，其他不動。

## 驗證
- `check_spec_consistency.rb` 綠（含 approval 覆蓋率交叉檢查）。
- `sync_derived.sh --check` 零漂移（`frontend/data.json` 的 `task_status` 統計、`logs/AUDIT_LOG.md` 已隨翻 done regen）。

## 核准依據
使用者 2026-07-19 指示「3 張 review 結案，再開工 P1-4」。收案 PR 人工合併為最終批准。
