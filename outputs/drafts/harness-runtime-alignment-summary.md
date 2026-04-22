# Harness Runtime Alignment 遷移摘要

**Task Card**：`tasks/2026-04-20_harness-runtime-alignment.yaml` (`20260420-002`)
**日期**：2026-04-20
**狀態**：已完成（CLAUDE.md 草稿待人工確認）
**執行紀錄**：`logs/runs/20260420-002_harness-runtime-alignment.yaml`
**相關決策**：D006（sub-agent scope）、D007（tool registry closure）

---

## 盤點結論

第一輪（`20260420-001`）處理了「資料層」相容性（模型 ID、MODEL_POLICY、COST_POLICY）。
第二輪由 **兩個並行 Explore sub-agent** 執行深度盤點，專注在「執行層」：工具命名、權限登錄、
runtime 整合、validator 閉包。共 **24 項 finding**：HIGH 5 / MED 7 / LOW 12。

本輪處理 HIGH + MED 共 12 項。LOW 延後下次 retro。

---

## 本輪 HIGH finding 處理對照

| # | Finding | 處理 | commit |
|---|---------|------|--------|
| H1 | 工具命名抽象層與 Claude Code 實際工具無對應 | `system/TOOL_MAPPING.yaml` 新檔：framework snake_case ↔ Claude Code PascalCase / mcp__* 雙向映射 | `bda734d` |
| H2 | Agent / TodoWrite / Skill / ToolSearch / MCP 未在 PERMISSIONS 登錄 | `system/PERMISSIONS.yaml` 擴充：新增 6 個 allow、3 個 ask、2 個 deny；檔頭加閉包規則 | `bda734d` |
| H3 | GitHub MCP 寫入未進 APPROVAL triggers | `system/APPROVAL_POLICY.yaml` 新增 3 條 trigger（github_write / user_skill_invoke / Plan mode）；對外動作 trigger 加 GitHub 範圍註解 | `875a8d7` |
| H4 | sub-agent 使用與 context.md 規則衝突 | D006 精準化「multi-agent swarm」為多 agent 長期協作，允許唯讀 sub-agent；context.md line 49 同步更新 | `bda734d` + `875a8d7` |
| H5 | validator 未做 allowed_tools 詞彙閉包 | D007 + `scripts/check_spec_consistency.rb` 擴充：closure / risk-approval / task_id uniqueness；3 類 fail case 驗證通過 | `b986ce6` |

## 本輪 MED finding 處理對照

| # | Finding | 處理 | commit |
|---|---------|------|--------|
| M1 | AGENT_CONTEXT 自我宣告不全 | can_do / cannot_do 擴充；新增 `runtime_integrations` 區塊（plan_mode / stop_hook / session_start_hook / pr_activity_subscription / auto_compaction / deferred_tools） | `875a8d7` |
| M2 | APPROVAL_POLICY 缺 Plan mode trigger | 已於 H3 處理（draft_first 等價物） | `875a8d7` |
| M3 | research skill 缺 knowledge cutoff 指引 | `skills/research/SKILL.md` 新增「知識截止與 web search 優先順序」段落（Opus 4.7 cutoff = 2026-01） | `875a8d7` |
| M4 | context.md 關鍵決策列表未更新 | 加 D006 / D007 兩行 | `875a8d7` |
| M5 | validator 缺 task_id 全域唯一檢查 | Ruby + Python 兩支 validator 都加上（跨語言互相背書） | `b986ce6` |
| M6 | validator 缺 risk ≥ high → approval 交叉檢查 | Ruby validator 新增此規則 + 3 組失敗案例驗證 | `b986ce6` |
| M7 | CLAUDE.md 執行流程步驟排序 / 缺 TOOL_MAPPING 引用 | 產出 `claude-md-harness-runtime-alignment-diff.md` 4 處建議；待人工確認 | `f57923b` + 本檔 |

---

## 四階段分工

### Phase 1 — 建檔 + PERMISSIONS ✓

| 項目 | 產出 |
|------|------|
| 工具對應表 | `system/TOOL_MAPPING.yaml`（新檔，含正向 framework→CC 與反向 CC→framework 索引） |
| D006 決策 | `memory/.../decisions/20260420-D006_sub-agent-scope.yaml` |
| D007 決策 | `memory/.../decisions/20260420-D007_tool-registry-closure.yaml` |
| PERMISSIONS 擴充 | +6 allow / +3 ask / +2 deny；檔頭加 closure 規則 |
| Task Card 建檔 | `tasks/2026-04-20_harness-runtime-alignment.yaml` |

commit: `bda734d`

### Phase 2 — 規則與 context ✓

| 項目 | 產出 |
|------|------|
| APPROVAL_POLICY 3 條 trigger | github_write→draft_first / user_skill_invoke→human_confirm / Plan mode→draft_first 等價 |
| AGENT_CONTEXT 擴充 | can_do / cannot_do + 新 runtime_integrations 區塊（6 個子項） |
| context.md 更新 | line 49 精修；決策列表加 D006 / D007 |
| research SKILL 更新 | 新增知識截止段落（Opus 4.7 cutoff = 2026-01） |

commit: `875a8d7`

### Phase 3 — Validator ✓

| 項目 | 產出 |
|------|------|
| check_spec_consistency.rb 擴充 | 載入 PERMISSIONS；allowed_tools 閉包；risk/approval 交叉；task_id 唯一 |
| Ruby 測試 | +9 tests（23 runs / 76 assertions / 0 fail） |
| check_task_card_skill_type.py 擴充 | 新增 extract_task_id() + 全域唯一檢查 |
| Python 測試 | +6 tests（19 tests / 0 fail） |
| 失敗案例驗證 | 3 類案例（未登錄工具 / high-risk + no approval / 重複 task_id）皆被 validator 擋下 |

commit: `b986ce6`

### Phase 4 — Draft + 收斂（本階段） ✓

| 項目 | 產出 |
|------|------|
| CLAUDE.md 建議 diff | `outputs/drafts/claude-md-harness-runtime-alignment-diff.md`（4 處建議，3 強烈建議 + 1 選配） |
| 本遷移摘要 | `outputs/drafts/harness-runtime-alignment-summary.md`（本檔） |
| 執行紀錄 | `logs/runs/20260420-002_harness-runtime-alignment.yaml` |
| Audit log | `logs/AUDIT_LOG.md` 新增 20260420-002 entry |

---

## 四層 Gate 驗證結果

| 層 | 結果 | 說明 |
|----|------|------|
| schema_check | pass | ruby + python validator 通過；本 Task Card 的 allowed_tools 已列入 PERMISSIONS（含新 `modify_scripts` ask 權限） |
| rule_check | pass | 所有 ask 級動作（modify_system_rules / modify_skills / write_long_term_memory / modify_scripts）取得人工批准；CLAUDE.md 僅產草稿符合 modify_claude_md ask 級流程 |
| completion_check | pass | DoD 全通過；Phase 1–3 直接修改、Phase 4 按 draft-first 原則 |
| risk_check | pass | risk_level=medium 與實際動作一致；對外動作限草稿；sub-agent 在本任務僅用於第二輪盤點（第一輪已完成），本任務本體未再 spawn sub-agent |

---

## 待人工確認項目

1. **CLAUDE.md 是否套用 `claude-md-harness-runtime-alignment-diff.md` 的建議**
   - 變更 1（執行流程拆 3a / 3b + 載入 TOOL_MAPPING）：強烈建議
   - 變更 2（權限段補 sub-agent 邊界）：強烈建議
   - 變更 3（Context 硬限制補 auto-compaction 說明）：強烈建議
   - 變更 4（三條硬規則後補 Plan mode 註記）：選配
2. **PR review**：本次 Phase 3 的 validator 擴充後，PR review bot 應該看到「0 新 comment」
   才代表閉包規則沒有漏掉既有 Task Card；若仍有 comment，需檢視是否遺漏 PERMISSIONS 登錄。
3. **Sub-agent 策略文件化**：D006 已正式化，下次使用 sub-agent 時 execution log 需記錄
   `tools_used: sub_agent_readonly (Explore)` 取代先前的自由文字。

---

## 檔案清單

**新增**
- `system/TOOL_MAPPING.yaml`
- `memory/active_projects/agent-harness/decisions/20260420-D006_sub-agent-scope.yaml`
- `memory/active_projects/agent-harness/decisions/20260420-D007_tool-registry-closure.yaml`
- `tasks/2026-04-20_harness-runtime-alignment.yaml`
- `logs/runs/20260420-002_harness-runtime-alignment.yaml`
- `outputs/drafts/claude-md-harness-runtime-alignment-diff.md`
- `outputs/drafts/harness-runtime-alignment-summary.md`（本檔）

**修改**
- `system/PERMISSIONS.yaml`（+6 allow / +3 ask / +2 deny + 閉包規則）
- `system/APPROVAL_POLICY.yaml`（+3 trigger）
- `system/AGENT_CONTEXT.yaml`（can_do / cannot_do + runtime_integrations）
- `memory/active_projects/agent-harness/context.md`（line 49 精修 + D006 / D007）
- `skills/research/SKILL.md`（知識截止段落）
- `scripts/check_spec_consistency.rb`（PERMISSIONS 閉包 + risk/approval + task_id unique）
- `scripts/test_check_spec_consistency.rb`（+9 tests）
- `scripts/check_task_card_skill_type.py`（task_id unique）
- `scripts/test_check_task_card_skill_type.py`（+6 tests）
- `logs/AUDIT_LOG.md`（新增 20260420-002 entry）

**未修改（草稿待審）**
- `CLAUDE.md`

---

## 下一步建議

1. 審閱本摘要與 `claude-md-harness-runtime-alignment-diff.md`
2. 若核可 CLAUDE.md 變更 1、2、3，回覆後由 agent 直接套用（本 Task Card scope 內）
3. 下一輪 retro 處理 LOW 項目（context compaction 詳述、execution log timezone、status schema 碎片化註解等 12 項）
4. 觀察 1–2 次使用 `user_skill_invoke` / `github_write` / `sub_agent_readonly` 的真實任務，驗證新 approval triggers 與 D006 邊界在實務上清楚
