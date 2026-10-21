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

Select with `--level project|flowie|hive`; when you joined several hives, `--hive {org-repo}` names one (its folder under `~/.neuroflow/hives/`), otherwise `/tasks` asks which. Flowie and hive levels pull before reading. Flowie writes are pushed by the flowie auto-sync hook; hive pushes happen only after you confirm; project-level changes stay in your working tree until you commit them.

At flowie and hive level, the tasks of **this project** come first in each column, marked `◆`. At flowie level that is the flowie project this repo is linked to (`/flowie --link`, or an entry of your flowie's `projects.json` that lists this repo); at hive level, the lab project in that hive's own `projects/projects.json` that lists this repo — a hive task's `project:` names the lab project. Without such a link, nothing is marked: names are never guessed.

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
| `--project {id}` | One project across every board: your flowie, each hive, this repository and the project's other repositories (their boards fetched into a local cache in `~/.neuroflow/boards/` each time, never synced) |
| `--apply-web` | Apply the changes you made on [your claude.ai workbench](../concepts/workbench.md) (see below) |

**Where a task goes.** On the narrowest board that everyone who must see it can read: only you — your flowie; the team — the hive (the default for a team project); the people working in this repository, about its code or files — the project board. `--add` proposes the board and says why; you can pick another.

Every board display is a rendered ASCII Kanban — never a flat list, except `--list`. Overdue tasks are flagged `⚠` and float to the top of their column, right after this project's tasks at flowie and hive level.

---

## Changes from your workbench (`--apply-web`)

A card you move or add on [your claude.ai workbench](../concepts/workbench.md) is a request; `--apply-web` is where it
lands in git. It picks up the waiting requests (a project's only when you run it in that project), claims them so a
second machine cannot apply them too, and checks each against git: a task that changed or moved since your snapshot is
a conflict and nothing is written. Accepted changes move the task files exactly as `--move` does — two moves of one card
become one move, a card you added on the page gets its slug here — and every flowie or hive commit names the requests it
holds, so nothing is applied twice. Your flowie is synced; a hive's push waits for your yes; a project's change stays in
your working tree. The outcomes and the refreshed boards go back to the page in one upload, after a one-line preview and
your yes.

`--move` warns you when a workbench change waits for the same card, and the board marks such cards `↻`.

---

## With the neuroflow mod

A bare `/neuroflow:tasks` opens the boards as a pane drawn by code, no model turn: the project's, your flowie's and each hive's, read from the local copies as they are, and — read-only — the boards of the project's other repositories, from a local cache that is refreshed in the background when the boards open. It opens holding the keyboard, on the project board when it has open tasks, else on the first level with open tasks of this project, else on the first level with any open tasks.

| Key | What it does |
|---|---|
| `1`–`9` | Show a level's board: the level row reads `1: project 3   2: flowie 12   3: example-lab-hive 4` |
| Tab, `h` `j` `k` `l` | Move to a card — `h` and `l` between columns, `j` and `k` within one |
| Enter | On a card: pick it to move (it is marked `▸`); on a column: move it there |
| `x` | Cancel the pick |
| `r` · `q` · Esc | Read the boards again · close the pane · give the keys back to the prompt |

At project and flowie level the move runs at once as one `/tasks` command (`/neuroflow:tasks --level flowie --move {slug} {column}` at flowie level), and `/tasks` moves the file as usual. At a hive's level the move only goes into the prompt (`/neuroflow:tasks --level hive --hive {org-repo} --move {slug} {column}`) for you to send with Esc and then Enter: it ends in a push to the team's repository, which `/tasks` shows you and makes only after your yes. Any argument runs the full command.

---

## Task files

One markdown file per task at `tasks/{column}/{slug}.md` — the folder is the column. Default columns: `inbox`, `ready`, `active`, `review`, `meeting`, `done`, `archive` (a level can define its own in `tasks/config.json`).

Frontmatter: `title`, `status` (always the column), optional `owner`, `due`, `phase`, `tags`, `blocked_by`, then `created`, `updated`, and at flowie/hive level `project`. Tasks created from meeting action items carry a `source:` pointing at the meeting file (e.g. `project:meetings/2026-08-12-lab-meeting.md`). Owners are roster handles — never invented — and task files never contain machine-local paths.

Older task files (`{id}-{slug}.md`, `assignee:` or `responsible:`) stay readable and are moved into the new layout the next time they are written, under the same slug when `/tasks` accepts it. If one names two people, you are asked who owns the task first, so nobody is dropped.

---

## Related

- [`/flowie`](flowie.md) — personal level lives in your flowie repo
- [`/hive`](hive.md) — team level lives in the hive cache
- [`/meeting`](meeting.md) — action items become tasks via this spec
- [`/dashboard`](dashboard.md) — open tasks at every level at a glance
- [The neuroflow mod](../concepts/mods.md) — the board pane and what else the mod adds
