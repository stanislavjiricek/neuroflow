---
name: phase
description: Show the current project phase and all phases worked on so far. Optionally switch to a different phase.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/sessions/
writes:
  - .neuroflow/project_config.md
  - .claude/CLAUDE.md
  - .github/copilot-instructions.md
  - AGENTS.md
  - ~/.neuroflow/flowie/projects/
---

# /phase

## What this command does

Shows a visual phase map of the project — current phase, visited phases, recommended phases, and untouched phases. Lets the user switch phase if they want.

---

## Steps

1. Read `project_config.md` — extract:
   - `active_phase` (the current active phase)
   - `recommended_phases` (list suggested after the initial interview, if present)
   - `default_mode` (personality mode: `teacher`, `executor`, or `critic` — absent if not set)

2. Check which phase subfolders exist inside `.neuroflow/` — these are phases that have been worked on (a `.neuroflow/{phase}/` directory is present).

3. Check `sessions/` — find the most recent session log and note the date.

4. Print a visual phase map. Use these markers:

   - `◉` — current active phase
   - `●` — visited: a `.neuroflow/{phase}/` subfolder already exists (work has been done here)
   - `→` — recommended: suggested by neuroflow after the initial interview (listed in `recommended_phases` in `project_config.md`), but not yet visited
   - `○` — not started: no subfolder, not recommended

   The complete ordered list of phases is the **Phase taxonomy** in `neuroflow:neuroflow-core` — that section is canonical; if this file ever disagrees, core wins. Current canonical order:

   ```
   ideation → preregistration → grant-proposal → finance → experiment →
   tool-build → tool-validate → data → data-preprocess → data-analyze →
   brain-build → brain-optimize → brain-run → paper → review → poster →
   write-report → output   (+ notes — cadence-free, shown last)
   ```

   Print the map in order. Example output:

   ```
   Phase map — Last session: 2026-03-09

     ● ideation
     ◉ experiment          ← current
     → data-preprocess     ← recommended
     → data-analyze        ← recommended
     → paper               ← recommended
     ○ preregistration
     ○ grant-proposal
     ○ finance
     ○ tool-build
     ○ tool-validate
     ○ data
     ○ brain-build
     ○ brain-optimize
     ○ brain-run
     ○ review
     ○ poster
     ○ write-report
     ○ output
     ○ notes

   Legend: ◉ current  ● visited  → recommended  ○ not started
   ```

   Show visited and current phases first (in pipeline order), then recommended phases, then the rest.

   If `recommended_phases` is absent from `project_config.md`, omit the `→` entries and the legend entry for "recommended". Suggest running `/neuroflow` to set up the project and generate phase recommendations.

   **Below the phase map, render upcoming deadlines** from `.neuroflow/timeline.md` (if it exists and has entries): the next 3 entries with future dates, `⚠` on anything within 14 days, `❌ OVERDUE` on past dates that are not marked done:

   ```
   Deadlines:
     ⚠ 2026-08-25  SfN abstract deadline          (paper)
       2026-10-01  Ethics approval expires        (data)
   ```

   Skip the block silently if `timeline.md` is absent or empty.

   Below that, print one line for the active personality mode:

   ```
   Personality mode: 🧐 Teacher (teacher)    [or ⚡ Executor (executor) / 🔍 Critic (critic)]
   ```

   If `default_mode` is absent from `project_config.md`, print: `Personality mode: not set (default: Executor — run /neuroflow to choose)`

5. Ask: "Do you want to switch to a different phase, or continue with the current one?"

6. If the user picks a different phase, update `project_config.md`, `.claude/CLAUDE.md`, `.github/copilot-instructions.md`, and `AGENTS.md` (all three agent-instruction mirrors must stay identical) with the new active phase, then suggest the corresponding command.

7. **Flowie phase sync:** After updating `project_config.md`, check whether `flowie_profiles` is set and non-empty in `project_config.md`. If it is, and `~/.neuroflow/flowie/` exists as a git repo, use the first entry (`flowie_profiles[0]`):

   - Pull: `git -C ~/.neuroflow/flowie pull --rebase origin main || true`
   - Read `projects/projects.json` — find the project entry where `"id"` matches the linked project name
   - Update `current_phase` to the new phase
   - Append to `visited_phases` if this phase is not already listed: `{ "phase": "{new_phase}", "entered": "{YYYY-MM-DD}" }`
   - Write updated `projects/projects.json`
   - Read `projects/{name}.md` — append a new row to the Phase timeline table: `| {new_phase} | {YYYY-MM-DD} |`
   - Commit and push: `git -C ~/.neuroflow/flowie add projects/projects.json "projects/{name}.md" && git -C ~/.neuroflow/flowie commit -m "phase: {project} → {new_phase}" && git -C ~/.neuroflow/flowie push || true`

   If `~/.neuroflow/flowie/` does not exist, `flowie_profiles` is absent or empty, or any git operation fails, skip silently — never surface flowie errors to the user during a phase switch.
