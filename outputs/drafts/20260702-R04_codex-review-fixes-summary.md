# 20260702-R04 摘要：PR #122 Codex review 三項修復

## 改了什麼

- **P1（squash merge 決定論）**：`generate_audit_log.py` 新增 `resolve_checkpoints()` — Task Card 的 `checkpoints:` 欄位非空即為權威來源，空的才 fallback `git log --grep`。修向（卡片優先 vs --check 忽略 vs merge 政策）由使用者定案。docstring 同步改寫，說明卡片與 reviewed diff 同源、可審。
- **P2（分隔符 ampersand）**：`spawn_background_process` 加獨立 token 規則（前有空白、後為空白或行尾），`cmd & cmd2` 形式的背景啟動也擋；排除 stderr 重導向（`2>&1`、`>&2`）、雙 ampersand、URL 查詢字串。已知 trade-off：引號字串內帶空格的 ampersand 會誤擋（正則不解析引號），已記錄在測試註解 — 執行中我自己的 commit message 就中招一次，改寫訊息即可。
- **P3（引號路徑）**：`auto_write_memory` 三個 alternative 的 `memory/` 前各允許 `["']?`，`>> "memory/f"`、`tee 'memory/f'`、`cp a "memory/a"` 不再繞過。

## 驗證

- guard 26 測試、generator 8 測試全綠（各含新增 pin）。
- 12 個 stdin smoke case 全對（6 block / 6 allow，含 `2>&1`、URL、`&&` 反例）。
- squash merge 模擬：detached checkout + `git merge --squash` 後 `generate_audit_log.py --check` exit 0（見卡片 DoD）。

## Checkpoints

- dc87573（任務卡 + 批准紀錄）
- 319077a（guard 兩處 pattern）
- b65b81e（generator 卡片優先）
