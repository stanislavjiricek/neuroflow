---
title: /phase
---

# `/neuroflow:phase`

**Show the current project phase and optionally switch to a different one.**

`/phase` gives you a quick status overview — what phase you're in, what phases have been worked on, and when the last session was. It also lets you switch phase if you want to jump to a different part of the pipeline.

---

## When to use it

- You want to quickly check where you are in the project
- You want to switch from one phase to another
- You're orienting yourself at the start of a session (though `/neuroflow` does this too)

---

## What it does

1. Reads `project_config.md` to get the current active phase
2. Reads root `flow.md` to list all phase subfolders that exist
3. Checks `sessions/` for the most recent session log

Then prints a compact status:

```
Current phase: ideation
Phases worked on: ideation, experiment
Last session: 2026-03-09

Available phases to switch to:
  [ ] grant-proposal
  [ ] tool-build
  [ ] tool-validate
  [ ] data
  [ ] data-preprocess
  [ ] data-analyze
  [ ] paper
  [ ] review
  [ ] notes
```

4. Asks: "Do you want to switch to a different phase, or continue with the current one?"

5. If you pick a different phase, it updates `project_config.md` and `.claude/CLAUDE.md` with the new active phase, then suggests the corresponding command.

---

## Example session

```
/neuroflow:phase
```

```
Current phase: data-preprocess
Phases worked on: ideation, experiment, data, data-preprocess
Last session: 2026-03-08

Continue with data-preprocess, or switch phase?

You: Switch to data-analyze — preprocessing is done.

Claude: ✅ Active phase updated to: data-analyze

        Run /neuroflow:data-analyze to continue.
```

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/sessions/` |
| Writes | `project_config.md` and `.claude/CLAUDE.md` (only if phase is changed) |

---

## Related commands

- [`/neuroflow`](neuroflow.md) — full project status + session start
- [`/sentinel`](sentinel.md) — audit project for consistency issues
