---
title: /dashboard
---

# `/neuroflow:dashboard`

**The project at a glance: phase map, upcoming deadlines, integrity state, open tasks at every level and the running
autoresearch loop.**

---

## With the neuroflow mod

The dashboard opens as a pane drawn by code — no model turn, no tokens — docked beside the conversation in a wide
terminal, or inline above the prompt otherwise. It stays current as files change.

| Key | Tab |
|---|---|
| `p` | **Phase** — the phase map (`●` current, `✔` visited, `○` recommended) and the next step; `s` opens the phase picker |
| `d` | **Deadlines** — dated rows of `.neuroflow/timeline.md` and the ethics expiry, with days left |
| `i` | **Integrity** — ethics approval, frozen preregistration, read-only raw-data folders, config problems; `f` freezes the preregistration after you confirm, `v` re-checks its hashes, `u` unfreezes it with a reason |
| `t` | **Tasks** — open tasks per level on one line (`project 3 · flowie 12 (2 Oddball EEG) · example-lab-hive 4`: the project, your flowie and each hive, with this project's share where that level links it, then the project's other repositories from the local cache of their boards), then the first open tasks across levels, each tagged with its level — this project's first, overdue first; `b` opens the boards, `r` reads them again |
| `l` | **Loop** — the running autoresearch loop: iteration, best snapshot, a quality sparkline and its open questions; `r` refreshes |

`/neuroflow:dashboard loop` opens it on a tab. The one-line band above the prompt opens it with `d`. When the project is on an
older neuroflow than the one installed, an `Update` line sits under the title and `m` runs [`/neuroflow:migrate`](migrate.md) —
or, while a wellbeing check-in still waits to sync to your flowie, puts it in the prompt: press Enter and the sync runs
first, so the migration finds your flowie clean.

Every symbol comes with a word, so the dashboard reads correctly without colour and with a screen reader.

## Without the mod

The same overview is printed once as a compact text block, read from the same files. Nothing is written. When the
project is on an older neuroflow version than the one installed, an `Update` line names [`/neuroflow:migrate`](migrate.md);
with the mod, the band above the prompt and the dashboard pane say the same.

---

## `--web` — your claude.ai workbench

`/neuroflow:dashboard --web` publishes and refreshes [your workbench](../concepts/workbench.md): one private claude.ai
page with a tab for your flowie, each hive you joined and each project you export it from — a board with drag and drop
and keyboard moves, the project list, the wiki and the level's panel. Git stays the only store; a click on the page is
a request that [`/neuroflow:tasks --apply-web`](tasks.md) checks and applies.

| Mode | What it does |
|---|---|
| `--web` | The first time: explains what would leave your machine, asks your consent, a name for this machine and which levels to mirror, then — after a one-line preview and your yes — publishes the page and uploads. After that: refreshes the levels, upgrades the page when the installed neuroflow ships a newer one, cleans up finished requests, and copies your page settings into your flowie |
| `--web --status` | Which account and page, the page's version against the plugin's, each level's consent and the team's opt-in, how many changes wait — nothing is uploaded |
| `--web --levels` | Choose again which levels are mirrored; one you take off is purged from the page |

Every upload asks first, every time: nothing is sent on a timer or at the end of another command. A hive or project is
mirrored only when its team set `workbench_mirror` (in `hive.md` or `project_config.md`); without it, it is left out
and the command says why. With the mod active, `--web` runs the full command too.

## Files read

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/timeline.md`, `.neuroflow/ethics/status.md`, `.neuroflow/preregistration/status.md`, `.neuroflow/tasks/`, `~/.neuroflow/flowie/tasks/` and each `~/.neuroflow/hives/{org-repo}/tasks/` (the local copies, never pulled), `~/.neuroflow/local-projects.json` and `~/.neuroflow/flowie/projects/projects.json` (which flowie project this is), each hive's `projects/projects.json` (which lab project it is there), `~/.neuroflow/user.yaml` (hive order), `.neuroflow/{phase}/autoresearch-loops.md` and the loops' `results.md` / `report.md`; with `--web` also the levels it mirrors, `~/.neuroflow/workbench/` and the workbench record (`~/.neuroflow/flowie/workbench.json`) |
| Writes | nothing, unless you freeze or unfreeze the preregistration from the integrity tab: then `freeze.py` writes `.neuroflow/preregistration/status.md`, the banners and `deviations.md`, and the mod adds a session line and a reasoning entry. `--web` writes your consent and levels to `~/.neuroflow/user.yaml`, `~/.neuroflow/workbench/pending.json`, the workbench record, and a session line — and uploads, after your yes, to your own claude.ai workbench |

## Related

- [`/phase`](phase.md) — the phase map and phase switching (a picker with the mod)
- [`/tasks`](tasks.md) — work the task boards (with the mod, every level in one pane)
- [The neuroflow mod](../concepts/mods.md) — what the mod adds and how to turn it on or off
