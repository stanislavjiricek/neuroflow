---
title: /doctor
---

# `/neuroflow:doctor`

**A health check of the setup around a neuroflow project: tools, backups, storage location, contracts — and whether
the neuroflow mod is live.**

---

## What it checks

| Check | Why it matters |
|---|---|
| Python 3.10+, git, Claude Code version | neuroflow's scripts and the mod need them |
| git repository, remote, unpushed commits, last commit age | project memory that exists on one disk only is one disk failure from lost |
| uncommitted changes under `.neuroflow/` | the same, for today's work |
| network share or cloud-synced folder | sync and shares corrupt or duplicate files written mid-sync |
| `project_config.md` frontmatter and `nf_schema` | the mod and the scripts read the current contract |
| `.gitignore` and `.gitattributes` | local-only files stay out of git; append-only logs merge cleanly |
| your flowie, if set up: unpushed commits, failures in `~/.neuroflow/flowie-sync.log` (count and first timestamp) | changes that never reached your private repo exist on this machine only — [`/flowie --sync`](flowie.md) resolves both; nothing is reported without flowie |

## Is the mod live?

When the [neuroflow mod](../concepts/mods.md) is running, it answers `/neuroflow:doctor` itself, instantly: the first
lines name its settings and any feature that could not run. If the answer comes from the model instead, the mod is not
live in that session — the report says so.

The same checks run either way, from one script: `skills/neuroflow-core/scripts/doctor.py` (`--json` for machine
output; exit 0 all good, 1 warnings, 2 could not run).

## Related

- [`/sentinel`](sentinel.md) — consistency of the project memory itself
- [`/migrate`](migrate.md) — bring a project to the current contracts
