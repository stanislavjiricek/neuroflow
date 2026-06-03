---
name: autoresearch
description: Infinite improvement loop for any research artifact — one managing agent makes a focused change each iteration, judges it against the current best, keeps or reverts. Its memory is a per-loop wiki it reads before and writes after every move. Folder lives next to the artifact; never stops until interrupted.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/objectives.md
  - .neuroflow/fails/core.md
  - .neuroflow/fails/science.md
  - .neuroflow/fails/ux.md
  - .neuroflow/{phase}/autoresearch-loops.md
  - skills/autoresearch/SKILL.md
writes:
  - .neuroflow/{phase}/autoresearch-loops.md   # pointer registry only
  - "{loop-location}/{name}_autoresearch/"      # loop folder — next to the artifact, user-chosen
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /autoresearch

Read the `neuroflow:autoresearch` skill first. Then follow the neuroflow-core lifecycle.

## What this command does

Starts (or resumes) an infinite improvement loop for a set of tracked files. **One managing agent** makes one focused change per iteration, judges it against the current best (BETTER / WORSE / NO CHANGE), and keeps or reverts. The agent's long-term memory is a **per-loop wiki** it reads before every move and writes after every move — that is what lets a single agent run forever and get smarter instead of going in circles. The loop never stops until the user interrupts it.

## Invocation forms

| Form | Behaviour |
|---|---|
| `/autoresearch` | Active phase from `project_config.md` |
| `/autoresearch {phase}` | Target the named phase explicitly |
| `/{phase} autoresearch` | Any phase command with `autoresearch` in the prompt triggers this |
| `/autoresearch --target path/to/file.py` | Pre-fill tracked file; skips the "which files?" question |

## Steps

### 1 — Determine phase
Read `project_config.md` for the active phase, or use the phase given in the invocation.

### 2 — Check the pointer registry
Read `.neuroflow/{phase}/autoresearch-loops.md` (if it exists) to find loops already running in this phase.

**Resume:** if one or more loops are listed, confirm which to resume (see Resume in the skill), then read that loop's `program.md`, `__thetask__.md`, `results.md`, **and its wiki** (index + synthesis), and go straight to the loop.

**New loop:** run the full INIT procedure from the autoresearch skill — which files, name + location (default: next to the primary tracked file), criteria (3 layers), and the loop configuration interview (branching, literature search, evaluation mode, outputs, answer channel, wiki promotion).

### 3 — Run the loop
The managing agent runs the loop indefinitely per the protocol in the skill: RECALL (read wiki) → DECIDE → ACT → JUDGE → KEEP/REVERT → RECORD (write wiki) → STEER → repeat. It does **not** spawn worker/evaluator subagents — it is one agent holding full context, with the wiki as externalized memory. The only optional subagent is a fresh evaluator when `evaluation: fresh-eval`.

## At end (on interruption)

- Current best tracked files remain in place (last KEPT version); `results.md` and the wiki are already current
- Per `promote_to_project_wiki`, offer to promote durable wiki findings to the project wiki (`.neuroflow/wiki/` via `neuroflow:wiki`)
- Append the final milestone to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update the loop's `flow.md` and the pointer registry status to `interrupted`
