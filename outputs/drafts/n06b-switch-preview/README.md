# N06b switch preview — 候選版本，不等於核准切換

本資料夾預製 N06b（task_id `20260509-N09`，`tasks/2026-05-09_harness-plugin-switch.yaml`）切換 PR 會用到的 3 個產物草稿，目的是把那張 PR 的決策面降到接近零。

**重要**：這些都是 **草稿**。N06b 仍 `pending`，等使用者完成 `outputs/drafts/2026-05-09_n06-bootstrap-runbook.md` §1-§4 並核准 N06b 後，才由另一張 PR 把這些檔案搬到正本位置。本資料夾內容**不影響**現行 agent-harness 行為。

---

## 內容

| 檔名 | N06b PR 落點 | 對應 N06b DoD |
|---|---|---|
| `check_plugin_present.sh.draft` | `scripts/check_plugin_present.sh` | DoD #4（≤30 行 routing 腳本）|
| `settings.json.draft` | `.claude/settings.json`（覆寫）| DoD #2（hook 改引用 plugin + fallback）|
| `claude-md-prepend.md` | 插在 `CLAUDE.md` 第 1 行（標題下、第一節「## 三條硬規則」之前）| DoD #3（≤5 行依賴註）|

## N06b 核准後的套用流程

```bash
# 1. 把腳本搬到正本 + 給執行權限
cp outputs/drafts/n06b-switch-preview/check_plugin_present.sh.draft scripts/check_plugin_present.sh
chmod +x scripts/check_plugin_present.sh

# 2. 覆寫 settings.json
cp outputs/drafts/n06b-switch-preview/settings.json.draft .claude/settings.json

# 3. 把 prepend 段插到 CLAUDE.md 開頭（手動或 sed；CLAUDE.md 第一行是 "# 一人公司 Agent Harness v2"）
#    手動編輯較安全：把 claude-md-prepend.md 的 3 行貼在 "# 一人公司 Agent Harness v2" 之後、空白行之前

# 4. 端到端煙霧測試（N06b DoD #6）
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' \
  | bash scripts/check_plugin_present.sh
# 預期：stderr 含 "BLOCKED by pre_tool_use" + stdout 為 {"decision":"block",...}

# 5. CI 雙路徑驗證（N06b DoD #5）
#    plugin 已裝：~/.claude/plugins/agent-governance/hooks/pre_tool_use.py 存在 → 走 plugin
#    plugin 未裝：删掉上面路徑或在 fresh CI runner → 走 scripts/permissions_guard.py fallback
#    兩個 case 都應綠
```

## 設計重點

- **不重造 deny 邏輯**：plugin 端 `hooks/pre_tool_use.py` 已從 `scripts/permissions_guard.py` 移植；切換只決定路由，不重寫規則。
- **Fallback 等價**：`scripts/permissions_guard.py`（156 行 deny-list）保留不動，當 plugin 缺席時 routing 腳本直接 `exec` 它，stdin/stdout 透傳。
- **三層保險**：plugin 路徑 → fallback 路徑 → 兩者都缺時 stdout 回 `{"decision":"allow"}` + stderr 警告（避免 hook 失靈時把所有 Bash 都意外 block）。
- **共用 PERMISSIONS.yaml**：plugin 與 fallback 同一份規則來源（`system/PERMISSIONS.yaml`），切換不改規則內容。

## Rollback

N06b PR merge 後若要撤回：`git revert <merge-commit>` 即可。本資料夾本身可隨時刪除（純 drafts，allow 級）。
