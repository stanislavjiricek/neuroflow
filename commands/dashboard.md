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
  - ~/.neuroflow/user.yaml
  - .neuroflow/{phase}/autoresearch-loops.md
writes: []
lifecycle: light
requires:
  - .neuroflow/project_config.md
next:
  - phase
---

# /dashboard

Shows the project at a glance. It changes nothing.

**With the neuroflow mod active**, this command never reaches the model: the mod opens the dashboard as a pane drawn
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
   - **Loop**: each row of the phases' `autoresearch-loops.md`; for a running loop, the `Running` column of its
     `results.md` as a sparkline and the open questions at the top of its `report.md`.
   Every symbol has a word next to it, so the block reads correctly without colour.
3. If something needs attention (a date within 3 days, an expired approval, a marker not set by a person, a legacy
   config format), end with one line naming the command that deals with it.

This command writes nothing, so it adds no session line.
