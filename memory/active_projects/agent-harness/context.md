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

## 目前狀態（2026-04-15）
- v2 框架完成，所有檔案到位
- 已完成 Week 1 pipeline 驗證（research → review → writing → ops）
- 累積 6 筆 audit log 紀錄

## Skill 類型
- research：資料蒐集與分析
- analysis：決策支援與策略分析
- writing：內容產出
- ops：營運操作
- review：品質審查

## 限制與邊界
- 單一指揮官 + 派工模式（2026-07-03 起）：主對話為唯一指揮官，粗活派 subagent，規則見 system/DELEGATION_PLAYBOOK.md；仍不做開放式 multi-agent swarm
- 不自動擴展長期記憶
- 不做自動對外發送（email/社群）
- 不做自動 shell 執行

## 關鍵決策紀錄
- 2026-04-03：選擇 Task Card + git checkpoint 模式，而非 database
- 2026-04-03：v1 用粗略護欄 + 事後量測，不做即時 token 追蹤
- 2026-04-04：完成首次專案檢查，修正 HIGH/MEDIUM priority 缺漏
- 2026-04-09：v2 系統全流程驗證通過，補正 FAILURE_TAXONOMY 至 14 種
