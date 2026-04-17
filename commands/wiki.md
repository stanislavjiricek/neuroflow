---
name: wiki
description: Project-level shared knowledge base — Karpathy-style LLM-maintained wiki at .neuroflow/wiki/, git-tracked and shared with all project collaborators. The shared brain for experimental rationale, analysis decisions, project literature, and methods. Use /flowie --wiki-* for personal wiki, /hive --wiki-* for team wiki.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/wiki/**
writes:
  - .neuroflow/wiki/
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /wiki

Project-level shared knowledge base. Lives at `.neuroflow/wiki/`, git-tracked in the project repo, visible to all collaborators.

**Three-level wiki overview:**
- `/wiki` — this command — project brain (shared with collaborators)
- `/flowie --wiki-*` — personal wiki (private, in flowie repo)
- `/hive --wiki-*` — team wiki (lab-wide, in hive repo)

Read the `neuroflow:wiki` skill first with `level: project`. Then follow the neuroflow-core lifecycle.

---

## Step 0 — Check for .neuroflow/

If `.neuroflow/` does not exist, stop and tell the user to run `/neuroflow` first.

---

## Step 1 — Parse mode flag

If no flag given: default to `--view` if wiki exists, `--schema` if it does not.

| Flag | Action |
|------|--------|
| `--view` | Show wiki overview: page count, recent activity |
| `--ingest [path]` | Ingest a source into the project wiki |
| `--query [question]` | Ask a question answered from the project wiki |
| `--lint` | Health check: orphans, stale pages, missing tags |
| `--add [title]` | Create or update a wiki page |
| `--schema` | View or update wiki conventions (also initializes wiki) |

Wiki root for all operations: `.neuroflow/wiki/`
Git pattern: standard `git` in project root (not `-C` flowie pattern).

---

## Step 2 — Execute mode

Follow the `neuroflow:wiki` skill at `level: project`.

**Project-specific context for `projects:` tagging:**
The current project IS the context — read `project_config.md` for project name, phase, and modality. Ask if the page also relates to other projects the user is aware of.

---

## Step 3 — Session log

Append to `.neuroflow/sessions/YYYY-MM-DD.md`:

```
[HH:MM] /wiki --{mode} [level:project] — {brief summary}
```
