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
  - ~/.neuroflow/boards/                    # --project: cached boards of the project's other repositories
  - ~/.neuroflow/workbench/                 # pending.json: changes waiting on the claude.ai workbench
  - ~/.neuroflow/flowie/workbench.json      # --apply-web: the workbench record
writes:
  - ~/.neuroflow/boards/                    # --project refreshes it (machine-local, never synced)
  - .neuroflow/tasks/
  - ~/.neuroflow/flowie/tasks/
  - ~/.neuroflow/hives/{org-repo}/tasks/
  - ~/.neuroflow/workbench/                 # --apply-web: pending.json and ledger.json (machine-local)
  - ~/.neuroflow/flowie/workbench.json      # --apply-web: the record's copy of the page's preferences
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

**This project** is the project card this repo belongs to (`neuroflow:neuroflow-core` → **Project registry**): the `name` of this folder's entry in `~/.neuroflow/local-projects.json`, else the card whose `repos` list this folder or its `origin` remote URL — in the flowie or in a hive, a flowie pointer leading to its hive card. Its tasks, at every level, are those whose `project:` is the card's `id`. A registry written before one card per project may still name a project differently per level: then each level's own entry whose `repos` list this repo names it there. Without a link, no task is this project's — never guess one from names.

## Placement

A task goes on the narrowest board that everyone who must see it can read:

| Who must see it | Board |
|---|---|
| only the person | `flowie` |
| the team (anyone else in the hive) | `hive` — the default for a task of a team project |
| the people working in this repository, about its code or files (a pipeline step, a bug, a data folder) | `project` |

`--add` without `--level` proposes the board by this rule and says why in one line (*"hive example-lab-hive — the team works on this project"*), and the person can pick another. A personal to-do about a team project stays in the flowie. Never move a task to a wider board without the person's yes: a flowie task becomes visible to the team on the hive.

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
the flowie's and every hive clone's, read as the local clones are (nothing is pulled), and the boards of the project card's other repositories, read-only, from the cache in `~/.neuroflow/boards/` — refreshed in the background (`projects.py refresh`) when the boards open. The pane opens holding the
keyboard, on the project board when it has open tasks, else on the first level with open tasks of this project, else
on the first with any; the digits pick the level. Tab, or `h` `j` `k` `l`, reaches a card; Enter picks it (marked
`▸`), and Enter on a column moves it. A column shows five cards at a time, as below; `j` past the fifth shows the next
five. Where the pane is too narrow for the columns side by side (a dock beside the conversation), they stand one under
the other. The pane holds the keys while the person may be typing for the prompt, so an Enter that comes right after
another key does nothing, and at project and flowie level the mod runs the move only after the person's yes in a
question whose safe answer comes first — `/neuroflow:tasks --move {slug} {column}`, with `--level flowie` before
`--move` there — and the move runs as below. At
hive level it only puts `/neuroflow:tasks --level hive --hive {org-repo} --move {slug} {column}` in the prompt for the
person to send, because that move ends in a push to the team's repository (At end). `x` cancels a pick, `r` reads the
boards again, `q` closes. Any argument (`--list`, `--add`, `--move`, `--level`, `--hive`, …) runs this prose.

| Mode | What it does |
|---|---|
| *(none)* | Render the board for the chosen level |
| `--list` | Flat list for the chosen level — for narrow screens, or when the person asks for a list: grouped by column, then by `due` (soonest first, undated last) |
| `--add "title"` | Create a task in `inbox`. Ask for owner, due date or phase only if the person's phrasing implies them; at flowie and hive levels, ask which project if it is not obvious from the current repo |
| `--move {slug} {column}` | Move the task to another column (see Moves) |
| `--done {slug}` | Same as `--move {slug} done` |
| `--archive` | Move `done` tasks whose `updated` is older than `archive_after_days` to `archive` |
| `--apply-web` | Apply the changes queued on your claude.ai workbench (see Web changes) |
| `--project {id}` | One project across every level: run `python <neuroflow-core skill base dir>/scripts/projects.py view --project {id} --root . --json` (exit `0`; `1` — some repository's board could not be read: name it with the script's reason and show the rest; `2` — show the error). It pulls nothing in the flowie or the hives; it refreshes the machine-local cache of the card's other repositories (`~/.neuroflow/boards/`) from their remotes each time. Render one section per level (the card's place first, then the flowie, each hive, this repository and each other repository, naming where it was read from and, for a cached board, when it was fetched), open tasks only, overdue first; then the card's status and phase in one line, and each of the script's `problems` (two cards, a pointer that leads nowhere) as a line pointing at `/neuroflow:migrate` or `/sentinel`. With `--level`, it filters that level's board to the project instead |

## Moves

Before a move: if `~/.neuroflow/workbench/pending.json` lists this task's slug at this level, a change queued on the
claude.ai workbench waits for it — say so in one line, with the time the file names, and ask whether to move it anyway
or to run `--apply-web` first (a move here turns that change into a conflict).

1. Set `status: {column}` and `updated: {today}` in the task file where it is (Edit).
2. Move the file to `tasks/{column}/` — with `git mv` when the level is a git repo, so history follows it.
3. Commit the move by path — never `git add -A`:
   - `flowie`: `git -C ~/.neuroflow/flowie commit -m "tasks: move {slug} → {column}" -- tasks/{from}/{slug}.md tasks/{column}/{slug}.md`, then `git -C ~/.neuroflow/flowie pull --rebase --autostash && git -C ~/.neuroflow/flowie push` (the auto-sync hook only sees Edit/Write, not `git mv`).
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
- When `~/.neuroflow/workbench/pending.json` lists changes waiting on the claude.ai workbench, the cards it names are marked `↻` and one more line follows the footer: `↻ {n} workbench changes wait (oldest {age of its oldest}, as of {HH:MM}) — /neuroflow:tasks --apply-web`.

## Web changes (`--apply-web`)

A click on your claude.ai workbench (`/neuroflow:dashboard --web`) is an **intent**: a request this mode checks against
git and applies through Moves and each level's push rule. `neuroflow:neuroflow-core` → **Workbench snapshot** holds
the format and every rule; nothing applies a click on a timer, so it lands in git when you run this. `{wb}` stands for
`python <neuroflow-core skill base dir>/scripts/workbench.py`, `{scratch}` for a folder in this session's scratchpad;
every `{wb}` call takes `--json` (exit `0` clean, `1` findings to name, `2` an error: show it and stop).

1. **The workbench.** `{wb} record`; without a record say *"No workbench yet — /neuroflow:dashboard --web sets one up."*
   and stop. Load ArtifactData with ToolSearch when it is deferred. Before its first call, read the record's URL with the
   Artifact tool: if the result does not say you can edit it, Claude Code is signed into another claude.ai account —
   stop with one line naming the record's account label.
2. **Pickup.** ArtifactData `list` of collection `data/users/me/inbox/intents` with `out_dir` `{scratch}/intents`
   (follow its cursor to the end; finished intents are pruned, so it stays small). `{wb} pickup --intents
   {scratch}/intents` lists what this session may apply — pending intents of your flowie, the hives cloned here and this
   project, expired claims, a chain whole — with one claim batch, and names what it leaves: another project's (*open
   Claude Code in {project}*), a hive not cloned here, a fresh claim of another machine, a link waiting for an earlier
   one. Nothing to claim: say so, and what waits elsewhere, and go to step 7.
3. **Claim.** Send the claim batch with ArtifactData `batch`, `writes` exactly as printed (each pinned with
   `if_version`). Refused: another machine or session claimed first — list again and redo step 2.
4. **Check.** List the intents again into `{scratch}/intents2` (this sees a cancel or a release the page wrote since,
   and gives the versions the outcomes pin to), then `{wb} validate --intents {scratch}/intents2 --out
   {scratch}/plan.json`: one verdict per claimed intent — applied, coalesced, conflict, rejected or cancelled, with its
   reason — and per level the planned file changes.
5. **Apply, level by level.** Pull a hive clone first, as at command start. For each level with planned changes run
   `{wb} apply --plan {scratch}/plan.json --level {key}`: it changes the task files as Moves does — `status`, `updated`,
   `git mv`, and for an added card a new file in the Task file format — and in a flowie or hive clone stages them. It
   prints the commit to run, whose message carries one `Neuroflow-Intent: {id}` trailer per intent; a change it could
   not make is listed with its reason and gets no outcome (the next pickup tries again).
   - `flowie`: run the printed commit, then `git -C ~/.neuroflow/flowie pull --rebase --autostash && git -C ~/.neuroflow/flowie push`.
<!-- nf-rule: EGRESS-CONFIRM -->
   - `hive`: run the printed commit, show `git -C ~/.neuroflow/hives/{org-repo} log --stat @{u}..HEAD` and push only after your yes in this turn; a protected main branch takes a branch and a pull request (`neuroflow:phase-hive` → Pushing to the hive). A push you decline leaves the commit local; its outcome says *committed, not pushed*.
   - `project`: nothing more — the change stays in the working tree with your other changes, as Moves leaves it; `/git` commits it.
6. **Outcomes and the refreshed levels, one upload.** List the stored metas and the touched levels' parts into
   `{scratch}/remote` (as `/dashboard --web` step 7 does), then `{wb} export --out {scratch}/up --remote
   {scratch}/remote --outcomes {scratch}/plan.json --intents {scratch}/intents2 --level {each touched level}`: batches
   holding every decided intent's outcome — a change not yet in git gets none and stays claimed — and the refreshed
   levels, with the refresh guard as in `/dashboard --web`. Preview it in one line (*"Upload to your workbench: the
   outcomes of 4 changes and the refreshed hive board — 3 documents, 41 KB. Go ahead?"*) and send it only after your yes
   in this turn.
7. **What waits.** List the intents once more into `{scratch}/intents3` and run `{wb} pending --intents
   {scratch}/intents3`: it writes `~/.neuroflow/workbench/pending.json`, which the mod's band and board read. When the
   page's preferences changed, copy them into the record as `/dashboard --web` step 9 does.
8. **Report** one line per level: what was applied and where it stands (committed, pushed, in the working tree), each
   conflict with the card's current column, each rejection with its reason, and what waits elsewhere. If `.neuroflow/`
   exists: `## HH:MM — [tasks] applied {n} workbench changes ({levels})`.

## At end

- `flowie` level: files written with Edit/Write are committed and pushed by the flowie auto-sync hook; moves are committed as in Moves.
<!-- nf-rule: EGRESS-CONFIRM -->
- `hive` level: commit the changed task files by path (`tasks: {action} {slug}`), show the person what will be pushed to the shared hive repo, and push only after their explicit yes in this turn.
- `project` level: leave the change in the working tree; pushing to the shared project remote is the person's call.
- If `.neuroflow/` exists: append `## HH:MM — [tasks] {action}: {slug} {title} ({level})` to `.neuroflow/sessions/YYYY-MM-DD.md`.
