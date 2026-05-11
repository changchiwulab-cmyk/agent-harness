---
name: gate-check
description: Run the 4-stage gate (schema → rule → completion → risk) for a Task Card and print verdicts.
---

# /gate-check

## Usage
- `/gate-check <task_id>` — run all 4 gates against `tasks/*<task_id>*.yaml` and the task's expected output.
- `/gate-check <task_id> --gate schema|rule|completion|risk` — run a single gate.

## Input
- `<task_id>` (`^\d{8}-[A-Z0-9]+$`)

## Output
- Markdown table:
  ```
  | gate        | status | detail                  |
  |-------------|:------:|-------------------------|
  | schema      |   ✅   | validate_task_card pass |
  | rule        |   ✅   | allowed_tools ok        |
  | completion  |   ⚠   | DoD #4 not in output    |
  | risk        |   ✅   | output in drafts/       |
  ```
- Exit 0 if all pass, 1 if any warn, 2 if any fail.

## Side effects
- read-only.

## Errors
- Task Card missing → exit 2 with hint.
- Output file referenced in `expected_output.location` not found → completion gate fails with detail.

## Contract
- schema gate: shells `validators/validate_task_card.py`
- rule gate: cross-checks `allowed_tools` against deny patterns from `config/deny_patterns.yaml`
- completion gate: keyword presence of every `definition_of_done` line in produced output (heuristic; LLM-assisted in interactive runtime)
- risk gate: `risk_level >= high` ⇒ output path must contain `outputs/drafts/`

Pinned set of 4 gate names is contractual: `EXPECTED_GATES = {"schema_check", "rule_check", "completion_check", "risk_check"}`. Adding a gate requires a Task Card.
