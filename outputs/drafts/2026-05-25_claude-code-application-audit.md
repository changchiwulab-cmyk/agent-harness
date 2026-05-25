# Claude Code 應用層面 Audit — agent-harness（A01）

| 欄位 | 值 |
|------|---|
| task_id | 20260525-A01 |
| date | 2026-05-25 |
| skill_type | analysis |
| risk_level | **high** |
| status | **draft** |
| requires_human_review | **true** |
| 上次 NATIVE_OVERLAP 評估 | 2026-05-09（16 天前） |
| 警訊閾值 | aggregate overlap_pct > 50% |

---

## 1. 執行摘要

**4 維度缺口分數（採用 `NATIVE_OVERLAP.yaml` 的 `overlap_pct` 方法，但這次量的是「應對接但未對接」的覆蓋差）：**

| 維度 | 應對接 | 已對接 | 缺口 % | 觸發硬規則 |
|------|--------|--------|--------|------------|
| Hooks 進階用法 | 5 種 hook 事件 | 1 種（PreToolUse/Bash） | **80%** | 全 3 條 |
| Subagents + Slash Commands | 5 agents + ≥3 commands | 0 + 0 | **100%** | 規則 1（Task Card） |
| MCP 與外部整合 | 涵蓋 session 自帶 ≥40 個 mcp__github__* | 0 條 PERMISSIONS 規則 | **100%** | 規則 2（草稿）|
| Claude Code on the web | 5 項環境差異需在 CLAUDE.md 註記 | 0 項 | **100%** | 規則 3（失敗 3 次）|

**Aggregate 估算：** 4 維度平均 95% 缺口。但這只是「新出現需求」的覆蓋率，與 `NATIVE_OVERLAP.yaml` 既有 9 模組的 aggregate 30%（「冗餘可砍」方向）不是同一個指標 — 應在 NATIVE_OVERLAP 新增 4 個模組欄位後重算 aggregate，預估會從 30% 上升至 **40-45%**（仍未觸發 50% 警訊，但接近）。

**3 條 P0 建議：**

1. **修補 4 個 SKILL.md 缺失的 frontmatter**（analysis/ops/review/writing）。當前 `.claude/skills/` 只 symlink 了 research → 5 個 skill 只有 1/5 進入 Claude Code 原生自動載入。這是已批准 N03 PoC 結論的延伸落地，risk_level: low，1 張小卡可解。
2. **新增 PostToolUse hook 落地「連續失敗 3 次停下」**（CLAUDE.md 硬規則 3 目前是純文字提醒，無自動偵測）。寫 `logs/error_count.json`，配 Stop hook 在 session 結束時清零。
3. **PERMISSIONS.yaml 新增 `mcp_github_read` / `mcp_github_write` 兩組分類**。本 session 已自帶 40+ 個 `mcp__github__*` 工具，但 PERMISSIONS.yaml 三層完全沒涵蓋，造成現有規則無法判定 `merge_pull_request`、`push_files` 等高風險動作的審批等級。

**結論：** 不需立即觸發大規模重構（NATIVE_OVERLAP aggregate 尚未到 50%），但 4 維度都有可在 1-2 週內收斂的落地缺口。建議拆 6-7 張 follow-up Task Card 分批執行。

---

## 2. 方法與範圍

**對齊基準：** Claude Code 當前文件（https://code.claude.com/docs）+ 本 session 觀察到的可用工具與行為。

**評估維度（每維度三層）：**
- 功能對接度（是否使用該功能）
- 與硬規則契合度（能否降低 CLAUDE.md 3 條硬規則的人為遵守成本）
- 落地成本（小：< 1 張卡；中：1 卡 + 1 PR；大：跨 2 卡 + 系統面改動）

**不在範圍內（列 P2 一筆帶過）：**
- Plugins（已有 N06 plugin bootstrap 在做，獨立軌道）
- Status line（一人公司無團隊看板需求）
- Memory tool（已有 N03/N04 native memory PoC 流，獨立軌道）
- IDE extension（CLI/web 為主要介面）

**高風險假設：**
- 假設 Claude Code 文件「2026-05 之後沒有大版本破壞性更新」— 若有，本報告結論需重評
- 假設 mcp__github__* 工具集在不同 web session 一致 — 若會因 trigger 不同而變動，PERMISSIONS 規則需用萬用字元

---

## 3. Hooks 進階用法

### 3.1 現況

`.claude/settings.json` 僅 1 條 hook：

```json
{
  "hooks": {
    "PreToolUse": [
      {"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 scripts/permissions_guard.py"}]}
    ]
  }
}
```

`scripts/permissions_guard.py` 對應 PERMISSIONS.yaml 5 條 deny 規則：`shell_delete`、`send_email`、`send_message_external`、`execute_payment`、`git_force_push`。但 `git_force_push` 沒寫在 PERMISSIONS.yaml 的 deny 清單裡（**規則漂移**，需修補）。

PreToolUse 只攔 Bash，**Edit/Write 完全沒攔**。CLAUDE.md「對外動作只產出草稿」與「只能寫 outputs/drafts/」的規則靠 prompt 約束。

### 3.2 缺口

| Hook 事件 | 對應硬規則 | 缺口嚴重度 |
|-----------|------------|------------|
| PostToolUse | 「連續失敗 3 次停下」自動計數 | **P0 高** |
| Stop | audit log 自動追加（取代手動寫 AUDIT_LOG.md） | P1 中 |
| SessionStart | bootstrap GLOBAL_RULES + AGENT_CONTEXT + 載入未完成 Task Card | P1 中 |
| UserPromptSubmit | 偵測無 Task Card 即提醒（呼應「沒有 Task Card 不執行」） | P2 低 |
| PreToolUse / Edit\|Write | 對外動作攔截（檢查目標路徑是否在 outputs/drafts/ 或 logs/）| P1 中 |

### 3.3 建議

**建議 H1（P0，須另開卡 → `20260526-O01`）：PostToolUse 失敗計數**

Matcher：`*`（全工具）。腳本骨架：
- 讀 hook payload 的 `tool_response` 與 exit code
- 失敗 → `logs/error_count.json` 中 `consecutive_failures += 1`
- 成功 → 歸零
- `consecutive_failures >= 3` → 印「請停下並寫入 logs/errors/，等使用者確認」並 exit code 2

**建議 H2（P1，須另開卡 → `20260526-O02`）：Stop hook 自動追加 AUDIT_LOG**

從 transcript 取本次 session 的 task_id / tools_used / checkpoints，依 `system/EXECUTION_LOG_SCHEMA.yaml` 簡化版格式追加到 `logs/AUDIT_LOG.md`。注意 Stop hook 在 web 環境是否觸發 — 列為 **待驗證**。

**建議 H3（P1，須另開卡 → `20260526-O03`）：SessionStart bootstrap**

inject context：
- 列 `tasks/` 下 `status: in_progress` 或 `status: checkpoint` 的 Task Card 摘要
- 簡述 PERMISSIONS.yaml deny list 與本次 session 可用 hook 範圍
- web 環境提示（fs ephemeral）

**建議 H4（P2，須另開卡 → `20260526-O04`）：UserPromptSubmit 提醒**

簡單腳本：若使用者 prompt 包含「執行」「跑」「做」等動詞，且當前無 in_progress 的 Task Card → 印提示「依硬規則 1，請先建立 Task Card」。可選擇性開啟（噪音管理）。

**建議 H5（P1，順手可做 — 報告附 patch 建議）：補 PERMISSIONS.yaml 的 git_force_push**

`scripts/permissions_guard.py` 已實作但 PERMISSIONS.yaml 未列。yaml 片段：

```yaml
deny:
  # ... 現有 8 條 ...
  - git_force_push           # 對 main/master 的 --force / -f push（permissions_guard 已實作）
```

---

## 4. Subagents + Slash Commands

### 4.1 現況

- `.claude/agents/`：**不存在**
- `.claude/commands/`：**不存在**
- `skills/` 5 個目錄：research 有完整 frontmatter；analysis / ops / review / writing **無 frontmatter**
- `.claude/skills/` 只 symlink 了 research

驗證：

```bash
$ ls .claude/skills/
research -> ../../skills/research
```

→ 原生 Skill 自動載入只覆蓋 1/5。N03 PoC 結論「H1 部分成立」的後續落地未完成。

### 4.2 缺口

| 項目 | 缺口 |
|------|------|
| 4 個 SKILL.md 無 frontmatter | analysis/ops/review/writing 無法被原生 Skills 觸發 |
| 0 個 subagent | 跨任務獨立 context 隔離無法靠原生機制；長對話無法分流 |
| 0 個 slash command | INTAKE_FLOW / RETRO_FLOW / validate_task_card.py 都靠人工呼叫 |

### 4.3 建議

**建議 S1（P0，須另開卡 → `20260526-N12`）：補 4 個 SKILL.md frontmatter**

依 N03 的格式（research 已驗證）。每個 SKILL.md 開頭加：

```yaml
---
name: analysis
description: 一人公司的決策支援 skill — 方案評估、Go/No-Go、策略分析、可行性評估。回答「該怎麼選」。觸發場景：Task Card 的 skill_type 為 analysis，或使用者明確要做多選項比較。輸出規範：結論 → 選項比較表（六維評估）→ 高風險假設 → 待驗證 → 建議下一步。
---
```

description 措辭依 N03 觀察「越具體路由越準」。同步建立 `.claude/skills/{analysis,ops,review,writing}` 4 個 symlink（與 research 同模式，避免雙寫漂移）。risk_level: low（純加 frontmatter，不改原 markdown）。

**建議 S2（P1，須另開卡 → `20260526-N13`）：5 個 subagent 落地**

對映表：

| Task Card skill_type | .claude/agents/[name].md | 主要 tools（對齊 PERMISSIONS.yaml allow）|
|----------------------|--------------------------|------------------------------------------|
| research | research.md | Read, Glob, Grep, WebSearch, WebFetch |
| analysis | analysis.md | Read, Glob, Grep（不需 web）|
| ops | ops.md | Read, Glob, Grep, Edit, Write, Bash（Bash 受 PreToolUse 攔截）|
| review | review.md | Read, Glob, Grep |
| writing | writing.md | Read, Glob, Grep, Write |

每個 agent frontmatter 草案：

```yaml
---
name: research
description: 一人公司研究分析子代理。在獨立 context 中執行資料調查、產業分析、競品研究、技術評估、事實查核。觸發：Task Card skill_type=research，或使用者請求調查/比較/盤點。
tools: Read, Glob, Grep, WebSearch, WebFetch
---

[正文沿用 skills/research/SKILL.md 的執行流程與輸出格式]
```

關鍵設計：tools 白名單明列（不繼承），對齊 `PERMISSIONS.yaml` 的 allow 清單。對應 `allowed_tools` 在 Task Card 的設計，做雙重保險。

**建議 S3（P0，須另開卡 → `20260526-O05`）：3 條核心 slash commands**

| Command | argument-hint | allowed-tools | 用途 |
|---------|---------------|---------------|------|
| `/task-new` | `<goal description>` | Write, Read | 從 TASK_CARD_TEMPLATE.yaml 產草稿，自動填 task_id 與 date |
| `/task-validate` | `<task_card_path>` | Bash | wrap `python3 system/validate_task_card.py $1`，輸出簡潔結果 |
| `/gate-check` | `<task_id>` | Read, Bash | 跑 GATE_POLICY 四層 self-check：schema → rule（檢查 tools 是否在白名單）→ completion（DoD 對照）→ risk（檔案位置確認）|

Slash command 檔案結構（範例 `/task-new`）：

```markdown
---
description: 從 TASK_CARD_TEMPLATE.yaml 建立新的 Task Card 草稿
argument-hint: <goal 一句話描述>
allowed-tools: Write, Read
---

請依以下步驟：
1. Read tasks/TASK_CARD_TEMPLATE.yaml
2. 用今天日期計算 task_id (YYYYMMDD-A01)，檔名 (YYYY-MM-DD_簡述.yaml)
3. 填入 goal: $ARGUMENTS
4. 將其他欄位以 [TODO] 標記
5. Write 到 tasks/<檔名>.yaml
6. 提醒使用者跑 /task-validate
```

**建議 S4（P2，須另開卡 → `20260526-O06`）：擴充 slash commands**

候選：`/checkpoint`（git commit checkpoint 簡化）、`/retro <task_id>`（依 RETRO_FLOW.md 產退一步檢討）、`/audit-log`（手動追加 audit log，過渡期用，等 H2 hook 落地後棄用）。視 S3 落地後使用頻率決定優先級。

---

## 5. MCP 與外部整合

### 5.1 現況

- 專案內：**0 個 MCP 設定**（無 `.mcp.json`、無 settings.json mcpServers 段）
- 本 session 由 Claude Code on the web 預載：**40+ 個 `mcp__github__*` 工具**（涵蓋 PR、Issue、Commit、Branch、Search、Repository 等讀寫操作）+ 1 個 PR webhook 訂閱機制（`subscribe_pr_activity`）

`PERMISSIONS.yaml` 的 allow/ask/deny 三層完全沒涵蓋 `mcp_*`：

```yaml
# 目前 deny 清單（節錄）
deny:
  - send_email             # 但 mcp__github__create_pull_request、merge_pull_request 等高風險動作未分類
  - send_message_external  # mcp__github__add_issue_comment 算嗎？目前無規則
```

### 5.2 缺口

| 缺口 | 影響 |
|------|------|
| 無 mcp_* 規則 | `permissions_guard.py` 無法判定 mcp 工具的審批等級 |
| 無 PR/Issue 寫入規則 | merge_pull_request、push_files、create_pull_request 應落 ask（high risk）但目前無規則攔截 |
| 無 commit 規則 | webhook 訂閱（subscribe_pr_activity）的 token 成本未受 cost policy 控管 |

### 5.3 建議

**建議 M1（P0，順手可做 — 報告附 patch 建議）：PERMISSIONS.yaml 新增 mcp 分類**

```yaml
permissions:
  allow:
    # ... 現有 9 條 ...
    - mcp_github_read      # search_*, list_*, get_*, pull_request_read（含 issue_read）

  ask:
    # ... 現有 6 條 ...
    - mcp_github_write_comment   # add_issue_comment, add_reply_to_pr_comment, add_comment_to_pending_review
    - mcp_github_write_pr        # create_pull_request, update_pull_request, pull_request_review_write
    - mcp_github_write_file      # create_or_update_file, push_files

  deny:
    # ... 現有 8 條 ...
    - mcp_github_merge           # merge_pull_request, enable_pr_auto_merge
    - mcp_github_delete          # delete_file
    - mcp_github_force_branch    # fork_repository, create_branch on protected refs
```

**建議 M2（P1，須另開卡 → `20260526-O07`）：permissions_guard.py 擴充 MCP 攔截**

當前 `permissions_guard.py` 只攔 Bash（`if tool_name not in ("Bash", "bash", "")`）。擴充：
- 偵測 `tool_name.startswith("mcp__github__")` → 對照 M1 的 deny 清單
- ask 等級的 mcp 工具：印警告但 decision=allow（讓 Claude Code 原生 permission prompt 接手）

**建議 M3（P2，須另開卡 → `20260527-O08`）：cost policy 納入 mcp 工具**

`system/COST_POLICY.md` 補充：mcp__github__list_* / search_* 每次呼叫的預估 token 範圍，與單一 Task Card 累計上限。

---

## 6. Claude Code on the web

### 6.1 環境差異（5 項，從本 session 觀察）

| 差異項 | 本地 CLI | Web | 影響專案 |
|--------|---------|-----|---------|
| Filesystem 持久性 | 持久 | **Ephemeral**（session 結束回收） | 「git commit checkpoint」變成「git commit + push」否則丟失 |
| Background process | 可（PERMISSIONS deny 已禁） | 受限（PERMISSIONS deny 相符） | 一致，無需調整 |
| MCP servers | 使用者自配 | **預載**（GitHub 等） | PERMISSIONS.yaml 需涵蓋（見 §5）|
| Settings 來源 | `~/.claude/` + 專案 `.claude/` | 容器啟動時注入（環境變數 / 預設） | SessionStart hook 行為可能不同 |
| Network policy | 預設全開 | **由 environment 策略控管** | web_search / WebFetch 可能受限，須 Task Card 預先評估 |

### 6.2 缺口

- CLAUDE.md 完全沒提 web 環境特性。所有規則隱含「本地 CLI 假設」
- 「git commit checkpoint」在 web 必須改成「commit + push 才算 checkpoint」，否則 session 重啟全丟
- PostToolUse hook（建議 H1）在 web 是否觸發 — 未驗證
- Plugin / SessionStart hook 在 web 的注入時機 — 未驗證

### 6.3 建議

**建議 W1（P0，順手可做 — 報告附 patch 建議）：CLAUDE.md 加 web 段落**

在「執行流程」章節之後加：

```markdown
## Web 環境特性（Claude Code on the web）

- Filesystem ephemeral：checkpoint 必須 commit + push，否則 session 結束丟失
- MCP 預載：GitHub MCP 工具自動可用，依 PERMISSIONS.yaml 的 mcp_* 分類審批
- Network policy 受環境控管：web_search 可能不可用，Task Card 需備援
- Hook 觸發行為與本地 CLI 可能不同（待 N12 系列驗證）
```

**建議 W2（P1，須另開卡 → `20260528-N14`）：web 環境 hook 行為驗證 PoC**

在 web session 中跑 H1/H2/H3 hook 草案，逐個記錄是否觸發、payload 結構是否一致。輸出供 H1-H3 落地卡參考。

**建議 W3（P2，順手可做 — 報告附 patch 建議）：NATIVE_OVERLAP.yaml revisit_trigger 加 web**

```yaml
revisit_trigger: "每季度；或 Claude Code 主版本升級時；或 Claude Code on the web 環境策略變更時"
```

---

## 7. 後續行動分流

### 7.1 順手可做（本報告附 patch 建議，不執行）

| ID | 修改 | Patch 位置 |
|----|------|------------|
| QW1 | `PERMISSIONS.yaml` 新增 `git_force_push` deny | §3.3 建議 H5 |
| QW2 | `PERMISSIONS.yaml` 新增 mcp_github_* 5 條分類 | §5.3 建議 M1 |
| QW3 | `CLAUDE.md` 加「Web 環境特性」段落 | §6.3 建議 W1 |
| QW4 | `NATIVE_OVERLAP.yaml` revisit_trigger 加 web | §6.3 建議 W3 |
| QW5 | `NATIVE_OVERLAP.yaml` 新增 4 個模組欄位（hooks_advanced / subagents_slash / mcp / web）並重算 aggregate | 本報告 §1 結論 |

→ 全部屬 `modify_system_rules` / `modify_claude_md`（ask 等級），需人工確認後執行。建議統一收進一張 follow-up 卡 `20260525-A02` 一次處理。

### 7.2 須另開 Task Card（候選清單，本卡不展開 DoD）

| 候選 task_id | goal | 預估 risk_level | 依賴 |
|--------------|------|-----------------|------|
| 20260526-N12 | 補 4 個 SKILL.md frontmatter + .claude/skills/ symlink | low | 無 |
| 20260526-O01 | PostToolUse hook 落地「連續失敗 3 次停下」 | medium | 無 |
| 20260526-O02 | Stop hook 自動追加 AUDIT_LOG | medium | W2（web 驗證）|
| 20260526-O03 | SessionStart hook context bootstrap | medium | W2 |
| 20260526-O04 | UserPromptSubmit 無 Task Card 提醒 | low | 無 |
| 20260526-N13 | 5 個 .claude/agents/ subagent 落地 | medium | N12 |
| 20260526-O05 | 3 條核心 slash commands（/task-new、/task-validate、/gate-check）| low | 無 |
| 20260526-O06 | 擴充 slash commands（/checkpoint、/retro、/audit-log）| low | O05 |
| 20260526-O07 | permissions_guard.py 擴充 MCP 攔截 | medium | M1 patch 落地 |
| 20260527-O08 | COST_POLICY 納入 mcp 工具 | low | M1 落地 |
| 20260528-N14 | web 環境 hook 行為驗證 PoC | medium | 無 |

**建議執行順序：** N12 → O05 → M1 patch（QW2）→ O01 → W2/N14 → O02/O03 → N13 → 其餘。

---

## 8. Gate Policy 四層自檢

依 `system/GATE_POLICY.yaml`：

### Schema gate
- ✅ Task Card `20260525-A01` 通過 `python3 system/validate_task_card.py`（commit `b594b15`）
- ✅ task_id 格式 `YYYYMMDD-A01`、skill_type=analysis、risk_level=high、allowed_tools 非空

### Rule gate
- ✅ 使用工具皆在 allowed_tools 白名單（file_read、file_search、write_drafts、git_commit_checkpoint）
- ✅ 動作不在 deny 清單（無 delete、無外發、無 production data 修改）
- ✅ approval_needed=true 已標明，待人工確認
- ✅ 0 輪 web search（max_web_searches: 0 已遵守）
- ⏳ 工具呼叫超過 5 次的 checkpoint 已做（Task Card 建立後 commit `b594b15`，報告完成後將再 commit）

### Completion gate（10 條 DoD 對照）

| # | DoD 條目 | 狀態 | 引用章節 |
|---|---------|------|---------|
| 1 | 4 大維度 × 三段（現況→缺口→建議）| **pass** | §3-6 各章 |
| 2 | 每條建議標 P0/P1/P2 + 順手 vs 另開卡 | **pass** | §3.3, §4.3, §5.3, §6.3, §7 |
| 3 | Hooks 章節 4 個 hook matcher + 對應硬規則 | **pass** | §3.3 H1-H5 |
| 4 | 5 個 .claude/agents/ frontmatter 草案 + tools 對齊 PERMISSIONS | **pass** | §4.3 S2 表 + 範例 |
| 5 | 3 條 slash commands + argument-hint + allowed-tools | **pass** | §4.3 S3 表 + 範例 |
| 6 | MCP 章節清點 + mcp_github_read/write + merge/push_files 分類 | **pass** | §5.1, §5.3 M1 |
| 7 | Web 5 項環境差異 + 「失敗 3 次停下」評估 | **pass** | §6.1 表 + §6.2 |
| 8 | 末尾分流表（順手 vs 另開卡 5 + 11 條）| **pass** | §7.1, §7.2 |
| 9 | 檔案在 outputs/drafts/ + 首頁標 risk_level/status/requires_human_review | **pass** | 本檔頂部 |
| 10 | Gate Policy 四層自檢表（pass/fail/partial + 引用）| **pass** | 本節 |

→ **Completion gate: 10/10 pass**

### Risk gate
- ✅ 檔案位置：`outputs/drafts/`（非 `reports/`）
- ✅ 首頁明標 `risk_level: high, status: draft, requires_human_review: true`
- ✅ 所有建議未直接落地任何 `system/` 或 `.claude/` 修改
- ✅ 報告本身 risk_escalated: false（風險預期內，未發生未預期的高風險動作）

→ **Risk gate: pass**

---

## 9. 已知事實 / 合理推論 / 待驗證 / 高風險假設

**已知事實：**
- 5 個 SKILL.md 中只有 research 有 frontmatter（讀檔驗證）
- `.claude/skills/` 只 symlink research（`ls -la` 驗證）
- `permissions_guard.py` 實作 5 條 deny 但 PERMISSIONS.yaml deny 清單漂移 1 條（`git_force_push` 未列）
- 本 session 自帶 40+ 個 `mcp__github__*` 工具（從 deferred tool 列表觀察）

**合理推論：**
- PostToolUse hook 在 web 環境應該會觸發（無證據不會，但無實測）
- subagent + slash command 落地後可減少 INTAKE_FLOW / RETRO_FLOW 的人工執行成本

**待驗證：**
- Stop hook 在 web session 是否觸發（→ W2 PoC）
- SessionStart hook 在 web 的注入時機（→ W2 PoC）
- M1 提案的 mcp 分類粒度是否合適（讀寫分組 vs 細分 PR/Issue/File）— 待 O07 落地時觀察

**高風險假設：**
- Claude Code 在 2026-05 後無破壞性更新 — 若有，本報告所有 hook/skill/MCP 格式建議需重評
- web 環境 GitHub MCP 工具集在不同 session 一致 — 若不一致，PERMISSIONS 規則需用萬用字元 `mcp__github__*` 而非逐條列舉

---

## 附錄 A：報告 metadata

- 撰寫工具呼叫次數：報告完成時填入（< max_tool_calls 25）
- Web search 次數：0
- Checkpoint：`b594b15`（Task Card 建立）+ 報告完成後 1 個
- 下一步：等使用者審閱 → 決定是否同意 QW1-QW5 順手 patch + 同意拆 11 張 follow-up 卡
