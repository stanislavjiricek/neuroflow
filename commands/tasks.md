---
name: tasks
description: Single entry point for the 3-tier Kanban task board — view, add, move, complete, and archive tasks at project, flowie (personal), or hive (team) level. /flowie --tasks, /meeting action items, and /hive --tasks all delegate to this spec.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/tasks/
  - ~/.neuroflow/flowie/tasks/
  - ~/.neuroflow/hives/{org-repo}/tasks/
  - ~/.neuroflow/local-projects.json        # which flowie project this repo is (this project's tasks first)
  - ~/.neuroflow/flowie/projects/projects.json
  - ~/.neuroflow/hives/{org-repo}/projects/projects.json   # which lab project this repo is in that hive
writes:
  - .neuroflow/tasks/
  - ~/.neuroflow/flowie/tasks/
  - ~/.neuroflow/hives/{org-repo}/tasks/
  - .neuroflow/sessions/YYYY-MM-DD.md
lifecycle: light
produces:
  - .neuroflow/tasks/
---

# /tasks

**This command owns the task board.** The 3-tier task model has exactly one canonical spec — this file. `/flowie --tasks`, `/hive --tasks`, and `/meeting` action-item conversion follow the rules here; they must not define their own board behavior or task format.

Follow the `neuroflow:neuroflow-core` lifecycle (open with its version notice when the project's `plugin_version` is missing or older than the running neuroflow's version in `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` (**Command lifecycle**, step 3), and the missing-`.neuroflow/` rule — for `--level project` without `.neuroflow/`, offer `/neuroflow` first).

## Levels

| Level | Path | Scope | Sync |
|---|---|---|---|
| `project` (default when `.neuroflow/` exists) | `.neuroflow/tasks/` | This project — git-tracked, shared with collaborators | Lives in the project's working tree; committing and pushing is the person's call (`/git`) |
| `flowie` | `~/.neuroflow/flowie/tasks/` | Personal, cross-project, private | Pull before read; the flowie auto-sync hook commits and pushes each file written with Edit/Write |
| `hive` | `~/.neuroflow/hives/{org-repo}/tasks/` | Team-wide | Pull before read; commit by path, push only after the person confirms |

Select with `--level project|flowie|hive`. At hive level, `--hive {org-repo}` names the hive — its folder under `~/.neuroflow/hives/` — when the person joined several; without it, ask which (a single joined hive needs no flag). If the requested level's storage doesn't exist (no flowie linked, no hive joined), say so and point at `/flowie` or `/hive --init` — never scaffold another level's storage from here.

**This project** is named per level, by the registry whose names that level's `project:` carries. At flowie level it is the flowie project this repo is linked to: the `name` of this folder's entry in `~/.neuroflow/local-projects.json`, else the entry of the flowie's `projects/projects.json` whose `repos` list this folder or its `origin` remote URL. At hive level, where `project:` names the lab project (`neuroflow:phase-hive` → `--tasks`), it is the entry of that hive's own `projects/projects.json` whose `repos` list this folder or its `origin` remote URL. A level's tasks of this project are those whose `project:` is its name there. Without a link at a level, none of that level's tasks is this project's — never guess one from names, nor carry a name from one level to another.

## Task file format

One markdown file per task at `{level root}/tasks/{column}/{slug}.md` — **the folder is the column**. The same format at every level:

```markdown
---
title: "Re-run ICA on sub-07 after channel repair"
status: active                  # always equals the column folder
owner: jana                     # optional — roster handle, no @
due: 2026-08-20                 # optional — YYYY-MM-DD
phase: data-preprocess          # optional — canonical phase id
tags: [eeg, qc]                 # optional
blocked_by: [fix-channel-map]   # optional — slugs at the same level
created: 2026-08-13
updated: 2026-08-14             # set on every change, moves included
project: Oddball EEG            # flowie and hive levels — which project the task belongs to
source: project:meetings/2026-08-12-lab-meeting.md   # optional — {level}:{path under that level's root}
---

Free-form task notes below the frontmatter.
```

- **Slug** — the file name and the task's id. Built from the title: lowercase ASCII, accents dropped, every other run of characters → `-`, at most 40 characters (`task` if nothing is left). If `{slug}.md` already exists in any column of that level, append `-2`, `-3`, … Never rename or renumber a slug once written.
- **`status` mirrors the folder.** If they disagree, the folder wins; fix `status` on the next write.
- **`owner`** is a handle from the roster: `collaborators:` in `project_config.md`, the hive's `members.md`, or the person's own flowie handle. If a name does not match the roster, ask — never invent a handle or an email address.
- **No machine-local paths** (`C:/Users/…`, `/home/…`) in task files: flowie and hive tasks sync to other machines and people. Refer to projects by name (`project:`), to files by repo-relative path.
- **Legacy files** (`{id}-{slug}.md` flat in `tasks/`, or `id:` / `assignee:` / `responsible:` / `level:` keys) stay readable: read `assignee` or `responsible` as `owner` and `status` as the column (`archived` = `archive`). The next write to such a task moves it into its column folder under its slug and writes the keys above. If `assignee`, `responsible` and `owner` name different people, ask who owns the task before that write — never drop a person. If its name has to change (a `-2` suffix, or a file name that is not a slug), update the `blocked_by` entries at that level that name it.

## Columns

Default columns, in board order: `inbox` · `ready` · `active` · `review` · `meeting` · `done` · `archive`. `meeting` holds items to raise at the next meeting.

A level may carry `tasks/config.json` with its own `columns` list (`id`, `label`, optional `"archive": true`) and `archive_after_days` (default 90). Without it, the defaults apply. Column folders are created on first use.

## Modes

**With the neuroflow mod**, a bare `/neuroflow:tasks` never reaches the model: the mod draws the boards as a pane
from these files, each level's board as `/tasks --level {level}` renders it (same rendering rules) — the project's,
the flowie's and every hive clone's, read as the local clones are (nothing is pulled). `v` or a level's button
switches the level; the pane opens on the project board when it has open tasks, else on the first level with open
tasks of this project, else on the first with any. You pick a card and a column, and it puts the move in the prompt
for you to send — `/neuroflow:tasks --move {slug} {column}`, with `--level flowie` or `--level hive --hive {org-repo}`
before `--move` at those levels; the move itself still runs as below. Any argument (`--list`, `--add`, `--move`,
`--level`, `--hive`, …) runs this prose.

| Mode | What it does |
|---|---|
| *(none)* | Render the board for the chosen level |
| `--list` | Flat list for the chosen level — for narrow screens, or when the person asks for a list: grouped by column, then by `due` (soonest first, undated last) |
| `--add "title"` | Create a task in `inbox`. Ask for owner, due date or phase only if the person's phrasing implies them; at flowie and hive levels, ask which project if it is not obvious from the current repo |
| `--move {slug} {column}` | Move the task to another column (see Moves) |
| `--done {slug}` | Same as `--move {slug} done` |
| `--archive` | Move `done` tasks whose `updated` is older than `archive_after_days` to `archive` |
| `--project {name}` | Filter the board or list to tasks whose `project` is `{name}` |

## Moves

1. Set `status: {column}` and `updated: {today}` in the task file where it is (Edit).
2. Move the file to `tasks/{column}/` — with `git mv` when the level is a git repo, so history follows it.
3. Commit the move by path — never `git add -A`:
   - `flowie`: `git -C ~/.neuroflow/flowie commit -m "tasks: move {slug} → {column}" -- tasks/{from}/{slug}.md tasks/{column}/{slug}.md`, then `git -C ~/.neuroflow/flowie pull --rebase && git -C ~/.neuroflow/flowie push` (the auto-sync hook only sees Edit/Write, not `git mv`).
   - `hive`: the same commit inside the hive cache; push as in At end.
   - `project`: no commit — the move stays in the working tree with the person's other changes.

`--archive` moves several files the same way and commits them in one commit (`tasks: archive sweep {YYYY-MM-DD}`), listing every path.

## Rendering — mandatory

Every board display renders as an ASCII Kanban — never a flat list, except in `--list`:

```
┌─ inbox ──────────┬─ active ─────────┬─ review ────────┐
│ fix-marker       │ ⚠ rerun-ica @li  │ qc-report       │
│                  │   due 08-20      │                 │
│                  │ spin-tests       │                 │
└──────────────────┴──────────────────┴─────────────────┘
[done: 3 · level: project]
```

- Columns in board order. Omit empty columns except `inbox` and `active`; `done` and `archive` are counted in the footer, not drawn.
- At most 5 cards per column (`+N more` underneath); titles or slugs truncated to fit; `owner` as `@handle`, `due` as `due MM-DD`.
- Overdue tasks (past `due` and not done) are marked `⚠`. Within a column: at `flowie` and `hive` level this project's tasks first (Levels → This project), marked `◆`; then overdue tasks; then by `due`, undated last.
- Footer: the done count and the level shown — at flowie or hive level with `◆ {project}` when this project's tasks are marked.

## At end

- `flowie` level: files written with Edit/Write are committed and pushed by the flowie auto-sync hook; moves are committed as in Moves.
<!-- nf-rule: EGRESS-CONFIRM -->
- `hive` level: commit the changed task files by path (`tasks: {action} {slug}`), show the person what will be pushed to the shared hive repo, and push only after their explicit yes in this turn.
- `project` level: leave the change in the working tree; pushing to the shared project remote is the person's call.
- If `.neuroflow/` exists: append `## HH:MM — [tasks] {action}: {slug} {title} ({level})` to `.neuroflow/sessions/YYYY-MM-DD.md`.
