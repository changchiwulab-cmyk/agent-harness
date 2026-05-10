# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] — pending v0.1.0 tag

### Fixed
- `hooks/post_task_use.py` — `gate_risk` is now always invoked, even when
  `output_path` is None. Previously the `run()` short-circuit returned
  `("n/a", ...)` and bypassed the containment check, so high/critical tasks
  could pass the gate without writing under `outputs/drafts/`.
  (Codex P1 — agent-harness PR #71 review thread r3213314884)
- `hooks/post_task_use.py` — `gate_completion` now type-guards the
  `definition_of_done` list and its items; non-list values and non-string
  entries return a structured `fail` verdict instead of raising `TypeError`.
  (Codex P2 — agent-harness PR #71 review thread r3213314886)

### Added
- 2 regression tests in `hooks/test_hooks.py`
  (`test_risk_gate_fails_high_risk_when_no_output_path`,
  `test_completion_gate_fails_on_non_string_dod_items`).
  Hook test count: 12 → 14 (validators unchanged at 14; total 28).

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
