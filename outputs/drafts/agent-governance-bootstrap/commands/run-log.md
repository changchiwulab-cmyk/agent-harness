---
name: run-log
description: Manage per-task execution logs in logs/runs/ matching schemas/execution_log.schema.yaml.
---

# /run-log

## Usage
- `/run-log start <task_id>` — create `logs/runs/RUN-YYYYMMDD-<task_id>.yaml` with `status: started`.
- `/run-log finish <task_id> [--status done|partial|failed]` — fill `completion_time`, `actual_tool_calls`, `gate_results`.
- `/run-log show <task_id>` — print log content.

## Input
- `<task_id>` (`^\d{8}-[A-Z0-9]+$`)

## Output
- `start`: writes one file with `task_id`, `started_at` ISO timestamp.
- `finish`: in-place update; never overwrites existing fields silently — reports diff first.
- `show`: stdout YAML.

## Side effects
- `start`, `finish`: writes to `logs/runs/`.
- `show`: read-only.

## Errors
- Run already started → `start` exits 1.
- Run not found → `finish` / `show` exit 2.

## Contract
Schema: `schemas/execution_log.schema.yaml` (fields: task_id / started_at / completion_time / status / actual_tool_calls / gate_results / approvals / checkpoints).

## Scope
narrow per agent-harness D006: do not auto-write run logs for low-risk tasks; explicit `start` required.
