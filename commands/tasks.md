---
name: tasks
description: Single entry point for the 3-tier Kanban task board — view, add, move, complete, and archive tasks at project, flowie (personal), or hive (team) level. /flowie --tasks, /meeting action items, and /hive --tasks all delegate to this spec.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/tasks/
  - ~/.neuroflow/flowie/tasks/
  - ~/.neuroflow/hives/{org-repo}/tasks/
writes:
  - .neuroflow/tasks/
  - ~/.neuroflow/flowie/tasks/
  - ~/.neuroflow/hives/{org-repo}/tasks/
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /tasks

**This command owns the task board.** The 3-tier task model has exactly one canonical spec — this file. `/flowie --tasks`, `/hive --tasks`, and `/meeting` action-item conversion follow the rules here; they must not define their own board behavior.

Follow the `neuroflow:neuroflow-core` lifecycle (including the missing-`.neuroflow/` rule — for `--level project` without `.neuroflow/`, offer `/neuroflow` first).

## Levels

| Level | Path | Scope | Sync |
|---|---|---|---|
| `project` (default when `.neuroflow/` exists) | `.neuroflow/tasks/` | This project — git-tracked, shared with collaborators | Committed with the project repo |
| `flowie` | `~/.neuroflow/flowie/tasks/` | Personal, cross-project, private | Pull before read, push after write (flowie sync rules) |
| `hive` | `~/.neuroflow/hives/{org-repo}/tasks/` | Team-wide | Pull before read, push after write |

Select with `--level project|flowie|hive`. If the requested level's storage doesn't exist (no flowie linked, no hive joined), say so and point at `/flowie --init` or `/hive --init` — never scaffold another level's storage from here.

## Task file format

One markdown file per task, filename `{id}-{slug}.md`, in the level's `tasks/` folder:

```markdown
---
id: t-014
title: Re-run ICA on sub-07 after channel repair
status: active          # inbox | active | review | done | archived
created: 2026-08-13
due: 2026-08-20         # optional
assignee: {handle}      # optional — from project_config.md collaborators
project: {repo-name}    # flowie/hive levels only — which project this belongs to
source: meeting/2026-08-12-lab-meeting.md   # optional — where the task came from
---

Free-form task notes below the frontmatter.
```

## Modes

| Mode | What it does |
|---|---|
| *(none)* | Render the board for the chosen level |
| `--add "title"` | Create a task in `inbox` (ask for due date/assignee only if the user's phrasing implies them) |
| `--move {id} {column}` | Change `status` |
| `--done {id}` | Set `status: done` |
| `--archive` | Move all `done` tasks to `status: archived` |

## Rendering — mandatory

Every board display renders as an ASCII Kanban, never a flat list:

```
┌─ inbox ──────────┬─ active ─────────┬─ review ────────┬─ done ──────────┐
│ t-015 fix marker │ t-014 re-run ICA │ t-011 QC report │ t-009 prereg    │
│                  │   due 08-20      │                 │                 │
└──────────────────┴──────────────────┴─────────────────┴─────────────────┘
```

Overdue tasks (past `due`) are marked `⚠` and listed first in their column.

## At end

- For `flowie`/`hive` levels: commit and push the change (`tasks: {action} {id}`), fail silently on network errors.
- If `.neuroflow/` exists: append `## HH:MM — [tasks] {action}: {id} {title} ({level})` to `.neuroflow/sessions/YYYY-MM-DD.md`.
