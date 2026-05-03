# O06 — Archive tools-inventory 三張卡

- Task ID：20260503-O06
- 日期：2026-05-03

## TL;DR

`git mv` 三張 tools-inventory Task Card 到 `tasks/archived/`。**CI healthcheck（`check_task_output_exists.py`）首次全綠。** frontend tasks 17 → 14。

## 搬檔清單

| Task ID | 舊路徑 | 新路徑 |
|---|---|---|
| 20260404-R01 | `tasks/2026-04-04_tools-inventory-research.yaml` | `tasks/archived/` |
| 20260404-R02 | `tasks/2026-04-04_tools-inventory-review.yaml` | `tasks/archived/` |
| 20260404-O01 | `tasks/2026-04-04_tools-inventory-fix.yaml` | `tasks/archived/` |

## 前置條件

✅ `outputs/drafts/20260503-W03_tools-inventory-memo.md` 已存在

## CI 本機驗證

| 步驟 | 結果 |
|---|---|
| `python3 scripts/check_task_output_exists.py` | **OK: all done/review Task Cards have their expected_output present.** |
| `python3 scripts/generate_frontend_manifest.py` | 16 tasks（-1 對比 O04 完成後的 17，W03 卡新增 +1 後再 -3） |
| `python3 scripts/generate_frontend_manifest.py --check` | OK |
| `ruby scripts/check_spec_consistency.rb` | OK |
| `python3 scripts/test_check_task_output_exists.py` | OK (5 tests) |

## 效應

- CI healthcheck 從連續紅燈（7 → 3 drifts 後仍紅）到**首次全綠**
- PR #65 的 `validate-spec` step 在下次 push 後預期全綠（含新加的 task output existence check）
- A02 → O04 + A03 → O06 兩輪 archive 合計清除 7 張遺失卡漂移，全部源自 pre-2026-04-11 gitignore 根因
