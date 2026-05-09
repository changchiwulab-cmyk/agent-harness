---
name: task-card
description: Create, validate, or list Task Card YAML files matching schemas/task_card.schema.yaml.
---

# /task-card

## Usage
- `/task-card new <slug>` — bootstrap a new card from `schemas/task_card.schema.yaml`.
- `/task-card validate <path>` — run schema check on an existing card.
- `/task-card list [--status pending|review|done|failed|partial]` — list cards by status.

## Input
- `<slug>` (new): kebab-case stem; produces `tasks/YYYY-MM-DD_<slug>.yaml`
- `<path>` (validate): repo-relative YAML path

## Output
- `new`: writes `tasks/YYYY-MM-DD_<slug>.yaml` with required fields stubbed; prints created path.
- `validate`: prints `✅ pass` or list of schema errors; exit code 0 / 2.
- `list`: prints table of `task_id | status | risk_level | goal`.

## Side effects
- `new`: writes one file. Never overwrites existing.
- `validate`, `list`: read-only.

## Errors
- File exists (new) → exit code 1, no overwrite.
- Schema fail (validate) → exit code 2, structured error list.
- Tasks dir missing → exit code 2 with hint.

## Contract
Matches `validators/validate_task_card.py` exit codes 1:1.
