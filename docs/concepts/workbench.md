---
title: The workbench
---

# The claude.ai workbench

**Your own private page over your neuroflow memory: the task boards with drag and drop, your hives' project lists and
the wikis — mirrored from git, with every change going back through Claude Code.**

---

## What it is

The workbench is one private claude.ai page per person. It has a tab for each level you mirror — your
[flowie](../commands/flowie.md), each [hive](../commands/hive.md) you joined, and each project you export it from — and
every tab is drawn the same way:

- **Board** — the level's Kanban: drag a card to another column, or use the keyboard (`Enter` or `M` opens *Move to*,
  `Shift` + `←` / `→` moves a card one column, `U` undoes your last waiting move, `N` adds a task).
- **Projects** — the level's project registry, with each card's status and phase.
- **Wiki** — the level's wiki, with `[[links]]` between pages working.
- **The level** — the flowie's ideas, notes and meetings; a hive's team text, people, ideas and errata; a project's
  phase map, dates and integrity markers.

**Git stays the only store.** The page shows a snapshot of your files, and a click on it is a request — an *intent* —
that Claude Code checks against git and applies when you run [`/neuroflow:tasks --apply-web`](../commands/tasks.md).
Until then the card shows *waits for Claude Code*. Nothing on the page is research state that git does not hold: if
the page were deleted, you would lose only the clicks still waiting.

**It is yours alone.** The page's database rules let only its owner read or write anything, so a page shared by
mistake shows others nothing. You can change how it looks — theme, density, which fields a card shows, the order of
the tabs, hidden columns, display-only column limits, grouping by project or owner — and Claude Code copies those
settings into your flowie, so a rebuilt workbench keeps them.

---

## How a click lands in git

1. You move a card on the page. It writes an intent into your private database and draws the card in its new column,
   marked as waiting.
2. In Claude Code you run `/neuroflow:tasks --apply-web`. It claims the waiting intents, checks each one against git —
   has the task changed since your snapshot, is it still in the column you saw — and moves the task files exactly as
   [`/tasks`](../commands/tasks.md) does. Two moves of one card become one move; a card you added and then moved is
   written once, in its last column.
3. Each level follows its own rule: your flowie is committed and synced; a hive's commit is pushed **only after your
   yes**; a project's change stays in your working tree for you to commit with [`/git`](../commands/git.md). Every commit
   names the clicks it holds in a `Neuroflow-Intent` trailer, so nothing is applied twice.
4. The outcomes and the refreshed levels go back to the page in one upload — after a one-line preview and your yes.

The page's top line counts the clicks still waiting and says how old the oldest is. With the
[neuroflow mod](mods.md), the band above the prompt says how many workbench changes wait and `a` puts
`/neuroflow:tasks --apply-web` in the prompt; the boards mark those cards with `↻`. Without the mod, `/tasks` and
`/dashboard` say the same in their text.

---

## Setting it up

Run [`/neuroflow:dashboard --web`](../commands/dashboard.md) in one of your projects. The first time it explains what
the workbench is and what would leave your machine, asks for your consent, a name for this machine and which levels
to mirror, shows a one-line preview — and only after your yes publishes the page and uploads the levels. After that,
the same command refreshes it; `--web --status` reports without uploading, and `--web --levels` changes which levels
are mirrored.

You need a claude.ai subscription with Artifacts, and Claude Code signed into the same claude.ai account (an API key,
Bedrock or Vertex cannot publish one). The workbench belongs to the account that published it: if Claude Code is signed
into another account — a personal plan at home, an institute's organization at work — neuroflow stops and names the
account the workbench was recorded under, rather than making a second one.

---

## Who decides what is mirrored

| Level | You (`~/.neuroflow/user.yaml`) | The team (shared file) |
|---|---|---|
| your flowie | `workbench: on`, and the level in `workbench_levels` | — it is yours |
| a hive | the same | `workbench_mirror` in the frontmatter of the hive's `hive.md` |
| a project | the same | `workbench_mirror` in the `project_config.md` frontmatter |

`workbench_mirror` is `allow`, `allow-names` (adds the names and roles the roster lists — never an email address) or
`forbid`. **Without the key, nothing of that hive or project is mirrored**: it is the team's decision, recorded in a
commit the team can see, and `/dashboard --web` never writes it for you. Your other keys: `workbench_machine` (the
name each export shows), `workbench_index_only` (levels whose wiki goes up as an index without page bodies) and
`workbench_account` (which recorded workbench this machine uses). The record itself — the page's address, the account
label, the page version and a copy of your settings — lives in your flowie's `workbench.json`, or in `user.yaml`
when no flowie is linked.

---

## What leaves your machine, per source

Everything uploaded comes from this list; `python <neuroflow-core>/scripts/workbench.py sources` prints the same table,
and a test keeps the two equal.

<!-- workbench-sources:begin -->
| Source | Levels | Read from | What is uploaded |
|---|---|---|---|
| tasks | flowie, hive, project | `tasks/{column}/{slug}.md` | `cards`, `slug`, `file`, `column`, `title`, `owner`, `due`, `created`, `updated`, `phase`, `tags`, `project`, `blocked_by`, `sha256`, `notes`, `legacy`, `readable` — owner only as a roster handle; the first 1,000 characters of the notes; sha256 is the content hash; legacy and readable say whether the file is in an older format or carries a merge conflict |
| columns | flowie, hive, project | `tasks/config.json` | `columns`, `id`, `label`, `archive`, `closed`, `extra`, `archive_after_days` — extra marks a folder that config.json does not name |
| registry | flowie, hive | `projects/projects.json` | `registry`, `id`, `description`, `status`, `current_phase`, `visited_phases`, `repos`, `pointer`, `hive` — remote repository URLs only; a flowie pointer as its id and hive only |
| wiki | flowie, hive, project | `wiki/pages/**, wiki/index.md` | `pages`, `id`, `title`, `type`, `tags`, `status`, `updated`, `summary`, `sources`, `body` — no body with index only; [[links]] resolved to pages; sources, raw/ files and images named, never uploaded |
| people | flowie, hive, project | `your handle, members.md, collaborators` | `people`, `handle`, `name`, `role` — name and role only with allow-names; your own handle only at flowie level; never an email address |
| ideas | flowie, hive | `ideas.md, ideas-inbox.md (flowie)` | `ideas`, `ideas_inbox` — the text |
| notes | flowie | `notes/*.md` | `notes`, `file`, `title`, `date` — never the notes themselves |
| meetings | flowie, hive, project | `meetings/*.md` | `meetings`, `slug`, `title`, `date` — never attendees, agenda or notes |
| team | hive | `hive.md` | `team` — the text after the frontmatter: the team's name, description, norms and research directions |
| errata | hive | `errata/*.md` | `errata`, `dataset`, `columns`, `rows` — the table rows: date, scope, problem, workaround, reported_by |
| phases | project | `project_config.md, phase folders` | `project_name`, `active_phase`, `recommended_phases`, `visited`, `ethics_not_applicable`, `phases`, `card` — visited names the phase folders that exist, card the project's id in your registry; no other config field |
| dates | project | `timeline.md` | `dates`, `date`, `what`, `gates` — the dated rows; gates names the phase a date gates |
| integrity | project | `ethics/status.md, preregistration/status.md` | `ethics`, `prereg`, `status`, `expires`, `frozen_at`, `by_person` — by_person says whether a person set the marker; never approval documents |
| git | flowie, hive, project | `the clone` | `source`, `git`, `branch`, `head`, `upstream`, `upstream_head`, `ahead`, `behind`, `fetched_at`, `shallow`, `uncommitted_tasks`, `machine`, `applied`, `state`, `commit` — machine is your label for this computer; applied names your own clicks that reached git, by their Neuroflow-Intent trailers |
| the level | flowie, hive, project | `the export itself` | `snap_schema`, `level`, `part`, `kind`, `label`, `panel`, `sha256`, `intent_schema`, `exported_at`, `policy`, `working_tree`, `index_only`, `parts`, `withheld`, `counts`, `id`, `bytes`, `source`, `reason`, `cards`, `open`, `pages` — the level's name and kind, format versions, the export time, the team's workbench_mirror value, part sizes and hashes, counts, and which sources held items back and why — never the held items or their names |

Never uploaded: sessions/, review/, paper/xray-*, wiki/.pending/ and every other local-tier path; integrations.json, user.yaml, local-projects.json, boards/; fails/, finance/, reasoning/; the flowie's profile.md and wellbeing/; wiki raw/ files and images; email addresses, anywhere; meeting attendees, agendas and notes; machine-local paths.

Free text (titles, notes, descriptions, column labels, wiki pages, ideas, team text, errata rows, dated rows) goes through pii_scan.py's patterns, without its allowance for addresses the project lists: an email address becomes [email removed], a phone number [phone removed], an ID number your pii_scan config names [id removed]. An item with secret-like text or a name from your participant roster is held back whole, and so is one whose file name, tags or links carry personal data, as they travel unchanged. The preview names each item held back; the page only counts them.
<!-- workbench-sources:end -->

Every upload — the first publish, each refresh, each write-back of outcomes — needs a one-line preview and your yes
in that turn. Nothing is uploaded on a timer or at the end of another command. Teammates' text reaches your page as
text: it is never run as HTML, and only `http` and `https` links leave it.

---

## Limits

- **Not live.** A teammate's move appears on your workbench after they push and you refresh. Each tab says what it
  was made from: *working tree on main @ 3f5a2c1 + 2 uncommitted task changes · upstream fetched … · from laptop*.
- **Claude Code has to run** for a click to reach git; clicks wait until you run `/neuroflow:tasks --apply-web`.
- **One person, one account.** There is no shared board and no read-only page for a supervisor in this version; a
  teammate sees your changes in git.
- **Phones:** drag and drop needs a mouse or trackpad; on a touch screen use *Move to…*.
- **The store's limits:** 256 KiB per document, 25,000 documents and 50 writes per upload. Finished requests are
  deleted after 7 days, and a level you stop mirroring is purged.
- **Big wikis:** an export over 8 MB is flagged as slow to load; `workbench_index_only` sends a level's wiki as an index
  without page bodies.

---

## When something goes wrong

| What happened | What neuroflow does |
|---|---|
| Claude Code is not running when you move cards | The cards wait, marked as such; nothing is half done in git |
| A teammate changed or moved the task after your snapshot | A conflict: nothing is written, the card says why and where the task is now |
| A run stopped half way (closed laptop, a refused approval) | The claim expires after 30 minutes; the next run finds what the stopped run already changed — in git, and in a note on your machine that lasts until the commit exists — and commits it instead of repeating it, so an added card is never added twice. A stuck card offers *Release*, which cancels only a change that was not made yet |
| You declined the hive push | The commit stays local and the card says *committed, not pushed*; a later push updates it |
| Another machine of yours exported the level | Claude Code asks before overwriting, naming both machines; a clone that is behind is skipped |
| A newer neuroflow wrote the workbench from another machine | It is never overwritten: update neuroflow here first |
| The page is deleted | Only the waiting clicks are lost: `/dashboard --web` rebuilds it from git and restores your settings |
| The workbench database is full | The page says so; `/dashboard --web` deletes old requests and purged levels |

---

## Related

- [`/dashboard`](../commands/dashboard.md) — `--web` publishes and refreshes the workbench
- [`/tasks`](../commands/tasks.md) — `--apply-web` applies its clicks
- [Three levels](memory.md) — the flowie, the hive and the project
- [The neuroflow mod](mods.md) — the band, the board marks and the guard on uploads
- [neuroflow-core](../skills/neuroflow-core/SKILL.md) — **Workbench snapshot**, the format and every rule
