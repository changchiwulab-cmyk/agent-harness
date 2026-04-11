# Project Context: Agent Harness v1

## 專案目標
建立一人公司可控的 Agent 作業系統，讓 Claude 在可控範圍內穩定完成任務。
核心價值：可復原、可審計、可量化。

## 架構
三平面十一模組：
- **控制平面**：Interface（Claude Code CLI）、Task Card、Planner/Router
- **執行平面**：Context Manager、Skill Executor、Tool Executor、Verifier、Checkpoint
- **治理平面**：Permission、Cost Policy、Audit Log

## 目前狀態（2026-04-04）
- v1 框架完成，所有檔案到位
- 尚未執行任何真實任務
- Rollout Week 1 階段：驗證 research→review pipeline

## 限制與邊界
- 單一核心 agent，不做 multi-agent swarm
- 不自動擴展長期記憶
- 不做自動對外發送（email/社群）
- 不做自動 shell 執行

## 關鍵決策紀錄
- 2026-04-03：選擇 Task Card + git checkpoint 模式，而非 database
- 2026-04-03：v1 用粗略護欄 + 事後量測，不做即時 token 追蹤
- 2026-04-04：完成首次專案檢查，修正 HIGH/MEDIUM priority 缺漏
