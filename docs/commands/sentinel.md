---
title: /sentinel
---

# `/neuroflow:sentinel`

**Full audit of your project — drift detection, broken references, and consistency checks.**

`/sentinel` is a coherence guard. It audits `.neuroflow/` for internal consistency: checks that `flow.md` files match the actual files on disk, re-checks that a frozen preregistration is unchanged, detects drift between phases, and keeps the project config in line with the installed plugin.

---

## When to use it

- Before writing a report or paper — make sure everything is consistent
- When you suspect something is out of sync
- After a git merge or pull — to catch conflict markers and broken logs
- Periodically, as a project health check
- In plugin development mode — to audit the plugin itself

---

## What it does

Claude checks which context it's in and routes to the appropriate agent:

1. If `.claude-plugin/plugin.json` exists → **plugin repo** — invokes the `sentinel-dev` agent
2. If `.neuroflow/` exists → **project repo** — invokes the `sentinel` agent
3. Otherwise → asks you to run `/neuroflow` first

Both agents start with a script that makes the mechanical checks the same way every time, then spend their own reading on the checks that need judgement. The scripts never change anything.

---

## Project repo — mechanical checks

The `sentinel` agent first runs `nf_check.py` from the `neuroflow-core` skill:

```bash
python <neuroflow-core skill base dir>/scripts/nf_check.py --json
```

Exit `0` = clean, `1` = findings, `2` = the script could not run (the agent then does the same checks by reading). You can run it yourself, or in CI, from anywhere inside the project.

| Id | Check | What it verifies |
|---|---|---|
| NF1 | flow.md index | The root `flow.md` lists every folder; each folder's `flow.md` lists every file in it (`sessions/`, `tasks/`, `wiki/` and `meetings/` have their own structure); nothing listed is missing |
| NF2 | Project config | `project_config.md` frontmatter, schema version, canonical phases, `plugin_version` against the installed plugin, no personal settings in the shared file |
| NF3 | Integrity status | `preregistration/status.md` and `ethics/status.md`; a frozen preregistration is re-hashed by the preregistration skill's `freeze.py verify`; expired or model-set approvals |
| NF4 | Reasoning logs | `reasoning/*.jsonl` holds one valid JSON object per line with `statement`, `source`, `reasoning`; old `.json` logs are flagged for `/neuroflow:migrate` |
| NF5 | Conflict markers | No `<<<<<<<` / `>>>>>>>` lines left over from a merge |
| NF6 | Memory structure | Only the documented files and folders in `.neuroflow/`; flags skill-named folders, legacy files and project-level `flowie/` or `hive/` folders |
| NF7 | Instruction block | `.claude/CLAUDE.md` points at `project_config.md` and holds no `Active phase` line; no stale neuroflow block in `~/.claude/CLAUDE.md`, `.github/copilot-instructions.md` or `AGENTS.md` |
| NF8 | Sensitive data | The phase-output skill's PII scanner over the shared memory files (emails, secrets, configured ID patterns, roster names); values are never printed |

## Project repo — judgement checks

| Id | Check |
|---|---|
| S1 | Timestamp drift — stale `flow.md` dates, phases untouched while the project is active |
| S2 | Phase consistency — `active_phase` vs the latest session log vs folder activity |
| S3 | Preregistration vs progress — analyses or decisions that deviate from the plan without a `deviations.md` entry |
| S4 | Ethics gate — human data in `.neuroflow/data/` without a recorded approval (silenced by `ethics: not-applicable`) |
| S5 | Names and institutions in logs (and emails or secrets when the PII scanner is not installed) |
| S6–S8 | Flowie, wiki and hive structure, when they exist |

---

## Plugin repo (`sentinel-dev`)

In the plugin repo the `sentinel-dev` agent runs `python scripts/automation/validate_pr.py` — the same checks CI runs on every pull request (V1–V15: manifests, version sync, command frontmatter, docs pages, names, `hooks.json`, rule markers, name collisions, README / nav propagation, dead references, release notes, sensitive info, path hygiene) — and adds the checks that need judgement. See [Maintenance Automation](../maintenance/automation.md).

---

## Example output

```
/neuroflow:sentinel
```

```
Sentinel report — 2026-10-07

Issues found:
────────────
1. [NF1] .neuroflow/data-preprocess/flow.md lists preprocess-config.md,
   but the file does not exist on disk.
   → Fix: remove the row? (y/n)

2. [NF2] project_config.md has plugin_version 0.2.18; the installed
   plugin is 0.2.22.
   → Fix: update plugin_version? (y/n)

3. [NF7] .claude/CLAUDE.md holds an "Active phase" line — it goes stale.
   → Fix: remove the line? (y/n)

4. [S3] The analysis summary uses a cluster-based permutation test; the
   frozen preregistration planned FDR across electrodes, and
   deviations.md has no entry for the change.

All other checks: ✅ All clear
```

---

## What sentinel can fix (after you agree)

| Issue | Fix |
|---|---|
| Missing file listed in `flow.md` | Remove the row |
| Existing file not in `flow.md` | Add a row |
| Plugin version out of sync | Update `plugin_version` in `project_config.md` |
| Skill-named subfolder in `.neuroflow/` | Move its files to the phase folder, delete the skill folder |
| Missing or stale neuroflow block in `.claude/CLAUDE.md` | Write the static block from `neuroflow-core` |
| Neuroflow block in `~/.claude/CLAUDE.md` or a stale copy | Remove that block, keep the rest of the file |

Sentinel never edits a frozen preregistration or its `status.md` (freezing and unfreezing are your actions; changes go to `deviations.md`), and never redacts sensitive data on its own.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/sentinel.md`, `.neuroflow/reasoning/`, `.neuroflow/preregistration/`, `.neuroflow/ethics/`, `.neuroflow/sessions/`, `.claude/CLAUDE.md` |
| Writes | `.neuroflow/sentinel.md`, `.neuroflow/project_config.md`, `.claude/CLAUDE.md` |

---

## Related commands

- [`/doctor`](doctor.md) — checks the setup around the project (Python, git, backups, the mod)
- [`/migrate`](migrate.md) — converts an older project to the current file formats
- [`/phase`](phase.md) — check current phase
- [`/write-report`](write-report.md) — generate a report after sentinel confirms consistency
