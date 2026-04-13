# Project Context: Agent Harness v2.0

## 專案目標
建立一人公司可控的 Agent 作業系統，讓 Claude 在可控範圍內穩定完成任務。
核心價值：可復原、可審計、可量化。

## 架構
三平面十六模組：
- **控制平面**：Interface（Claude Code CLI）、Task Card、Planner/Router
- **執行平面**：Context Manager、Skill Executor、Tool Executor、Verifier、Checkpoint
- **治理平面**：Permission、Cost Policy、Audit Log、Approval Policy、Failure Taxonomy、Gate Policy、Execution Log、Rollback

## Skill 清單（5 種）
- research：資料調查、市場分析、事實查核
- writing：提案寫作、報告輸出、內容規劃
- ops：資料整理、排程規劃、流程文件
- review：品質審查、邏輯驗證、風險評估
- analysis：決策支援、方案評估、可行性分析

## 目前狀態（2026-04-13）
- v2.0 框架完成，系統驗證通過（20260409-001）
- v2.0 新增組件：APPROVAL_POLICY、FAILURE_TAXONOMY（14 種）、GATE_POLICY（四層）、EXECUTION_LOG_SCHEMA、Rollback 定義
- 已完成任務：8 個（含 Week 1 research→review pipeline 驗證 + v2.0 全流程驗證）
- CI 測試：spec-consistency + task-card-skill-type 兩個 workflow

## 限制與邊界
- 單一核心 agent，不做 multi-agent swarm
- 不自動擴展長期記憶
- 不做自動對外發送（email/社群）
- 不做自動 shell 執行

## 關鍵決策紀錄
- 2026-04-03：選擇 Task Card + git checkpoint 模式，而非 database
- 2026-04-03：v1 用粗略護欄 + 事後量測，不做即時 token 追蹤
- 2026-04-04：完成首次專案檢查，修正 HIGH/MEDIUM priority 缺漏
- 2026-04-09：v2.0 驗證完成，補正 FAILURE_TAXONOMY SEC-04（幻覺驅動行動）
