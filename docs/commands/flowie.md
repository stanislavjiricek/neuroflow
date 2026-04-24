---
title: /flowie
---

# `/neuroflow:flowie`

**Personal research OS — a private GitHub repository that holds your identity profile, a cross-project Kanban task board, and a project registry with phase tracking.**

`/flowie` connects neuroflow to a private GitHub repository that acts as your personal research operating system. Claude reads your profile to personalise assistance, surfaces active tasks at session start, and automatically syncs phase changes to the project registry.

Flowie is entirely optional. Nothing in neuroflow breaks if you do not use it.

---

## What Flowie stores

The `flowie` GitHub repo has three layers:

| Layer | Files | Purpose |
|---|---|---|
| **Identity** | `profile.md`, `ideas.md` | Research identity: stances, writing style, preferred methods, key beliefs; cross-project hypotheses |
| **Kanban** | `tasks/config.json`, `tasks/{column}/` | Task board — one `.md` file per task, one folder per column |
| **Registry** | `projects/projects.json`, `projects/{name}.md` | Project list with GitHub repos, current phase, phase history |

All data lives in `.neuroflow/flowie/` locally (this folder IS a git clone). GitHub is the canonical source of truth — pull before read, push after every write.

---

## Prerequisites

- A GitHub account
- One of the following for authentication:
  - **GitHub CLI (`gh`)** — recommended; run `gh auth login` before using `/flowie`
  - **Personal Access Token (PAT)** — create one at [github.com/settings/tokens](https://github.com/settings/tokens) with the `repo` scope

---

## Getting started

Run `/flowie` in any neuroflow project. On first run, you will be guided through:

1. GitHub authentication (CLI or PAT)
2. Checking for an existing `flowie` repository on your account — or creating one
3. Cloning it to `.neuroflow/flowie/` and scaffolding the full structure

Then run `/flowie --init` to build your profile through a short interview.

---

## Modes

| Mode | What it does |
|---|---|
| `--init` | Build your profile from scratch via an interview — name, domain, methods, writing style, stances, 3–5 key beliefs |
| `--sync` | Pull the latest profile from GitHub, then push any local changes; shows diffs before applying |
| `--link` | Link the current project to a flowie project entry; adds an entry to the `flowie_profiles:` list in `project_config.md` |
| `--view` | Display your current profile summary |
| `--identify` | Claude generates a "who you are" paragraph from your profile; you confirm or correct it |
| `--tasks` | ASCII Kanban board view (all projects, or filtered with `--project {name}`) |
| `--tasks --list` | Flat list view of all tasks |
| `--tasks --add` | Add a task via a mini interview (title → project → phase, due) |
| `--tasks --move <slug> <column>` | Move a task to a different column |
| `--tasks --done <slug>` | Move a task to the `done/` column |
| `--tasks --archive` | Sweep `done/` → `archive/` for tasks older than `archive_after_days` |
| `--projects` | List all registered projects with ASCII phase timelines |
| `--projects --add` | Register a new project (name, description, GitHub repos) |

If no mode flag is provided, `/flowie` shows the mode menu.

---

## Kanban board

Tasks live as `.md` files inside column folders (`tasks/inbox/`, `tasks/active/`, etc.). Column definitions are in `tasks/config.json`.

**Default columns:** 📥 Inbox · 🟢 Ready · ⚡ Active · 👁 Review · 📅 Meeting · ✅ Done · 📦 Archive

ASCII board example:
```
┌─ 📥 Inbox ──────┐  ┌─ ⚡ Active ──────┐  ┌─ 👁 Review ──────┐
│ spin-tests      │  │ fix-rt-des       │  │ grant-draft      │
│ ethics-form     │  │ eeg-param-sweep  │  │                  │
└─────────────────┘  └──────────────────┘  └──────────────────┘
```

---

## Project registry

Projects are stored in `projects/projects.json` (machine index) and `projects/{name}.md` (rich notes with phase timeline table).

ASCII phase timeline example:
```
AlphaModulation
  [ideation ✓]→[experiment ✓]→[data ✓]→[analyze ◉]→[paper ·]
```

Phase changes are auto-synced: whenever `/phase` switches the active phase, if the project has a `flowie_profiles` binding, it updates the registry and pushes silently.

---

## How Claude uses the profile

Once a project is linked (via `--link`), Claude reads the profile at the start of each session and applies it:

- In **`/ideation`**: suggestions are framed around your research domain and existing ideas from `ideas.md`
- In **`/paper`**: drafts match your documented writing style and register
- In **`/data-analyze`**: statistical approaches are presented in your preferred framework (e.g. Bayesian-first if that is your stance)
- In **all phases**: if a documented stance or belief is relevant to a decision, Claude surfaces it once and asks whether it applies

The profile informs suggestions — it does not override your explicit instructions.

---

## Privacy

- The `flowie` GitHub repository is always private
- Profile data never appears in outputs intended for external readers (papers, grant proposals, reports)
- `.neuroflow/flowie/` is excluded from `/export` by default
- The PAT (if used) is held in memory only — never written to disk

---

## Sync behaviour

`--sync` always pulls before pushing:

1. Fetches remote changes and shows a diff
2. You confirm before remote changes are applied
3. Merge conflicts are shown side by side — never silently resolved
4. Local changes are pushed after the pull step
5. `last_synced` in `sync.json` is updated only if the push succeeds

All other write operations (task add/move/done, project add, phase sync) push silently with `|| true`.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/flowie/profile.md`, `.neuroflow/flowie/ideas.md`, `.neuroflow/flowie/sync.json`, `.neuroflow/flowie/tasks/config.json`, `.neuroflow/flowie/tasks/{column}/*.md`, `.neuroflow/flowie/projects/projects.json`, `.neuroflow/flowie/projects/{name}.md` |
| Writes | `.neuroflow/flowie/profile.md`, `.neuroflow/flowie/ideas.md`, `.neuroflow/flowie/sync.json`, `.neuroflow/flowie/tasks/{column}/{slug}.md`, `.neuroflow/flowie/projects/projects.json`, `.neuroflow/flowie/projects/{name}.md`, `.neuroflow/project_config.md`, `.neuroflow/sessions/YYYY-MM-DD.md` |

---

## Related commands and agents

- [`/neuroflow`](neuroflow.md) — project setup and status; run before `/flowie`
- [`flowie` agent](../concepts/agents.md) — apply the profile autonomously and surface active tasks at session start
- [`/phase`](phase.md) — phase switching; auto-syncs to the flowie project registry when linked
- [`/output`](output.md) — flowie data is excluded from project exports by default
