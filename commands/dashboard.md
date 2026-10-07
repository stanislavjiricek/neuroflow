---
name: dashboard
description: The project at a glance — phase map, upcoming deadlines, integrity state (ethics, frozen preregistration, raw data), task board counts, and the running autoresearch loop. Opens as a live pane when the neuroflow mod is active.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/timeline.md
  - .neuroflow/ethics/status.md
  - .neuroflow/preregistration/status.md
  - .neuroflow/tasks/
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
by code (tabs `p` phase · `d` deadlines · `i` integrity · `t` tasks · `l` loop, `s` to switch phase, `c` to close) and
keeps it current as files change. `/neuroflow:dashboard loop` opens it on a tab. On the integrity tab the person can
freeze the preregistration (`f`, after an explicit yes), re-check its hashes (`v`) or unfreeze it with a reason (`u`) —
the same `freeze.py` calls as `/preregistration` → Freeze, recorded as the person's action. The rest of this file is
what runs without the mod.

## Steps

1. Read `.neuroflow/project_config.md` (frontmatter per neuroflow-core → C1). If `.neuroflow/` does not exist, follow
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
Tasks     inbox 2 · ready 1 · active 1 · review 0 · done 4
Loop      connectivity (data-analyze) · running · iteration 23 · best v019 · quality ▁▂▃▅▆▇
          Q4 — delete the third control analysis?
```

   - **Phase**: the `recommended_phases` in order — `●` current, `✔` has a `.neuroflow/<phase>/` folder, `○` not
     started. Without `recommended_phases`, list the phases that have folders.
   - **Dates**: future rows of `.neuroflow/timeline.md` (`| YYYY-MM-DD | what | phase it gates |`), plus the ethics
     expiry; `⚠` within 3 days, `▸` within 14, `·` later.
   - **Integrity**: the frontmatter of `.neuroflow/ethics/status.md` and `.neuroflow/preregistration/status.md`
     (neuroflow-core → C2). A `frozen` or `approved` marker whose `set_by` is not `person` is shown with `?` and the
     words "not set by a person".
   - **Tasks**: the number of task files per column of `.neuroflow/tasks/`.
   - **Loop**: each row of the phases' `autoresearch-loops.md`; for a running loop, the `Running` column of its
     `results.md` as a sparkline and the open questions at the top of its `report.md`.
   Every symbol has a word next to it, so the block reads correctly without colour.
3. If something needs attention (a date within 3 days, an expired approval, a marker not set by a person, a legacy
   config format), end with one line naming the command that deals with it.

This command writes nothing, so it adds no session line.
