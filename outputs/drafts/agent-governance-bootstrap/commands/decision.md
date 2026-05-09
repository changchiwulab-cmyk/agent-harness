---
name: decision
description: Create or list structured Decision Log YAML entries matching schemas/decision_log.schema.yaml.
---

# /decision

## Usage
- `/decision new <slug>` — bootstrap `decisions/YYYYMMDD-D###_<slug>.yaml`. Auto-increments D###.
- `/decision list [--unresolved]` — list decisions, optionally those with `revisit_trigger` not yet fired.
- `/decision revisit <D###>` — re-open and stub a follow-up Task Card.

## Input
- `<slug>`: kebab-case (new)
- `<D###>`: existing decision id (revisit)

## Output
- `new`: writes one file with `decision_date`, `options_considered: []`, `decision`, `rationale`, `revisit_trigger` fields stubbed.
- `list`: table of `id | date | decision | risk | revisit_trigger`.
- `revisit`: prints suggested Task Card stub; does not write.

## Side effects
- `new`: writes one file under `memory/active_projects/<project>/decisions/`.
- `list`, `revisit`: read-only (revisit may surface a Task Card draft to stdout).

## Errors
- Duplicate D### → exit 1.
- `revisit_trigger` empty → exit 2 with hint that decisions without trigger are anti-pattern.

## Contract
Schema: `schemas/decision_log.schema.yaml` (4 required fields: decision_date / decision / rationale / revisit_trigger)
