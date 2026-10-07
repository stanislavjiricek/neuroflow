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
| **Kanban** | `tasks/config.json`, `tasks/{column}/{slug}.md` | Task board — one `.md` file per task, one folder per column; the format is defined by [`/tasks`](tasks.md) |
| **Registry** | `projects/projects.json`, `projects/{name}.md` | Project list with GitHub repos, current phase, phase history |

All data lives in `~/.neuroflow/flowie/` locally (this folder IS a git clone). GitHub is the canonical source of truth — pull before read, push after every write.

---

## Prerequisites

- A GitHub account
- One of the following for authentication:
  - **GitHub CLI (`gh`)** — recommended; run `gh auth login` before using `/flowie`
  - **git with a stored GitHub credential** — store it yourself, in your own terminal (your git credential manager, or `git credential approve`); without `gh`, you create the private `flowie` repository on GitHub yourself

---

## Getting started

Run `/flowie` in any neuroflow project. On first run, you will be guided through:

1. GitHub authentication (`gh`, or git with a credential you stored yourself — never a token in the chat)
2. Checking for an existing `flowie` repository on your account — or creating one
3. Cloning it to `~/.neuroflow/flowie/` and scaffolding the full structure

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
| `--tasks` | ASCII Kanban board view (all projects, or filtered with `--project {name}`) — same as `/tasks --level flowie` |
| `--tasks --list` | Flat list view of all tasks |
| `--tasks --add` | Add a task (title, project; owner, due date and phase when they apply) |
| `--tasks --move <slug> <column>` | Move a task to a different column |
| `--tasks --done <slug>` | Move a task to the `done/` column |
| `--tasks --archive` | Sweep `done/` → `archive/` for tasks not updated for `archive_after_days` |
| `--projects` | List all registered projects with ASCII phase timelines |
| `--projects --add` | Register a new project (name, description, GitHub repos) |

If no mode flag is provided, `/flowie` shows the mode menu.

---

## Kanban board

Tasks live as `.md` files inside column folders (`tasks/inbox/`, `tasks/active/`, etc.), one file per task named by its slug. Column definitions are in `tasks/config.json`. The file format and board rules are the same at every level — see [`/tasks`](tasks.md).

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

Where each project lives on *this* machine is kept in `~/.neuroflow/local-projects.json`, outside the flowie repo and never synced — so no local folder paths end up in your GitHub repo. `/flowie --link` writes it; `/flowie --projects` shows the local folder next to each project.

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
- `~/.neuroflow/flowie/` is never included in an `/output` export
- neuroflow never asks for a GitHub token in the chat: you sign in with `gh auth login` or store a git credential in your own terminal
- `integrations.json` is gitignored in the flowie repo and never committed
- Wellbeing entries are only what you type in `--assess` — nothing is inferred from your messages or working patterns

---

## Sync behaviour

`--sync` always pulls before pushing:

1. Pulls remote changes (rebase) and summarises what came in
2. Merge conflicts are shown side by side — never silently resolved; a half-finished rebase is always aborted
3. Local changes are listed, then committed by path (never `git add -A`, never `integrations.json`) and pushed
4. `last_synced` in `sync.json` is updated only if the push succeeds
5. Failures recorded by the auto-sync hook are shown, and cleared once a pull and a push have both succeeded

Every other write (task add/move/done, project add, wellbeing, phase sync) is synced as it happens: the plugin's auto-sync hook commits the one file Claude just wrote, pulls with rebase, then pushes. It never blocks you — if anything fails (offline, auth, a conflict), the commit stays local and one line goes to `~/.neuroflow/flowie-sync.log`, which `/flowie` mentions until `--sync` resolves it.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `~/.neuroflow/flowie/profile.md`, `~/.neuroflow/flowie/ideas.md`, `~/.neuroflow/flowie/sync.json`, `~/.neuroflow/flowie/tasks/config.json`, `~/.neuroflow/flowie/tasks/{column}/*.md`, `~/.neuroflow/flowie/projects/projects.json`, `~/.neuroflow/flowie/projects/{name}.md` |
| Writes | `~/.neuroflow/flowie/profile.md`, `~/.neuroflow/flowie/ideas.md`, `~/.neuroflow/flowie/sync.json`, `~/.neuroflow/flowie/tasks/{column}/{slug}.md`, `~/.neuroflow/flowie/projects/projects.json`, `~/.neuroflow/flowie/projects/{name}.md`, `.neuroflow/project_config.md`, `.neuroflow/sessions/YYYY-MM-DD.md` |

---

## Related commands and agents

- [`/neuroflow`](neuroflow.md) — project setup and status; run before `/flowie`
- [`flowie` agent](../concepts/agents.md) — apply the profile autonomously and surface active tasks at session start
- [`/phase`](phase.md) — phase switching; auto-syncs to the flowie project registry when linked
- [`/output`](output.md) — flowie data is never included in project exports
