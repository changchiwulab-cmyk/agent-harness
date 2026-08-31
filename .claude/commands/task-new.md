---
description: 由需求生成 Task Card 骨架、驗證 schema、綁定 active task（執行流程步驟 1）
argument-hint: [一句話描述要完成什麼]
allowed-tools: Bash(python3 scripts/active_task.py:*), Bash(python3 system/validate_task_card.py:*), Bash(cp:*), Bash(ls:*), Read, Write, Edit, Glob, Grep
---

# 建立 Task Card

需求：$ARGUMENTS

依 `CLAUDE.md` 執行流程步驟 1–2。**沒有 Task Card 不執行任何任務**（硬規則 1），本指令是唯一入口。

## 步驟

1. **先確認需求夠具體**：若無法從 $ARGUMENTS 推出可驗證的 `definition_of_done`，
   依 `system/INTAKE_FLOW.md` 向使用者釐清，**不要猜**。範圍模糊到無法定義 DoD 時拒絕建卡
   （`system/AGENT_CONTEXT.yaml` boundaries.refuse_when）。

2. **依模板填卡**：以 `tasks/TASK_CARD_TEMPLATE.yaml` 為骨架，寫到
   `tasks/YYYY-MM-DD_<簡述>.yaml`。10 個必填欄位一個都不能少：
   `task_id`（`YYYYMMDD-NNN` 或含字母前綴）／`date`／`status`／`goal`／`definition_of_done`／
   `expected_output`／`risk_level`／`approval_needed`／`skill_type`／`allowed_tools`。

   - `skill_type` 只能是 `system/ROUTING_RULES.md` 的權威清單值；跨兩個 skill 就拆兩張卡。
   - `allowed_tools` 只列這張卡真正需要的——這份白名單由 `scripts/allowed_tools_guard.py`
     在 PreToolUse **當下強制**，列太少會擋住自己，列太多等於沒有白名單。
   - `risk_level` ≥ high 時 `approval_needed` 必須 true，且產出只能落 `outputs/drafts/`。
   - `definition_of_done` 每一條都要能被機器或人一眼判定真假，不要寫「完善」「優化」這類詞。

3. **驗證**：`python3 system/validate_task_card.py tasks/<新卡>.yaml` 必須通過。
   失敗就修卡，**重試上限 1 次**，仍失敗停下問使用者（CLAUDE.md 驗證失敗處理）。

4. **綁定**：`python3 scripts/active_task.py --set <task_id>`。
   這一步是 `task_card_guard.py` 授權新正式報告的前提，漏掉後面會被擋。

5. **checkpoint**：`git commit -m "checkpoint: [<task_id>] 建立 Task Card 並綁定 active task（C0）"`

## 完成後

回報卡片路徑、`task_id`、`skill_type`、DoD 條數，並提示接下來用 `/task-run`。
