---
title: /migrate
---

# `/neuroflow:migrate`

**Bring an older project up to the current project-memory format — shown first, written only after you agree.**

`/migrate` converts `.neuroflow/` project memory written by earlier neuroflow versions: it turns `project_config.md` into YAML frontmatter plus free notes, converts decision logs to JSON Lines, adds the merge-safety and local-only git lines, and replaces an outdated instruction block. It is idempotent: a migrated project has nothing left to do.

---

## When to use it

- `/neuroflow` or another command says your `project_config.md` uses a legacy format
- your decision logs are still `reasoning/*.json` arrays
- after updating the plugin, to check whether the project needs anything

---

## What it does

1. **Dry run** — runs `migrate.py` from the `neuroflow-core` skill, which writes nothing and prints the plan, including a diff of `project_config.md`
2. **Decisions** — asks about anything it cannot decide alone, for example which phase a legacy value such as `active development` means
3. **Personal fields** — offers to move your issue-report consent, name and writing style out of the shared project file into `~/.neuroflow/user.yaml`
4. **Apply** — writes the plan only after you confirm

| What | Before | After |
|---|---|---|
| `project_config.md` | `**Phase:** data-analyze` or `active_phase: data analyze` lines | YAML frontmatter (`nf_schema: 1`, `active_phase: data-analyze`, …) followed by your notes, unchanged |
| Decision logs | `reasoning/general.json` (one JSON array) | `reasoning/general.jsonl` (one entry per line); the old file is kept as `general.json.bak` |
| `.gitattributes` | — | union merge for append-only logs, so two collaborators' entries merge without conflicts |
| `.gitignore` | — | session logs, confidential reviews and credentials stay out of git |
| `.claude/CLAUDE.md` | a neuroflow block naming the active phase | the static block that points at `project_config.md` |

It only **reports** neuroflow blocks in `~/.claude/CLAUDE.md`, `.github/copilot-instructions.md` and `AGENTS.md`, and offers to remove each one after showing it to you.

!!! note "Newer projects"
    If a collaborator's newer neuroflow already wrote the project (`nf_schema` higher than your plugin knows), `/migrate` refuses and asks you to update the plugin.

---

## Example session

```
/neuroflow:migrate
```

```
Plan (dry run, nothing written):
  project_config.md: bold labels → frontmatter (nf_schema 1)
  reasoning/general.json → general.jsonl (14 entries), old file kept as general.json.bak
  .gitattributes: +5 lines   .gitignore: +3 lines
  .claude/CLAUDE.md: replace the block that names a phase

Needs a decision: active_phase "active development" is not a phase id.

Claude: Which phase is this project in?   ▸ data-analyze   paper   tool-build   Other
You:    data-analyze

Claude: Move your issue-report consent to ~/.neuroflow/user.yaml?   ▸ Move it   Leave it
You:    Move it

✅ Migrated. Commit it on its own so collaborators see one clean change.
Next: /neuroflow:phase
```

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/reasoning/`, `.claude/CLAUDE.md`, `.gitattributes`, `.gitignore`, `~/.neuroflow/user.yaml`; `~/.claude/CLAUDE.md`, `.github/copilot-instructions.md`, `AGENTS.md` (report only) |
| Writes | `.neuroflow/project_config.md`, `.neuroflow/reasoning/`, `.neuroflow/sessions/YYYY-MM-DD.md`, `.claude/CLAUDE.md`, `.gitattributes`, `.gitignore`, `~/.neuroflow/user.yaml` (only if you agree) |

---

## Related commands

- [`/neuroflow`](neuroflow.md) — project status; points you here when the project needs migrating
- [`/phase`](phase.md) — check or switch the active phase
- [`/sentinel`](sentinel.md) — audit `.neuroflow/` for consistency
