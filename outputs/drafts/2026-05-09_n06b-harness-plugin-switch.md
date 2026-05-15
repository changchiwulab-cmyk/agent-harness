# N06b — agent-harness 切換引用 agent-governance plugin

- Task Card: `20260509-N09`（risk=medium，使用者 2026-05-15 明示核准）
- 上游：N06（`20260509-N06`）bootstrap + D007 決策；N10 預製切換產物
- 前置：使用者回報 `changchiwulab-cmyk/agent-governance` v0.1.0 已建好（帶外手動，agent 無法獨立查驗，見下「驗證邊界」）

## 切換前後 diff 摘要（DoD #8）

| 檔案 | 切換前 | 切換後 |
|---|---|---|
| `.claude/settings.json` | PreToolUse(Bash) → `python3 scripts/permissions_guard.py`（直連 fallback） | PreToolUse(Bash) → `bash scripts/check_plugin_present.sh`（路由層） |
| `scripts/check_plugin_present.sh` | 不存在 | 新增（21 行）：plugin 在 → `~/.claude/plugins/agent-governance/hooks/pre_tool_use.py`；缺席 → `scripts/permissions_guard.py`；皆缺 → `{"decision":"allow"}` + stderr 警告 |
| `CLAUDE.md` | 標題後直接進正文 | 標題後插 3 行依賴 blockquote（plugin 依賴 + fallback + 路由來源） |
| `D007` 決策檔 | `status: active` | 加 `followup_done: "20260509-N09"`（轉 public 仍待 v0.2.0） |

未刪除 `system/validate_task_card.py`、`scripts/permissions_guard.py`、`scripts/generate_audit_log.py`——雙寫並存，待 plugin v0.2.0 stable 由遷移卡處理。

## 引用方式（DoD #9）

**npm-style 原生 plugin 安裝目錄**：`~/.claude/plugins/agent-governance/`（Claude Code 原生 plugin 約定位置）。
agent-harness **不** vendor / 不 git submodule / 不 clone plugin 進本 repo——僅在 runtime 由 `check_plugin_present.sh` 偵測該路徑是否存在來決定路由。plugin 的安裝/升級由使用者在 `~/.claude/plugins/` 端自理，與本 repo 解耦（符合 D007 獨立 repo + N4 §1.3 解耦聲明）。

## DoD 對照

| # | 項目 | 結果 |
|---|---|---|
| 1 | agent-governance v0.1.0 存在 | ⚠️ 使用者具結（agent 無 gh / 跨 repo MCP scope，無法獨立查驗）|
| 2 | settings.json → plugin + fallback | ✅ |
| 3 | CLAUDE.md ≤5 行依賴段 + 預算 | ✅ 3 行；budget 1287/3000 |
| 4 | check_plugin_present.sh ≤30 行 | ✅ 21 行，`bash -n` 通過 |
| 5 | plugin 在/缺席兩路徑皆綠 | ✅ 實測：缺席→fallback block；模擬 plugin 在→走 plugin hook |
| 6 | PreToolUse 端到端煙霧測試 | ✅ `rm -rf /` payload → `{"decision":"block",...}` + stderr「BLOCKED by permissions_guard」exit 2 |
| 7 | D007 followup_done 標記 | ✅ |
| 8 | PR diff 摘要 + rollback | ✅ 本文件 + PR description |
| 9 | 引用方式註記 | ✅ 見上「引用方式」 |

## 驗證邊界（誠實聲明）

DoD #1「agent-governance v0.1.0 已存在」由使用者於 2026-05-15 具結回報「repo 已建好」。本 agent 的 GitHub 工具被硬限制於 `changchiwulab-cmyk/agent-harness` 單一 repo，且環境無 `gh` CLI，**無法獨立查驗** `agent-governance` repo / v0.1.0 tag 是否實際存在。切換邏輯的安全性不依賴此查驗：plugin 缺席時 `check_plugin_present.sh` 自動降回 `scripts/permissions_guard.py`，故即使外部 repo 尚未就緒，agent-harness 行為與 CI 不受影響。

## Rollback（DoD #8）

```
git revert <merge-commit>      # 一行完整還原 settings.json + CLAUDE.md + D007 + 刪 check_plugin_present.sh
```

PR merge 前可直接關 PR。agent-governance plugin repo 不在本卡範圍，rollback 不影響它。
