# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] — 2026-05-09 (skeleton bootstrap)

### Added
- `plugin.json` manifest with 5 commands / 4 schemas / 2 hooks / 2 validators registered.
- 5 slash command interface specs: `/task-card`, `/audit`, `/decision`, `/run-log`, `/gate-check`.
- 4 YAML schemas: `task_card`, `decision_log`, `execution_log`, `failure_taxonomy`.
- 2 hooks: `pre_tool_use.py` (deny-list runtime guard, ported from agent-harness Phase A) and `post_task_use.py` (post-task gate-check trigger stub).
- 2 standalone CLI validators: `validate_task_card.py` (ported from agent-harness `system/validate_task_card.py`) and `check_audit_format.py` (new).
- Apache-2.0 license.
- CI workflow: hooks tests + validators tests on every push.

### Notes
- This is a private bootstrap. Expect API changes in 0.2.x as it's exercised against agent-harness.
- agent-harness will continue to host its own copies of these files until 0.2.x stabilizes; see `outputs/drafts/2026-05-09_v3_extraction_plan.md` §6 for the migration path.
