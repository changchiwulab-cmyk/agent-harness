# agent-governance

Governance layer for [Claude Code](https://claude.com/claude-code): Task Card contracts, Audit Log, Decision Log, Gate Policy, Failure Taxonomy.

License: Apache-2.0

> **Status: v0.1.0 (skeleton bootstrap)**
>
> This repo was bootstrapped from `outputs/drafts/agent-governance-bootstrap/`
> in [`agent-harness`](https://github.com/changchiwulab-cmyk/agent-harness)
> (PR #69, Decision Log D007). agent-harness is the reference implementation.

## What this gives you

- **Task Card contract**: every task starts with `goal` + `definition_of_done`. Run via `/task-card`.
- **Audit Log generator**: per-task structured record (model, tools, tokens, gate results).
- **Decision Log**: structured YAML for cross-session decisions with `revisit_trigger`.
- **Gate Policy**: 4-stage validation (schema → rule → completion → risk).
- **Failure Taxonomy**: 14 failure modes mapped to mitigations.

## Quick start (≤5 steps)

1. `git clone https://github.com/<org>/agent-governance ~/.claude/plugins/agent-governance`
2. Add `"plugins": ["agent-governance"]` to your `.claude/settings.json`
3. Copy `schemas/task_card.schema.yaml` reference into your repo (or import via plugin schemas)
4. Run `/task-card new` to bootstrap your first Task Card
5. Run `/gate-check` after each task to walk the 4-stage validation

## What this does not do

- No replacement for Claude Code Skills (routing) — handled natively
- No replacement for Claude Code permissions (`.claude/settings.json`) — plugin only adds the `risk_level` dimension
- No long-term memory ingestion — use Claude Code's native Memory
- No cost dashboard or auto-retro generation — out of v3.0 scope

## Compatibility matrix

| plugin | claude-code | tested |
|--------|-------------|--------|
| 0.1.0  | >=0.x       | manual smoke only |

## Layout

```
agent-governance/
├── plugin.json
├── README.md
├── LICENSE
├── CHANGELOG.md
├── commands/         # 5 slash commands (.md spec files)
├── schemas/          # 4 YAML schemas
├── hooks/            # 2 Python hooks + tests
├── validators/       # 2 standalone CLI validators + tests
└── .github/
    └── workflows/
        └── ci.yml
```

## Development

```bash
# Run all tests (hooks + validators)
python -m unittest discover -s . -p "test_*.py"
```

CI runs the same on every PR.

## Reference

- Design skeleton: `outputs/drafts/2026-05-09_n04_governance-plugin-skeleton.md` in agent-harness
- Bootstrap decision: `memory/active_projects/agent-harness/decisions/20260509-D007_*.yaml` in agent-harness
- v3 extraction plan: `outputs/drafts/2026-05-09_v3_extraction_plan.md` in agent-harness
