# N06：v3 governance plugin bootstrap

- Task: `20260509-N06`
- Date: 2026-05-09
- Skill: ops
- Status: review（DoD #1-#5/#7/#9 完成；#6/#8 留下個 session）
- 上游：A01 §5.2 plugin 邊界 + N4 skeleton + N7 評估

## 0. 一句話

使用者於 PR #69 明示核准 N06 + 4 子題決策（D007）。本 session 受工具限制（GitHub MCP 僅限 agent-harness），無法直接建外部 repo，改採折衷：在 `outputs/drafts/agent-governance-bootstrap/` 完整準備 plugin v0.1.0 檔案樹，下個 session 由使用者 git init + push。

## 1. 4 子題決策（Decision Log D007）

| # | 子題 | 決策 | 理由 |
|---|------|------|------|
| 1 | Repo 命名 | `agent-governance` | 與 N4 plugin.json name 一致；plan §6 解耦目標對齊 |
| 2 | License | Apache-2.0 | 保留 patent 條款，與企業整合友善；MIT 也可，但 Apache 多 patent 保護成本接近於零 |
| 3 | Visibility | Private（v0.1.0 內部驗證後再轉 public） | v0.1.0 → v0.2.0 之間的 breaking change 不被外部使用者卡住 |
| 4 | Layout | 獨立 repo | 與 N4 §1.3 plugin 與 harness 解耦聲明一致 |

完整決策文件：`memory/active_projects/agent-harness/decisions/20260509-D007_v3-plugin-bootstrap-decisions.yaml`

## 2. 已交付（DoD #1/#2/#3/#4/#5/#7/#9）

位於 `outputs/drafts/agent-governance-bootstrap/`：

```
agent-governance-bootstrap/
├── plugin.json                   # DoD #1 — manifest（5 commands + 4 schemas + 2 hooks + 2 validators 全註冊）
├── README.md                     # DoD #7 — 5 步 quick start + 與 harness 解耦聲明
├── LICENSE                       # DoD #7 — Apache-2.0 完整文本
├── CHANGELOG.md                  # DoD #7 — 0.1.0 release notes
├── commands/                     # DoD #2 — 5 slash command 介面契約
│   ├── task-card.md
│   ├── audit.md
│   ├── decision.md
│   ├── run-log.md
│   └── gate-check.md
├── schemas/                      # DoD #3 — 4 個 schema 草案
│   ├── task_card.schema.yaml
│   ├── decision_log.schema.yaml
│   ├── execution_log.schema.yaml
│   └── failure_taxonomy.schema.yaml
├── hooks/                        # DoD #4 — 2 hooks + 5 tests
│   ├── pre_tool_use.py           # 移植自 scripts/permissions_guard.py
│   ├── post_task_use.py          # 新：4-stage gate runner
│   └── test_hooks.py             # 5 unit tests（pre 4 + post 4，總 8 含 hook entry test）
├── validators/                   # DoD #5 — 2 validators + 13 tests
│   ├── validate_task_card.py     # 移植自 system/validate_task_card.py（exit code 改 2）
│   ├── check_audit_format.py     # 新：audit log 格式檢查 + AUTO marker 平衡
│   └── test_validators.py        # 13 unit tests
└── .github/workflows/ci.yml      # CI workflow（hook tests + validator tests + manifest sanity）
```

每個介面契約（5 commands）標註 input / output / 副作用 / 錯誤處理 / contract（對應 schema 或 validator）。

## 3. 待下個 session 完成（DoD #6/#8）

| # | DoD | 阻擋原因 | 下個 session 動作 |
|---|-----|---------|-------------------|
| 6 | agent-harness CLAUDE.md / settings.json 切換引用 plugin | modify_system_rules + modify_claude_md（ask 級）未在本 PR 範圍 | 開新 PR 修改 |
| 8 | agent-harness 自身 CI 在 plugin 缺席仍綠 | 待 #6 完成後驗證 | #6 PR 內順帶測試 |
| — | 真實 GitHub repo 建立（agent-governance, private） | GitHub MCP 限定 agent-harness 單一 repo | 使用者本機 / 新 session |
| — | git init agent-governance + 搬入 outputs/drafts/agent-governance-bootstrap/ + push v0.1.0 | 同上 | 同上 |

## 4. 下個 session 5 步遷移指南

```bash
# 1. 在 GitHub 建 private repo
gh repo create agent-governance --private --description "Governance layer for Claude Code"

# 2. clone 空 repo + 從本 PR 搬入 bootstrap 檔樹
git clone git@github.com:<owner>/agent-governance
cd agent-governance
cp -r ~/agent-harness/outputs/drafts/agent-governance-bootstrap/. .

# 3. 跑 plugin 自身的 tests 確認搬入無誤
python -m unittest hooks.test_hooks -v
python -m unittest validators.test_validators -v

# 4. 初次 commit + tag v0.1.0
git add .
git commit -m "chore: v0.1.0 skeleton bootstrap from agent-harness PR #69"
git tag v0.1.0
git push -u origin main --tags

# 5. 在 agent-harness 新 PR 切換引用（modify_system_rules 範圍）
#    - 修改 .claude/settings.json hook 指向 plugin
#    - 在 CLAUDE.md 註明 plugin 依賴
#    - agent-harness CI 仍須通過（plugin 缺席不掛）
```

## 5. 已知工程缺陷（本 PR 內無法處理）

### 5.1 Hook PATH 脆弱性

`.claude/settings.json` 的 `PreToolUse` hook 指令 `python3 scripts/permissions_guard.py` 使用相對路徑。當 cwd 不在 repo root 時 hook 會找不到腳本而 block 全部 Bash 工具呼叫（本 session 在準備 plugin tests 時就撞到了：cd 進 bootstrap 子目錄後無法回退）。

建議下個 session 順帶修為 absolute path 或 `${CLAUDE_PROJECT_DIR}/scripts/permissions_guard.py`（屬於 modify_system_rules，故未在本 PR 修）。

### 5.2 plugin v0.1.0 與 harness v2.x 並存期

bootstrap 完成後一段時間內 agent-harness 仍會保有自己的 system/validate_task_card.py、scripts/permissions_guard.py 等。雙寫漂移風險與 N3 PoC 階段相同。緩解：v0.2.0 stable 後，agent-harness 改 import plugin 版本，刪除自有複本（屬遷移卡，非本卡範圍）。

## 6. DoD 自評（9 條）

| # | DoD | 對應 | 狀態 |
|---|-----|------|:----:|
| 1 | plugin.json manifest 草案 | `plugin.json` | ✅ |
| 2 | 5 slash command 介面契約 | `commands/*.md` 5 檔 | ✅ |
| 3 | 4 schema 草案 | `schemas/*.schema.yaml` 4 檔 | ✅ |
| 4 | 2 hook 介面 + ≥3 unit tests 每個 | `hooks/{pre,post}_*.py` + 8 tests | ✅（test_hooks.py 含 4 pre + 4 post） |
| 5 | 2 standalone validator + CLI 入口 | `validators/{validate_task_card,check_audit_format}.py` + 13 tests | ✅ |
| 6 | agent-harness CLAUDE.md / settings.json 切換引用 plugin | — | ⏸ 留下個 session |
| 7 | README + LICENSE + CHANGELOG + CI workflow | 4 檔備齊 | ✅ |
| 8 | agent-harness 自身仍可獨立通過 spec-consistency CI | — | ⏸ 待 #6 完成後驗證 |
| 9 | Decision Log D007 紀錄 4 子題決策 | `memory/active_projects/agent-harness/decisions/20260509-D007_*.yaml` | ✅ |

→ 7/9 完成；2/9 受工具限制留下個 session。

## 7. 後續候補

- **N06-續**：agent-harness 切換引用 plugin（DoD #6/#8）— ask 級，需另開 PR
- **M01**：原生 Memory PoC（已建卡 `tasks/2026-05-09_native-memory-poc.yaml`，等核准）
- **plugin v0.1.1+**：bootstrap 後 plugin repo 自身的 follow-up（不在本 PR 範圍）
