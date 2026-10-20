---
name: dashboard
description: The project at a glance — phase map, upcoming deadlines, integrity state (ethics, frozen preregistration, raw data), open tasks at every level (project, flowie, hives), and the running autoresearch loop. Opens as a live pane when the neuroflow mod is active.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/timeline.md
  - .neuroflow/ethics/status.md
  - .neuroflow/preregistration/status.md
  - .neuroflow/tasks/
  - ~/.neuroflow/flowie/tasks/
  - ~/.neuroflow/hives/{org-repo}/tasks/
  - ~/.neuroflow/local-projects.json
  - ~/.neuroflow/flowie/projects/projects.json
  - ~/.neuroflow/hives/{org-repo}/projects/projects.json
  - ~/.neuroflow/boards/                # the project's other repositories' boards (cache, read-only)
  - ~/.neuroflow/user.yaml
  - .neuroflow/{phase}/autoresearch-loops.md
  - ~/.neuroflow/workbench/                  # --web: what waits on the claude.ai workbench
  - ~/.neuroflow/flowie/workbench.json       # --web: the workbench record, when a flowie is linked
  - ~/.neuroflow/hives/{org-repo}/hive.md    # --web: the team's workbench_mirror
writes:
  - ~/.neuroflow/user.yaml                   # --web only: the person's consent, levels and machine name (merged, never replaced)
  - ~/.neuroflow/workbench/                  # --web only: pending.json (machine-local)
  - ~/.neuroflow/flowie/workbench.json       # --web only: the workbench record, committed by path with the private sync
  - .neuroflow/sessions/YYYY-MM-DD.md         # --web only: one session line
lifecycle: light
requires:
  - .neuroflow/project_config.md
next:
  - phase
---

# /dashboard

Shows the project at a glance. It changes nothing — except `--web`, which publishes and refreshes your private claude.ai
workbench (below).

**With the neuroflow mod active**, this command (without `--web`) never reaches the model: the mod opens the dashboard as a pane drawn
by code (tabs `p` phase · `d` deadlines · `i` integrity · `t` tasks · `l` loop, `s` to switch phase, `m` to run
`/neuroflow:migrate` when the project is behind the installed neuroflow, `c` to close) and
keeps it current as files change. While a flowie sync of the mod's waits (a wellbeing check-in on the band), `m` puts
`/neuroflow:migrate` in the prompt instead: sent with Enter, it waits for the sync, so its pull finds the flowie clean. `/neuroflow:dashboard loop` opens it on a tab. The tasks tab shows the Tasks section
below; `b` opens the boards (`/neuroflow:tasks`) and `r` reads them again. On the integrity tab the person can
freeze the preregistration (`f`, after an explicit yes), re-check its hashes (`v`) or unfreeze it with a reason (`u`) —
the same `freeze.py` calls as `/preregistration` → Freeze, recorded as the person's action. The rest of this file is
what runs without the mod.

## Steps

1. Read `.neuroflow/project_config.md` (frontmatter per neuroflow-core → **project_config.md — the config contract**). If `.neuroflow/` does not exist, follow
   the neuroflow-core missing-project rule and stop.
2. Render one compact block, in this order, each section a few lines at most:

```
<project_name> · <active_phase> · <default_mode>

Phase     ✔ ideation  ✔ preregistration  ● data-analyze  ○ paper
Dates     ⚠ 2026-10-08  Abstract deadline — tomorrow
          ▸ 2026-10-19  ethics approval expires — in 12 days
Integrity ✔ ethics approved · expires 2027-06-30 · model may read: pseudonymised data
          ■ preregistration frozen 2026-10-01 · 2 files (set by a person)
          ■ read-only raw data: sourcedata/
Tasks     project 3 · flowie 12 (2 Oddball EEG) · example-lab-hive 4
          [project] ⚠ Rerun ICA on sub-07 @jana due 10-06
          [flowie] ◆ Read the N2pc review due 10-20
          ◆ this project (Oddball EEG) · ⚠ overdue
Loop      connectivity (data-analyze) · running · iteration 23 · best v019 · quality ▁▂▃▅▆▇
          Q4 — delete the third control analysis?
```

   - **Update** (only when the version notice applies — neuroflow-core → **Command lifecycle**, step 3, which compares
     the versions number by number; the running one is in `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`): one line under the header with the notice, verbatim. It stands in for the
     separate one-line notice, so the person reads it once:
     `Update    ↑ neuroflow 0.2.22 is installed; this project is on 0.2.21 — run /neuroflow:migrate to bring the project, your flowie and the team hive up to date`.
   - **Phase**: the `recommended_phases` in order — `●` current, `✔` has a `.neuroflow/<phase>/` folder, `○` not
     started. Without `recommended_phases`, list the phases that have folders.
   - **Dates**: future rows of `.neuroflow/timeline.md` (`| YYYY-MM-DD | what | phase it gates |`), plus the ethics
     expiry; `⚠` within 3 days, `▸` within 14, `·` later.
   - **Integrity**: the frontmatter of `.neuroflow/ethics/status.md` and `.neuroflow/preregistration/status.md`
     (neuroflow-core → **Integrity markers**). A `frozen` or `approved` marker whose `set_by` is not `person` is shown with `?` and the
     words "not set by a person".
   - **Tasks**: open tasks per level on one line — `project` (`.neuroflow/tasks/`), `flowie` (`~/.neuroflow/flowie/tasks/`)
     and each hive clone with a `tasks/` folder (`~/.neuroflow/hives/{org-repo}/`; the hives `~/.neuroflow/user.yaml`
     lists first, the others alphabetically) — counting every column but `done` and the archive ones, with this
     project's share in brackets at flowie and hive level (this project as `/tasks` → Levels defines it). Then the
     first few open tasks across levels, each tagged `[level]`: this project's first (`◆` at flowie and hive level),
     overdue (`⚠`) first, then by due date; a last line names the marks shown. Read the local files as they are; pull
     nothing. A level whose storage does not exist is left out (the project's is always shown).
     The boards of the project card's other repositories (`neuroflow:neuroflow-core` → **Project registry**) follow,
     each as `[owner/repo]`, from the cache in `~/.neuroflow/boards/` as it is, with the time it was fetched.
   - **Loop**: each row of the phases' `autoresearch-loops.md`; for a running loop, the `Running` column of its
     `results.md` as a sparkline and the open questions at the top of its `report.md`.
   Every symbol has a word next to it, so the block reads correctly without colour.
3. If something needs attention (a date within 3 days, an expired approval, a marker not set by a person, a legacy
   config format), end with one line naming the command that deals with it. When `~/.neuroflow/workbench/pending.json`
   lists changes waiting on the workbench, add one line: `↻ {n} workbench changes wait (as of {HH:MM}) — /neuroflow:tasks --apply-web`.

Without `--web` this command writes nothing, so it adds no session line.

## `--web` — your claude.ai workbench

One private claude.ai page over your own levels: a tab for your flowie, each hive you joined and each project you export
it from, each drawn the same way — the board with drag and drop and keyboard moves, the project list, the wiki and the
level's panel. `neuroflow:neuroflow-core` → **Workbench snapshot** holds the format and every rule this mode follows.
Git stays the only store: the page shows a snapshot, and a click there is a request that `/neuroflow:tasks --apply-web`
checks against git and applies. With the mod active, `--web` still runs this prose.

`--web` sets the workbench up the first time and refreshes it after; `--web --status` reports and uploads nothing;
`--web --levels` changes which levels are mirrored. Below, `{wb}` stands for
`python <neuroflow-core skill base dir>/scripts/workbench.py` and `{scratch}` for a folder in this session's scratchpad.
Every `{wb}` call takes `--json`; exit `0` is clean, `1` names findings (say them), `2` is an error (show it and stop).

1. **Tools.** The workbench needs the Artifact and ArtifactData tools — a claude.ai subscription with Artifacts, not an
   API key, Bedrock or Vertex. Load ArtifactData with ToolSearch when it is deferred. If either is missing, say so in
   one sentence (the terminal boards — `/neuroflow:tasks` and the mod's board pane — work as before) and stop.
2. **Your consent and levels.** `{wb} levels` lists this machine's levels: the key, the team's opt-in and yours.
   - Without `workbench: on` in `~/.neuroflow/user.yaml`: say in three lines what the workbench is, that it lives in the
     claude.ai account Claude Code is signed into, and what leaves — show the table `{wb} sources` prints — then ask
     (AskUserQuestion: *Set it up* / *Not now*). Only after a yes, write `workbench: on` (merge into the file, never
     replace it).
   - Without `workbench_machine`: ask once for a name for this machine (suggest two, e.g. *laptop*, *lab desktop*) and
     write it.
   - On the first run and with `--levels`: ask which levels to mirror (AskUserQuestion, several may be picked), offering
     only those the team allows; name the others with the reason `{wb} levels` gives — never write a team's
     `workbench_mirror` yourself. Write `workbench_levels` as a JSON list, and `workbench_index_only` for levels whose
     wiki should go up without page bodies.
3. **Export.** `{wb} export --out {scratch}/wb`: per level the documents, the size, the cards and wiki pages, the
   freshness label, and every item held back with its reason (exit `1`).
4. **The record and the account.** `{wb} record`.
   - With a record: read its URL with the Artifact tool (`action: read`) before any ArtifactData call. If the result does
     not say you can edit it, Claude Code is signed into another account than the workbench's: stop with one line that
     names the record's account label, and never create a second workbench without asking. Run
     `{wb} page --check {the file the read saved}`: `changed` means someone edited the live page since neuroflow
     published it — ask before replacing it; `upgrade: true` means the plugin's page is newer — step 6 republishes it.
   - Without one: ask for an account label (*personal*, *institute*, …). Without a linked flowie, an Artifact `list` may
     show a workbench made on another machine (title *neuroflow workbench*): ask whether it is yours and use its URL
     rather than making another.
<!-- nf-rule: EGRESS-CONFIRM -->
5. **Preview, then your yes.** One line, then one question: *"Upload to your private workbench ({account}): {levels} —
   {n} documents, {KB} KB{; and publish the page, neuroflow template {t}, {KB} KB}. Go ahead?"* Nothing leaves before a
   yes in this turn. Without one, upload nothing and say how to run it later. No upload ever runs on a timer or at the end
   of another command.
6. **Publish — the first time, or to upgrade.** `{wb} stage --out {scratch}/page` prints the file, its hashes, the
   capabilities, the contract, the title, the icon and the description. Read the staged file in full (the Artifact tool
   requires it for a file Claude did not write), then publish it with the Artifact tool: `file_path` the staged file,
   `capabilities` and `contract` exactly as printed; `icon` and `description` on the first publish; to upgrade, the
   record's `url`. Then record it: `{wb} record --set url=… --set account=… --set template_version=… --set contract=…
   --set page_sha256=… --set published_at=…`.
7. **Upload.** List what the store holds: ArtifactData `list` of collection `data/users/me`, and of
   `data/users/me/{level}/parts` for each level being written, each with `out_dir` `{scratch}/remote`. Then
   `{wb} export --out {scratch}/wb --remote {scratch}/remote --fetch`. Its `guard` gives each level a verdict: `write`;
   `ask` — another machine or branch exported it: ask its one-line question, and after a yes rerun with
   `--overwrite {level}`; `skip` or `refuse` — say why, nothing is written for that level. Exit `2` because the listing
   shows no versions: write the versions the ArtifactData results named as `{"path": version}` into a file and rerun with
   `--versions {file}`. Send each of its `batches` with ArtifactData `batch`, `writes` exactly as printed (parts first,
   the meta last). A batch refused because a document changed: list again and redo it — never force.
8. **Clean up.** ArtifactData `list` of `data/users/me/inbox/intents` (`out_dir` `{scratch}/intents`), then
   `{wb} gc --intents {scratch}/intents --remote {scratch}/remote`: finished intents older than 7 days, and every document
   of a level no longer mirrored (parts first, then the meta). A delete sends nothing; send its batches.
9. **Check and record.** ArtifactData `list` of `data/users/me` with `as_level: admin` must come back empty — the
   owner-only rules hide the workbench even from an editor; report it as *owner-only rules checked {date}*. Copy the
   page's preferences into the record: ArtifactData `get` of `data/users/me` · `prefs` (`out_dir`), then
   `{wb} record --prefs {file}`; when it reports `changed` with a flowie, commit by path as it prints, then
   `git -C ~/.neuroflow/flowie pull --rebase --autostash && git -C ~/.neuroflow/flowie push` (the private sync). Write
   what waits: `{wb} pending --intents {scratch}/intents`; when changes wait, offer `/neuroflow:tasks --apply-web`.
10. **The first time only:** give the link and offer to pin it to the claude.ai sidebar (AskUserQuestion); pin only after
    a yes.
11. If `.neuroflow/` exists: `## HH:MM — [dashboard] workbench refreshed: {levels} ({n} documents)`.

`--web --status` reads local files only — the record, `{wb} levels` and `~/.neuroflow/workbench/pending.json` — and
prints the account, the URL, the page's template against the plugin's, each level with its consent and the team's
opt-in, and how many changes wait. It uploads nothing.

`--web --levels` asks step 2's level question again; a level taken off is purged in step 8, after the step 5 yes.
