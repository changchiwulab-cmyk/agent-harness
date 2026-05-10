# Agent Governance Plugin — Manifest Skeleton

- Task: `20260509-N04`
- Date: 2026-05-09
- Skill: writing
- Status: draft（risk_level=low）
- 上游：A01 §5.2 plugin 邊界、N3 PoC（驗證 H1 部分成立）

> **範圍**：本文件是 **設計** skeleton，不是實作。產出每個元件的「介面契約 + 行為規範」，以便日後 `agent-governance/` 獨立 repo 建立時有單一事實來源。
>
> **不建立任何新檔案**，只在 `outputs/drafts/` 留下這份設計文件；plugin repo 的真正建置在 v3.0 release 工程才做。

---

## 1. plugin 定位

### 1.1 一句話定位
> **Agent Governance Plugin**：給 Claude Code 用的治理層 — 把 Task Card 契約、Audit Log、Decision Log、Gate Policy、Failure Taxonomy 收成 5 個 slash command + 2 個 hook + 4 個 schema + 2 個 standalone CLI。

### 1.2 不替代什麼
- 不替代原生 Skills（路由）— 由 Claude Code 處理
- 不替代原生 Permissions（settings.json）— 由 Claude Code 處理；plugin 只追加 `risk_level` 維度
- 不替代原生 Memory — 不接管長期記憶
- 不做 cost dashboard、自動 retro 生成、跨 session 排程

### 1.3 與 agent-harness 的關係
- agent-harness 是這個 plugin 的 **reference implementation**
- plugin 自身不引用 `agent-harness/` 任何路徑（解耦）
- agent-harness v3 過渡期會逐步把治理三件遷出，最後只剩 reference 樣本與該 user 的私有 Task Cards / outputs / logs

---

## 2. plugin.json manifest（草案）

```json
{
  "$schema": "https://schemas.anthropic.com/claude-code/plugin-v1.json",
  "name": "agent-governance",
  "version": "0.1.0-skeleton",
  "description": "Agent governance layer for solo founders: Task Card contracts, Audit Log, Decision Log, Gate Policy, Failure Taxonomy.",
  "author": {
    "name": "agent-governance contributors",
    "url": "https://github.com/<org>/agent-governance"
  },
  "license": "MIT",
  "engines": {
    "claude-code": ">=0.x"
  },
  "commands": [
    "commands/task-card.md",
    "commands/audit.md",
    "commands/decision.md",
    "commands/run-log.md",
    "commands/gate-check.md"
  ],
  "skills": [
    "skills/governance/SKILL.md"
  ],
  "hooks": {
    "PreToolUse": "hooks/pre_tool_use.py",
    "PostTaskUse": "hooks/post_task_use.py"
  },
  "schemas": [
    "schemas/task_card.schema.yaml",
    "schemas/decision_log.schema.yaml",
    "schemas/execution_log.schema.yaml",
    "schemas/failure_taxonomy.yaml"
  ],
  "validators": [
    "validators/validate_task_card.py",
    "validators/check_audit_format.py"
  ],
  "config": {
    "tasks_dir": "tasks/",
    "audit_log_path": "logs/AUDIT_LOG.md",
    "decisions_dir": "memory/active_projects/{project}/decisions/",
    "drafts_dir": "outputs/drafts/",
    "reports_dir": "outputs/reports/",
    "runs_dir": "logs/runs/"
  }
}
```

> `engines.claude-code` 採開放下界，等規範穩定後收緊。
>
> `config` 段允許使用者覆寫；plugin 預設以本表為主。

---

## 3. Slash Command 介面契約（5 個）

### 3.1 `/task-card`
- **用法**：`/task-card [簡述]` 或 `/task-card --from <plan-section>`
- **input**：簡述（≤30 字）或既有 plan 段落引用
- **output**：在 `tasks_dir` 建立 `YYYY-MM-DD_<簡述>.yaml`，欄位填到「足以開跑」（goal / DoD ≥1 條 / risk_level / skill_type / allowed_tools / expected_output）
- **副作用**：寫一個新檔；不寫 audit、不 commit
- **錯誤處理**：
  - 簡述為空 → 提示要求簡述
  - 同檔名已存在 → 加上 `-002`、`-003` 後綴遞增
  - DoD 未填 → 必須詢問使用者至少填 1 條才寫檔

### 3.2 `/audit`
- **用法**：`/audit <task_id>` 或 `/audit`（互動模式）
- **input**：task_id（從 `tasks_dir` 自動補完）
- **output**：在 `audit_log_path` 文件頭部 append 一筆 yaml 區塊（依 schema）
- **副作用**：append-only；不修改既有條目
- **錯誤處理**：
  - task_id 對應不到 → 列出近 10 張 Task Card 讓使用者選
  - 必填欄位缺漏 → 互動補欄位
  - audit log 檔不存在 → 拒絕建立（屬使用者環境配置，不自動修復）

### 3.3 `/decision`
- **用法**：`/decision [topic]`
- **input**：決策主題；至少 2 個 options
- **output**：在 `decisions_dir` 建立 `YYYYMMDD-D<###>_<topic>.yaml`，依 DECISION_LOG schema
- **副作用**：寫一個新檔；不寫 audit
- **錯誤處理**：
  - options < 2 → 互動補
  - reasoning 為「感覺」「直覺」等空話 → 警告但不阻斷
  - decision_id 編號衝突 → 取目錄下最大號 +1

### 3.4 `/run-log`（窄範圍）
- **用法**：`/run-log <task_id>`
- **input**：task_id
- **output**：在 `runs_dir` 建立 `RUN-YYYYMMDD-<###>.yaml`，依 EXECUTION_LOG_SCHEMA
- **觸發條件**：僅以下任一情境才寫（呼應 D006）：
  - status = failed
  - status = partial
  - risk_level >= high
  - checkpoints >= 3
- **副作用**：寫一個新檔
- **錯誤處理**：
  - 不符觸發條件 → 提示「此任務未達 run-log 觸發條件，audit 即可」並退出 0
  - 必填欄位缺漏 → 互動補

### 3.5 `/gate-check`
- **用法**：`/gate-check <task_id>` 或 `/gate-check --all-pending`
- **input**：task_id；讀取對應 Task Card 與輸出檔
- **output**：終端列印四層驗證結果，每層 pass/fail；退出碼：0=全 pass、1=某層 fail
- **副作用**：不寫檔（只讀）；可選 `--write-runs` 自動觸發 `/run-log`
- **錯誤處理**：
  - schema_check fail → 立即停下，列差異
  - rule_check fail → 寫 logs/errors/，提示使用者
  - completion_check fail → 列缺漏項，建議移到 drafts/
  - risk_check fail → 鎖到 drafts/、Audit Log 補 risk_escalated: true

---

## 4. Schemas（4 個）

### 4.1 `schemas/task_card.schema.yaml`
**必填**：`task_id` / `date` / `goal` / `definition_of_done` / `risk_level` / `skill_type` / `allowed_tools` / `expected_output`
**選填**：`context` / `input_data` / `approval_needed` / `max_tool_calls` / `max_retries` / `max_web_searches`
**Agent-fill**：`status` / `checkpoints` / `actual_tool_calls` / `result_summary` / `completion_time` / `audit_log_ref`

範例：
```yaml
task_id: "20260601-001"
date: "2026-06-01"
goal: "整理 Q2 客戶聯絡資料為單一 YAML"
definition_of_done:
  - "所有客戶資料合併到一檔，欄位統一"
  - "輸出含變更摘要（新增/合併/跳過筆數）"
risk_level: "low"
skill_type: "ops"
allowed_tools: ["file_read", "file_search"]
expected_output:
  format: "yaml"
  location: "outputs/drafts/"
  filename: "client-contacts-q2.yaml"
```

### 4.2 `schemas/decision_log.schema.yaml`
**必填**：`decision_id` / `date` / `project` / `context` / `options_considered`(≥2) / `decision` / `reasoning` / `status`
**選填**：`risk` / `revisit_trigger` / `related_task`

範例：見 `memory/active_projects/agent-harness/decisions/20260424-D006_execution-log-scope.yaml`（已是符合此 schema 的 reference）。

### 4.3 `schemas/execution_log.schema.yaml`
**必填**：`run_id` / `task_id` / `started_at` / `ended_at` / `status` / `gate_results`
**選填**：`tools_used` / `checkpoints` / `token_estimate` / `approvals` / `output_path` / `error_summary` / `notes`

範例：依 v2 `system/EXECUTION_LOG_SCHEMA.yaml`。

### 4.4 `schemas/failure_taxonomy.yaml`（靜態資料）
14 條失敗模式，依四大類分組：spec / coordination / validation / security。每條：`id`（如 SPEC-01）、`name`、`description`、`mitigation`。

直接 fork v2 `system/FAILURE_TAXONOMY.yaml`，作為 plugin v0.1.0 的 baseline；後續以 PR 方式擴充。

---

## 5. Hooks（2 個）

### 5.1 `hooks/pre_tool_use.py`
- **觸發時機**：Claude Code 每次 tool call 前（matcher: 全部）
- **輸入**：stdin JSON `{"tool_name": "...", "tool_input": {...}}`
- **行為**：
  1. 從 `settings.json` 載入 deny patterns（取代 v2 hardcoded）
  2. 從當前 in-flight Task Card 載入 `allowed_tools`（透過 env var `CC_TASK_CARD_PATH` 或 settings.json 配置）
  3. 若 tool_name 不在 allowed_tools → block，reason: `tool not in task card whitelist: <name>`
  4. 若指令 match deny pattern → block，reason: `matched deny: <rule_id>`
  5. 否則 allow
- **失敗行為**：
  - 配置缺失 → fail-safe **allow**（不破壞既有 workflow），但寫 `logs/errors/` 警告
  - 解析錯誤 → block，reason: `hook config malformed`，並寫 `logs/errors/`
- **退出碼**：0（一律），決定靠 stdout JSON

### 5.2 `hooks/post_task_use.py`
- **觸發時機**：Task 結束（透過 plugin 自定義事件 `PostTaskUse`，或 `/gate-check` 完成的後置 hook）
- **行為**：
  1. 自動跑 `/gate-check <task_id>`
  2. 若所有 gate pass → 寫 audit log
  3. 若 risk >= high or checkpoints >= 3 → 自動跑 `/run-log`
  4. 任何 fail → 不寫 audit，要求使用者處理
- **失敗行為**：
  - hook 自身崩潰 → 不寫 audit、不阻斷使用者；寫 `logs/errors/<timestamp>_post_task.log`
  - gate fail → 列缺漏，使用者決定下一步

---

## 6. Standalone Validators（2 個 CLI）

### 6.1 `validators/validate_task_card.py`
```
用法：python validate_task_card.py <task-card-path>
退出碼：
  0 = pass
  1 = schema 違反
  2 = 路徑不存在
  3 = YAML 解析錯誤
輸出（stderr）：每個錯誤一行，格式 `[<rule>] <message>`
```
直接 fork v2 `system/validate_task_card.py`，但移除 agent-harness 路徑硬編碼。

### 6.2 `validators/check_audit_format.py`
```
用法：python check_audit_format.py <audit-log-path>
退出碼：
  0 = 全部條目格式正確
  1 = 至少一條格式錯誤
  2 = 路徑不存在
輸出：列出每個錯誤條目的 task_id 與缺漏欄位
```

兩個 validator **不依賴 Claude Code**，可獨立用於 CI 或 git pre-commit hook。

---

## 7. Skill：`skills/governance/SKILL.md`

frontmatter：
```yaml
---
name: governance
description: 一人公司的 agent 治理 skill — 引導使用者建立 Task Card、寫 Audit Log、寫 Decision Log、跑 Gate Check。觸發場景：使用者要開新任務、回顧已完成任務、需要對重要決策留下紀錄。輸出：互動引導使用者填關鍵欄位，最終呼叫對應 slash command。
---
```

正文：簡述治理三原則（可恢復／可審計／可量化）+ 5 個 command 何時用 + 與其他 skill 的關係（governance 不做事實調查、不做撰寫，只做契約簽收）。

---

## 8. README outline

```
agent-governance/
├── 1. 是什麼（一句話定位 §1.1）
├── 2. 它不是什麼（§1.2 — 不替代原生 Skills/Permissions/Memory）
├── 3. Quick Start（≤5 步驟）
│   1. install plugin
│   2. /task-card <簡述>
│   3. 執行 → /gate-check <task_id>
│   4. /audit <task_id>
│   5. （重大決策時）/decision
├── 4. 5 個 Command 速查表
├── 5. 4 個 Schema 速查表
├── 6. 與 agent-harness 的關係
├── 7. 版本兼容矩陣（plugin × Claude Code engine）
├── 8. 治理三原則：可恢復／可審計／可量化（為什麼這 5 個 command 是這 5 個）
├── 9. 設計取捨（不做清單 + 為什麼）
└── 10. 貢獻指南（PR / 失敗模式新增 / schema 演進）
```

---

## 9. v2 模組 → plugin 元件對照

| v2 模組（A01 §4.2 編號） | 裁決 | plugin 元件 | 來源檔案 |
|------|------|------|------|
| #2 Task Card | 重構 | schemas/task_card.schema.yaml + commands/task-card.md | TASK_CARD_TEMPLATE.yaml |
| #4 Decision Log | 抽出 | schemas/decision_log.schema.yaml + commands/decision.md | DECISION_LOG_TEMPLATE.yaml |
| #8 Gate Verifier | 抽出 | commands/gate-check.md + hooks/post_task_use.py | system/GATE_POLICY.yaml |
| #11 Permission | 重構 | hooks/pre_tool_use.py（吃 settings.json + Task Card） | scripts/permissions_guard.py |
| #14 Failure Taxonomy | 抽出 | schemas/failure_taxonomy.yaml（靜態） | system/FAILURE_TAXONOMY.yaml |
| #15 Execution Log | 抽出 | schemas/execution_log.schema.yaml + commands/run-log.md | system/EXECUTION_LOG_SCHEMA.yaml |
| #16 Audit Log | 抽出 | commands/audit.md（append-only） | logs/AUDIT_LOG.md（格式仍以 yaml 區塊為主） |
| #1 Interface | 砍除 | — | （由 Claude Code runtime 提供） |
| #3 Planner/Router | 砍除（保留拆分原則） | — | 拆分原則一句話寫進 plugin README §3 |
| #6 Skill Executor | 砍除 | skills/governance/SKILL.md（**僅** governance skill；其餘 skill 仍由原生承載） | （N3 PoC 驗證可行） |
| #10 Agent Context | 砍除 | — | （內容併回 README） |
| #9 Checkpoint | 砍除 | — | （git commit 是慣例） |
| #7 Tool Executor | 重構 | hooks/pre_tool_use.py 第 2 步 | — |
| #5 Context Manager | 重構 | （非 plugin 範圍）寫進使用者 CLAUDE.md | — |
| #12 Approval Policy | 重構 | commands/* 各自處理 draft_first / human_confirm | — |
| #13 Cost Policy | 重構 | （非 plugin 範圍）使用者保留校準資料 | — |

對照確認：
- 抽出 6（#4 / #8 / #14 / #15 / #16，再加 #2 task card 部分），plugin 全部承載 ✓
- 砍除 5（#1 / #3 / #6 / #10 / #9），plugin 不承載 ✓
- 重構 5（#2 / #11 / #7 / #5 / #12 / #13），其中 4 個進 plugin（#2 / #11 / #7 / #12），2 個留 user 端（#5 / #13）✓

---

## 10. 暫不做清單（plugin v3.0）

| 項目 | 為什麼 |
|------|--------|
| Cost dashboard / token 視覺化 | A01 §1.2 已說明 v2 frontend 是 reference；plugin 應後端中立 |
| 自動 retro 生成 | retro 是人工反思工作，不該被自動化（治理思想第一原則） |
| 跨 session 自動排程 | 違反 v2 AGENT_CONTEXT「cannot_do: 自動排程」 |
| 自動長期記憶寫入 | 違反 v2 AGENT_CONTEXT「cannot_do: 跨 session 自動記憶」 |
| MCP server 形態 | A01 §5.1 已排在 v3.2，先 plugin → CLI → MCP |
| GUI（除 README 內 mermaid 圖）| 一人公司不需要 GUI；CLI + 純文字輸出即可 |
| 多 project 自動切換 | 改由 `config.tasks_dir` 等路徑覆寫處理 |
| AI agent 對 audit log 的自動分析 | 等使用者明確要求；目前是工具，不是 agent |

---

## 11. 風險與限制

- **L1 — `engines.claude-code` 規範未穩定**：plugin manifest 欄位可能變動。緩解：v0.1.0 標 skeleton；正式版前重新對齊規範。
- **L2 — `PostTaskUse` hook 是否原生支援未知** `[待驗證]`：若不支援，post_task_use.py 改由 `/gate-check` 完成後手動觸發。
- **L3 — settings.json 是否可被 plugin 寫入**：需查官方 spec。若不行，plugin 只**讀** settings.json，要求使用者自行設定。
- **R1 — schema 演進破壞向後相容**：策略：v0.x 期間任何 schema 改動都記在 plugin Decision Log；v1.0 凍結後採 semver，schema breaking 一律 major bump。

---

## 12. DoD 驗收

| # | DoD | 狀態 | 段落 |
|---|-----|:-:|------|
| 1 | plugin.json manifest 草案，每段最小範例 | ✅ | §2 |
| 2 | 5 commands 介面契約（用法/input/output/副作用/錯誤）| ✅ | §3 |
| 3 | 4 schema 草案，必填欄位 + 1 範例 | ✅ | §4 |
| 4 | 2 hooks（觸發/行為/失敗行為）| ✅ | §5 |
| 5 | 2 validator（CLI 入口 + 退出碼）| ✅ | §6 |
| 6 | README outline（定位/quick start/解耦/版本矩陣）| ✅ | §8 |
| 7 | v2 → plugin 對照表 | ✅ | §9 |
| 8 | 暫不做清單 | ✅ | §10 |

8/8 通過。

---

## 13. 建議下一步

1. 等 N3 在新 session 驗證自動觸發（research skill 出現在 available-skills）。
2. 把 §2 的 `plugin.json` 跟官方 plugin spec 比對，校正欄位名稱。
3. 起 task card 真正建立 `agent-governance/` 獨立 repo（risk=high，因為涉及 repo 建立與 license 選擇，需人工核准）。
4. plugin v0.1.0-skeleton 用 N3+N4 兩份草稿做 dogfood：在 agent-harness 自身切換到 plugin 跑 1 張 Task Card，記錄差異。
