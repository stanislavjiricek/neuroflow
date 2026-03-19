---
name: phase
description: Show the current project phase and all phases worked on so far. Optionally switch to a different phase.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/sessions/
writes: []
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

   The complete ordered list of phases is:

   ```
   ideation → preregistration → grant-proposal → experiment →
   tool-build → tool-validate → data → data-preprocess →
   data-analyze → paper → write-report →
   notes → finance
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
     ○ tool-build
     ○ tool-validate
     ○ data
     ○ review
     ○ write-report
     ○ notes
     ○ finance

   Legend: ◉ current  ● visited  → recommended  ○ not started
   ```

   Show visited and current phases first (in pipeline order), then recommended phases, then the rest.

   If `recommended_phases` is absent from `project_config.md`, omit the `→` entries and the legend entry for "recommended". Suggest running `/neuroflow` to set up the project and generate phase recommendations.

   Below the phase map, print one line for the active personality mode:

   ```
   Personality mode: 🧐 Teacher (teacher)    [or ⚡ Executor (executor) / 🔍 Critic (critic)]
   ```

   If `default_mode` is absent from `project_config.md`, print: `Personality mode: not set (default: Executor — run /neuroflow to choose)`

5. Ask: "Do you want to switch to a different phase, or continue with the current one?"

6. If the user picks a different phase, update `project_config.md`, `.claude/CLAUDE.md`, and `.github/copilot-instructions.md` with the new active phase, then suggest the corresponding command.
