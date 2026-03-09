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

Shows the current project phase and phases worked on so far. Lets the user switch phase if they want.

---

## Steps

1. Read `project_config.md` — get the current active phase
2. Read root `flow.md` — list all phase subfolders that exist (these are phases that have been worked on)
3. Check `sessions/` — find the most recent session log and note the date

Print a compact status:

```
Current phase: ideation
Phases worked on: ideation, experiment
Last session: 2026-03-09

Available phases to switch to:
  [ ] grant-proposal
  [ ] data
  [ ] data-preprocess
  [ ] data-analyze
  [ ] paper-write
  [ ] paper-review
  [ ] tool-build
  [ ] tool-validate
  [ ] notes
```

4. Ask: "Do you want to switch to a different phase, or continue with the current one?"

5. If the user picks a different phase, update `project_config.md` and `.claude/CLAUDE.md` with the new active phase, then suggest the corresponding command.
