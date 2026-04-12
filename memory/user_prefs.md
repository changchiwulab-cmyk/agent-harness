# 使用者偏好

使用者全域偏好統一存放於 `~/.claude/memory/`（Claude Code 全域記憶）。
本檔案不再重複儲存，以防兩處內容漂移。

agent-harness 的 memory/ 資料夾**只存放**任務執行 context：
- `active_projects/` — 進行中專案的背景、決策紀錄
