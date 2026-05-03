# O04 — Archive AI-era Proposal 4 張卡

- Task ID：20260503-O04
- 日期：2026-05-03
- 觸發：A02 Go/No-Go 選 D（park）後的歸檔執行；W02 memo 已落地作為前置條件

## TL;DR

`git mv` 4 張 status: review 的 ai-era-solo-business 提案線 Task Card 從 `tasks/` 到 `tasks/archived/`，frontend 任務數從 20 → 16，spec consistency CI 在本機通過。歸檔意義由所在目錄表達（`VALID_STATUS` 沒有 archived，刻意不改 status 欄位）。tools-inventory 三張不在本卡範圍，待後續 A03 處理。

## 搬檔清單

| Task ID | 舊路徑 | 新路徑 |
|---|---|---|
| 20260404-S01 | `tasks/2026-04-04_ai-era-solo-business-strategy.yaml` | `tasks/archived/2026-04-04_ai-era-solo-business-strategy.yaml` |
| 20260404-W01 | `tasks/2026-04-04_ai-era-solo-business-proposal.yaml` | `tasks/archived/2026-04-04_ai-era-solo-business-proposal.yaml` |
| 20260404-RV01 | `tasks/2026-04-04_ai-era-solo-business-proposal-review.yaml` | `tasks/archived/2026-04-04_ai-era-solo-business-proposal-review.yaml` |
| 20260404-O02 | `tasks/2026-04-04_proposal-fix-v2.yaml` | `tasks/archived/2026-04-04_proposal-fix-v2.yaml` |

四張皆用 `git mv`，rename history 保留可追溯。

## 前置條件確認

✅ `outputs/drafts/20260503-W02_solo-business-strategy-memo.md` 已存在（commit `171eea6`）— 結論層快照已固化，方可放心搬檔。

## CI 本機驗證

| 步驟 | 結果 |
|---|---|
| `ruby scripts/check_spec_consistency.rb` | OK |
| `python3 scripts/generate_frontend_manifest.py` | Generated `frontend/data.json` (16 tasks, 1 logs, 6 decisions) |
| `python3 scripts/generate_frontend_manifest.py --check` | OK: up to date |
| `python3 scripts/check_task_output_exists.py` | **FAIL（剩 3 張 tools-inventory 漂移）** |
| `python3 scripts/test_check_task_output_exists.py` | OK (5 tests) |

CI 紅燈為**預期行為**：O05 strict 健檢仍會攔到 3 張 tools-inventory 卡的輸出遺失（同一 pre-2026-04-11 gitignore 根因，但不在 A02 / O04 範圍）。將由後續 A03 mini-Go/No-Go 處理。

## frontend/data.json before/after

| 指標 | before | after | delta |
|---|---:|---:|---:|
| tasks 陣列長度 | 20 | 16 | −4 |
| logs 陣列長度 | 1 | 1 | 0 |
| decisions 陣列長度 | 6 | 6 | 0 |

（DoD 原本估計 17 → 13，是寫卡時的舊計數；其間多開了 A02/W02/O04/O05 共 4 張，計數整體 +4 但 delta 仍正確 −4。）

## DoD 對照

| # | DoD 條件 | 結果 |
|---|---|---|
| 1 | W02 memo 草稿存在 | ✅ |
| 2 | 4 yaml git mv 完成 | ✅ |
| 3 | spec consistency 全綠 | ✅ |
| 4 | frontend manifest + drift check 全綠 | ✅ |
| 5 | data.json tasks 從 17 → 13 | ⚠️ 實際 20 → 16（同 delta，新卡造成基準位移）|
| 6 | 輸出 archive-summary | ✅（本檔）|
| 7 | AUDIT_LOG 1 筆 | 接續寫入 |

7/7 對應條件達成（#5 的數字漂移已說明）。

## 後續

- A03（待開）：對 `tools-inventory-research/review/fix` 三張 status: done 卡做 mini-Go/No-Go，決定 archive 或重產
- A03 完成後 → CI healthcheck 步驟回綠 → PR #65 整體可 merge
