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

Select with `--level project|flowie|hive`. Flowie and hive levels pull before reading and push after writing.

---

## Modes

| Mode | What it does |
|---|---|
| *(none)* | Render the ASCII Kanban board |
| `--add "title"` | Create a task in `inbox` |
| `--move {id} {column}` | Move between `inbox` / `active` / `review` / `done` |
| `--done {id}` | Complete a task |
| `--archive` | Archive all done tasks |

Every board display is a rendered ASCII Kanban — never a flat list. Overdue tasks are flagged `⚠` and float to the top of their column.

---

## Task files

One markdown file per task with frontmatter (`id`, `title`, `status`, `created`, optional `due`, `assignee`, `project`, `source`) and free-form notes below. Tasks created from meeting action items carry a `source:` pointing at the meeting file.

---

## Related

- [`/flowie`](flowie.md) — personal level lives in your flowie repo
- [`/hive`](hive.md) — team level lives in the hive cache
- [`/meeting`](meeting.md) — action items become tasks via this spec
