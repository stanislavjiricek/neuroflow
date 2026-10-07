---
title: /tasks
---

# `/neuroflow:tasks`

**Single entry point for the 3-tier Kanban task board.**

`/tasks` owns the task board. `/flowie --tasks`, `/hive --tasks`, and `/meeting` action-item conversion all follow its spec — one canonical definition of levels, task files, and rendering.

---

## Levels

| Level | Path | Scope |
|---|---|---|
| `project` (default) | `.neuroflow/tasks/` | This project — git-tracked, shared with collaborators |
| `flowie` | `~/.neuroflow/flowie/tasks/` | Personal, cross-project, private |
| `hive` | `~/.neuroflow/hives/{org-repo}/tasks/` | Team-wide |

Select with `--level project|flowie|hive`. Flowie and hive levels pull before reading. Flowie writes are pushed by the flowie auto-sync hook; hive pushes happen only after you confirm; project-level changes stay in your working tree until you commit them.

---

## Modes

| Mode | What it does |
|---|---|
| *(none)* | Render the ASCII Kanban board |
| `--list` | Flat list grouped by column (for narrow screens) |
| `--add "title"` | Create a task in `inbox` |
| `--move {slug} {column}` | Move a task to another column |
| `--done {slug}` | Complete a task |
| `--archive` | Archive done tasks older than `archive_after_days` (default 90) |
| `--project {name}` | Filter to one project |

Every board display is a rendered ASCII Kanban — never a flat list, except `--list`. Overdue tasks are flagged `⚠` and float to the top of their column.

---

## Task files

One markdown file per task at `tasks/{column}/{slug}.md` — the folder is the column. Default columns: `inbox`, `ready`, `active`, `review`, `meeting`, `done`, `archive` (a level can define its own in `tasks/config.json`).

Frontmatter: `title`, `status` (always the column), optional `owner`, `due`, `phase`, `tags`, `blocked_by`, then `created`, `updated`, and at flowie/hive level `project`. Tasks created from meeting action items carry a `source:` pointing at the meeting file (e.g. `project:meetings/2026-08-12-lab-meeting.md`). Owners are roster handles — never invented — and task files never contain machine-local paths.

Older task files (`{id}-{slug}.md`, `assignee:` or `responsible:`) stay readable and are moved into the new layout the next time they are written.

---

## Related

- [`/flowie`](flowie.md) — personal level lives in your flowie repo
- [`/hive`](hive.md) — team level lives in the hive cache
- [`/meeting`](meeting.md) — action items become tasks via this spec
