---
title: /sentinel
---

# `/neuroflow:sentinel`

**Full audit of your project — drift detection, broken references, and consistency checks.**

`/sentinel` is a coherence guard. It audits `.neuroflow/` for internal consistency: checks that `flow.md` files match the actual files on disk, detects drift between phases, verifies preregistration compliance, and keeps plugin version in sync.

---

## When to use it

- Before writing a report or paper — make sure everything is consistent
- When you suspect something is out of sync
- Periodically, as a project health check
- In plugin development mode — to audit the plugin itself

---

## What it does

Claude checks which context it's in and routes to the appropriate agent:

1. If `.claude-plugin/plugin.json` exists → **plugin repo** — invokes the `sentinel-dev` agent
2. If `.neuroflow/` exists → **project repo** — invokes the `sentinel` agent
3. Otherwise → asks you to run `/neuroflow` first

---

## Sentinel checks (project repo)

### 1 — flow.md completeness

Verifies that every file listed in a `flow.md` actually exists on disk, and every file that exists is listed. Flags mismatches in both directions.

### 2 — Timestamp drift

Compares `flow.md` last-changed dates against actual file modification times. Flags:
- Phase subfolders with recent file activity but stale `flow.md`
- Subfolders that haven't been touched while the project is active (possible abandoned phase)

### 3 — Broken references

Reads `.neuroflow/reasoning/flow.md` and validates each JSON decision file:
- All entries must have `statement`, `source`, and `reasoning` fields
- Flags missing fields

### 4 — Phase consistency

Compares the active phase in `project_config.md` against:
- The most recent session log
- Which phase subfolders exist and when they were last modified

Flags if these tell inconsistent stories.

### 5 — Preregistration vs progress

If `.neuroflow/preregistration/` exists, compares stated hypotheses and planned analyses against:
- `.neuroflow/reasoning/` (were there undocumented deviations?)
- The analysis summary in `.neuroflow/data-analyze/`

Flags deviations — does not judge them, just surfaces them.

### 6 — Plugin version sync

Reads the current plugin version from `plugin.json` and compares it against `plugin_version` in `project_config.md`.

- Flags if `plugin_version` is missing from `project_config.md`
- Flags if the plugin has been updated since the project was last configured
- **Auto-fixes:** updates `plugin_version` in `project_config.md` to match

### 7 — Subfolder name validation

Lists all subfolders in `.neuroflow/` and validates them against:
- Valid phase names (derived from command frontmatter)
- Standard root subfolders (`sessions`, `reasoning`, `ethics`, `preregistration`, `finance`)

Flags unrecognized subfolders and skill-named subfolders (skills must not create their own folders).

### 8 — CLAUDE.md reference check

Checks whether `.claude/CLAUDE.md` exists and references `project_config.md`.

**Auto-fixes:** appends the neuroflow block if missing, or creates the file if it doesn't exist.

---

## Example output

```
/neuroflow:sentinel
```

```
Sentinel report — 2026-03-09

Issues found:
────────────
1. flow.md drift: .neuroflow/data-preprocess/flow.md lists
   preprocess-config.md but the file does not exist on disk.
   → Fix: remove from flow.md? (y/n)

2. Plugin version: project_config.md has plugin_version: 0.1.1
   but current plugin is 0.1.2.
   → Auto-fixing: updating plugin_version in project_config.md

3. CLAUDE.md: .claude/CLAUDE.md exists but does not reference
   project_config.md.
   → Auto-fixing: appending neuroflow block

All other checks: ✅ All clear

Fixes applied. Rewriting .neuroflow/sentinel.md...
```

---

## What sentinel can auto-fix

| Issue | Auto-fix |
|---|---|
| Missing file listed in `flow.md` | Remove the entry from `flow.md` |
| Existing file not in `flow.md` | Add it to `flow.md` |
| Plugin version out of sync | Update `plugin_version` in `project_config.md` |
| Skill-named subfolder in `.neuroflow/` | Move contents to phase subfolder, delete skill folder |
| Missing neuroflow block in `CLAUDE.md` | Append the block |
| `CLAUDE.md` does not exist | Create it with the neuroflow block |

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/sentinel.md`, `.neuroflow/preregistration/`, `.neuroflow/sessions/`, `.claude/CLAUDE.md` |
| Writes | `.neuroflow/sentinel.md`, `.neuroflow/project_config.md`, `.claude/CLAUDE.md` |

---

## Related commands

- [`/phase`](phase.md) — check current phase
- [`/write-report`](write-report.md) — generate a report after sentinel confirms consistency
