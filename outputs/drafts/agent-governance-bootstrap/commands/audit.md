---
name: audit
description: Append a structured audit entry to logs/AUDIT_LOG.md or regenerate the auto-managed section from task cards + git checkpoints.
---

# /audit

## Usage
- `/audit append <task_id>` — interactively append one entry for `<task_id>`.
- `/audit regenerate` — rebuild the `AUTO_AUDIT_BEGIN/END` section from `tasks/*.yaml` + `git log --grep="checkpoint: <task_id>"`. Manual notes preserved.
- `/audit check` — run `validators/check_audit_format.py` against `logs/AUDIT_LOG.md`.

## Input
- `<task_id>` matching `^\d{8}-[A-Z0-9]+$` (regenerate / append)
- `logs/AUDIT_LOG.md` (auto-detected at repo root)

## Output
- `append`: pre-filled YAML block printed; user confirms before file write.
- `regenerate`: in-place file rewrite between `AUTO_AUDIT_BEGIN/END` markers. If markers absent, preserve existing body verbatim (regression-tested).
- `check`: pass / fail summary; exit 0 / 2.

## Side effects
- `append`, `regenerate`: write to `logs/AUDIT_LOG.md`. Never deletes manual notes.
- `check`: read-only.

## Errors
- Missing `logs/AUDIT_LOG.md` → create with template, warn.
- Task ID without checkpoint → leave `checkpoints: 0`, do not invent commits.
- Manual notes contain `AUTO_AUDIT_BEGIN` token → fail; ask user to rename.

## Contract
- Schema: `schemas/execution_log.schema.yaml`
- Format check: `validators/check_audit_format.py`
