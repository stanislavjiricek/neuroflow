---
name: autoresearch
description: Infinite improvement loop for any research artifact — point it at any file(s), and it runs a worker-evaluator loop indefinitely: one focused change per iteration, keep or revert based on relative comparison, dashboard at localhost:8765. Never stops until interrupted.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/objectives.md
  - .neuroflow/fails/core.md
  - .neuroflow/fails/science.md
  - .neuroflow/fails/ux.md
  - .neuroflow/{phase}/flow.md
  - .neuroflow/{phase}/autoresearch/program.md
  - .neuroflow/{phase}/autoresearch/__thetask__.md
  - .neuroflow/{phase}/autoresearch/results.md
  - skills/autoresearch/SKILL.md
writes:
  - .neuroflow/{phase}/autoresearch/
  - .neuroflow/{phase}/autoresearch/flow.md
  - .neuroflow/{phase}/autoresearch/program.md
  - .neuroflow/{phase}/autoresearch/__thetask__.md
  - .neuroflow/{phase}/autoresearch/results.md
  - .neuroflow/{phase}/autoresearch/server.py
  - .neuroflow/{phase}/autoresearch/history/
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /autoresearch

Read the `neuroflow:autoresearch` skill first. Then follow the neuroflow-core lifecycle.

## What this command does

Starts (or resumes) an infinite improvement loop for a set of tracked files in the active phase. A worker agent makes one focused change per iteration; an evaluator agent compares the result to the previous best and returns BETTER / WORSE / NO CHANGE. The loop never stops until the user interrupts it.

## Invocation forms

| Form | Behaviour |
|---|---|
| `/autoresearch` | Uses active phase from `project_config.md` |
| `/autoresearch {phase}` | Targets the named phase explicitly |
| `/{phase} autoresearch` | Any phase command with `autoresearch` in the prompt triggers this |
| `/autoresearch --target path/to/file.md` | Pre-fills tracked file; skips the "which files?" question |

## Steps

### 1 — Determine phase

Read `project_config.md` to get the active phase. If a phase was provided explicitly in the invocation, use that instead.

### 2 — Check for existing loop

Check whether `.neuroflow/{phase}/autoresearch/` already exists.

**If it exists (resume):**
- Read `program.md`, `__thetask__.md`, and `results.md`
- Confirm: *"Resuming autoresearch for {phase}. {N} iterations already logged. Best snapshot: {snapshot}. Continue? [Y/n]"*
- If yes, go directly to the loop (skip INIT)

**If it does not exist (new loop):**
- Run the full INIT procedure from the autoresearch skill

### 3 — Run the loop

Spawn the `neuroflow:autoresearch` agent and pass it:
- The active phase
- The `.neuroflow/{phase}/autoresearch/` folder path
- The contents of `program.md` and `__thetask__.md`
- The current `results.md` (or empty if new)

The agent runs the loop indefinitely per the protocol in the autoresearch skill.

## At end (on interruption)

When the user interrupts the loop:
- The current best tracked files remain in place (last KEPT version)
- `results.md` is already up to date
- Append final milestone to `.neuroflow/sessions/YYYY-MM-DD.md`:
  `## HH:MM — [autoresearch/{phase}] loop interrupted at iteration {N} — best: {snapshot}`
- Update `.neuroflow/{phase}/autoresearch/flow.md`
