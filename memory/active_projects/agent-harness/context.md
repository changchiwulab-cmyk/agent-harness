# Project Context: Agent Harness v2

## 專案目標
建立一人公司可控的 Agent 作業系統，讓 Claude 在可控範圍內穩定完成任務。
核心價值：可復原、可審計、可量化。

## 架構
三平面十六模組：

**控制平面**
- Interface（Claude Code CLI）
- Task Card（tasks/*.yaml）
- Planner/Router（system/ROUTING_RULES.md）
- Decision Log（tasks/DECISION_LOG_TEMPLATE.yaml）

**執行平面**
- Context Manager（CLAUDE.md）
- Skill Executor（skills/[type]/SKILL.md + eval_examples.md）
- Tool Executor（allowed_tools 白名單）
- Gate Verifier（system/GATE_POLICY.yaml）
- Checkpoint（git commit）

**治理平面**
- Agent Context（system/AGENT_CONTEXT.yaml）
- Permission（system/PERMISSIONS.yaml）
- Approval Policy（system/APPROVAL_POLICY.yaml）
- Cost Policy（system/COST_POLICY.md）
- Failure Taxonomy（system/FAILURE_TAXONOMY.yaml）
- Execution Log（system/EXECUTION_LOG_SCHEMA.yaml）
- Audit Log（logs/AUDIT_LOG.md）

## 目前狀態（2026-06-09）
- v2 框架成熟運行；R1–R8 強化系列已落地：
  - R1 approval-record schema、R2 logs schema lint（CI）、R3 analysis cost sample、
    R4 decision-revisit tracker、R5 failure drill（e2e）、R6 execution-log token source、
    R7 observability metrics + frontend overview panel、R8 disaster-recovery runbook。
- 規模：tasks/ 下 45 張 Task Card；7 筆 decision log（D001–D007）；outputs/ 含多份 drafts + 3 份 reports。
- 自動化護欄：
  - `.github/workflows/spec-consistency.yml`（CI 跑 13 道檢查：schema、YAML parse、context budget、
    frontend drift、permissions guard、audit-log generator、e2e smoke + failure drill、decision-revisit）。
  - `scripts/permissions_guard.py`（PreToolUse deny-list hook）、`scripts/governance_metrics.py`
    （plan §5.3 M1–M4 指標引擎）、`scripts/generate_audit_log.py`、`scripts/generate_frontend_manifest.py`。
  - 本地前端看板 `frontend/`（資料源 `frontend/data.json`，CI 驗漂移）。
- 2026-06-09 優化（task 20260609-001）：硬化三條硬規則（`task_card_guard.py` + `failure_counter.py`）、
  自動化 GATE_POLICY 剩餘三層（`gate_check.py`），並校正本檔等文件漂移。

## 策略方向（D-level）
- 已選定 **Route 2 + Route 3 並行**（見 plan `ai-bubbly-mountain.md` §8）：
  - Route 2：把治理三件（Audit / Decision Log / definition_of_done / Failure Taxonomy）抽成
    可獨立安裝的 Claude Code plugin（`agent-governance`）。
  - Route 3：把沉澱的治理思想寫成方法論內容資產。
- v3 `agent-governance` 插件已在 `outputs/drafts/agent-governance-bootstrap/` 完整 staged，
  但**建 repo 延至專屬 session**（D007；本類 session GitHub 範圍受限）。

## Skill 類型
- research：資料蒐集與分析
- analysis：決策支援與策略分析
- writing：內容產出
- ops：營運操作
- review：品質審查

## 限制與邊界
- 單一核心 agent，不做 multi-agent swarm
- 不自動擴展長期記憶
- 不做自動對外發送（email/社群）
- 不做自動 shell 執行

## 關鍵決策紀錄
- 2026-04-03（D001）：選擇 Task Card + git checkpoint 模式，而非 database
- 2026-04-03（D002）：v1 用粗略護欄 + 事後量測，不做即時 token 追蹤
- 2026-04-04：完成首次專案檢查，修正 HIGH/MEDIUM priority 缺漏
- 2026-04-09：v2 系統全流程驗證通過，補正 FAILURE_TAXONOMY 至 14 種
- 2026-04-15（D003）：v3 升級暫緩；（D004）create-task-card 提升為 allow；（D005）intake fast-path
- 2026-04-24（D006）：execution log 範圍收斂（僅 failed/partial/high-risk/checkpoints≥3）
- 2026-05-09（D007）：v3 plugin bootstrap 決策（命名 agent-governance / Apache-2.0 / private / 獨立 repo）
- 2026-06-09（D008）：硬化三條硬規則 + 自動化 GATE 剩餘三層（task 20260609-001）
