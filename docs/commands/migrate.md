---
title: /migrate
---

# `/neuroflow:migrate`

**After a plugin update, the one command that brings your project, your flowie and the team hive up to date — shown first, written only after you agree.**

`/migrate` converts what earlier neuroflow versions wrote, level by level. In the project's `.neuroflow/` it turns `project_config.md` into YAML frontmatter plus free notes, converts decision logs to JSON Lines, adds the merge-safety and local-only git lines, replaces an outdated instruction block, and records the neuroflow version the project is now up to date with (`plugin_version`). In your flowie and the team hive it moves task files into the current format and keeps machine-local files out of git. It is idempotent: a migrated level has nothing left to do.

---

## When to use it

- after updating the plugin — the main reason. When the project is on an older version than the one installed, the first neuroflow command in each session says so in one line and names `/migrate`; with the [neuroflow mod](../concepts/mods.md), the band above the prompt keeps that line, with an `m` key that runs `/migrate`. Only `/migrate` (and the setup of a new project) records the version, so the line stays until the project is migrated. See [Upgrading](../upgrading.md)
- `/neuroflow` or another command says your `project_config.md` uses a legacy format
- your decision logs are still `reasoning/*.json` arrays

---

## What it does

1. **Dry run** — runs `migrate.py` from the `neuroflow-core` skill, which writes nothing and prints the plan, including a diff of `project_config.md`
2. **Decisions** — asks about anything it cannot decide alone, for example which phase a legacy value such as `active development` means
3. **Personal fields** — offers to move your issue-report consent, name, writing style and Zotero preference out of the shared project file into `~/.neuroflow/user.yaml`
4. **Apply** — writes the plan only after you confirm
5. **Your flowie and the team hive** — pulls each one and plans only those that pulled cleanly: one whose pull fails waits for the next run, and an older hive cache of copied files (no `.git/`) waits for `/hive --init`, which replaces it with a clone. It shows the plan, applies it after you agree, and commits exactly the files it changed; your flowie is pushed (it is your own private repository), a hive only after your explicit yes — with a reminder that teammates on an older neuroflow should update before they use the migrated board

| What | Before | After |
|---|---|---|
| `project_config.md` | `**Phase:** data-analyze` or `active_phase: data analyze` lines | YAML frontmatter (`nf_schema: 1`, `active_phase: data-analyze`, …) followed by your notes, unchanged |
| `plugin_version` | an older version, or none | the version you run (a newer one, recorded by a teammate's newer neuroflow, stays) |
| Decision logs | `reasoning/general.json` (one JSON array) | `reasoning/general.jsonl` (one entry per line); the old file is kept as `general.json.bak` |
| `.gitattributes` | — | union merge for append-only logs, so two collaborators' entries merge without conflicts |
| `.gitignore` | — | session logs, confidential reviews and credentials stay out of git |
| `.claude/CLAUDE.md` | a neuroflow block naming the active phase | the static block that points at `project_config.md` |
| Flowie and hive tasks | `tasks/t-014-re-run-ica.md` with `id:` and `assignee:` | `tasks/active/re-run-ica.md` with `status:` and `owner:` (the [task format](tasks.md)), moved with `git mv` so its history follows; the slug stays as it was, and when a name has to change, the `blocked_by` entries that name the task follow it |
| Flowie and hive `.gitignore` | — | `integrations.json` (flowie) and `sync.json` (hive) stay on your machine |

It only **reports** neuroflow blocks in `~/.claude/CLAUDE.md`, `.github/copilot-instructions.md` and `AGENTS.md`, and offers to remove each one after showing it to you. It also only reports an `integrations.json` or `sync.json` that git already tracks: untracking it, and cleaning the history if you want that, is your call (for a hive, the team's). The same goes for a task file that is not UTF-8 (convert it, then run `/migrate` again), a task that names more than one person as its owner (you choose who owns it; nobody is dropped), and a `blocked_by` entry that could now mean two tasks.

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

✅ Project migrated.

Flowie (pulled):  tasks/t-014-re-run-ica.md → tasks/active/re-run-ica.md (assignee → owner)
                  .gitignore: + integrations.json
Hive example-lab (pulled): no changes needed

Claude: Apply the flowie changes?   ▸ Apply these changes   Cancel
You:    Apply these changes

✅ Flowie committed and pushed. Commit the project's migration on its own, so collaborators see one clean change.
Next: /neuroflow:phase
```

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/reasoning/`, `.claude/CLAUDE.md`, `.gitattributes`, `.gitignore`, `~/.neuroflow/user.yaml`, `~/.neuroflow/flowie/tasks/` and `.gitignore`, `~/.neuroflow/hives/{org-repo}/tasks/` and `.gitignore`; `~/.claude/CLAUDE.md`, `.github/copilot-instructions.md`, `AGENTS.md` (report only) |
| Writes | `.neuroflow/project_config.md`, `.neuroflow/reasoning/`, `.neuroflow/sessions/YYYY-MM-DD.md`, `.claude/CLAUDE.md`, `.gitattributes`, `.gitignore`, `~/.neuroflow/user.yaml` (only if you agree), `~/.neuroflow/flowie/tasks/` and `.gitignore` (committed and pushed), `~/.neuroflow/hives/{org-repo}/tasks/` and `.gitignore` (pushed only after your yes) |

---

## Related commands

- [`/neuroflow`](neuroflow.md) — project status; points you here when the project needs migrating
- [`/phase`](phase.md) — check or switch the active phase
- [`/sentinel`](sentinel.md) — audit `.neuroflow/` for consistency
- [`/tasks`](tasks.md) — the task format flowie and hive boards are moved to
- [`/flowie`](flowie.md) and [`/hive`](hive.md) — your personal level and the team level
