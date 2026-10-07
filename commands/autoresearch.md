---
name: autoresearch
description: Open-ended improvement loop for any research artifact — one managing agent makes a focused change each iteration, judges it against the current best, keeps or reverts. Its memory is a per-loop wiki it reads before and writes after every move. Folder lives next to the artifact; never stops on its own judgement — stops at the caps you set or when you stop it.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/objectives.md
  - .neuroflow/fails/core.md
  - .neuroflow/fails/science.md
  - .neuroflow/fails/ux.md
  - .neuroflow/{phase}/autoresearch-loops.md
  - .neuroflow/preregistration/flow.md
  - .neuroflow/preregistration/status.md
  - skills/autoresearch-protocol/SKILL.md
  - skills/autoresearch-protocol/references/integrity.md
writes:
  - .neuroflow/{phase}/autoresearch-loops.md   # pointer registry only
  - "{loop-location}/{name}_autoresearch/"      # loop folder — next to the artifact, user-chosen
  - .neuroflow/data-analyze/multiverse.md      # exploratory analysis loops only — append-only ledger
  - .neuroflow/data-analyze/flow.md            # lists the ledger
  - .neuroflow/reasoning/{phase}.jsonl         # the integrity-mode decision
  - .neuroflow/sessions/YYYY-MM-DD.md
lifecycle: full
produces:
  - .neuroflow/{phase}/autoresearch-loops.md
  - "{loop-location}/{name}_autoresearch/report.md"
---

# /autoresearch

Read the `neuroflow:autoresearch-protocol` skill first. Then follow the neuroflow-core lifecycle — its version notice included (**Command lifecycle**, step 3).

## What this command does

Starts (or resumes) an open-ended improvement loop for a set of tracked files. **One managing agent** makes one focused change per iteration, judges it against the current best (BETTER / WORSE / NO CHANGE), and keeps or reverts. The agent's long-term memory is a **per-loop wiki** it reads before every move and writes after every move — that is what lets a single agent run for hundreds of iterations and get smarter instead of going in circles. The loop never stops on its own judgement, and it always stops at the caps the user set (iterations and wall-clock time per run, cost where measurable), when the user stops it, or after repeated tool errors.

## Invocation forms

| Form | Behaviour |
|---|---|
| `/autoresearch` | Active phase from `project_config.md` |
| `/autoresearch {phase}` | Target the named phase explicitly |
| `/{phase} autoresearch` | Any phase command with `autoresearch` in the prompt triggers this |
| `/autoresearch --target path/to/file.py` | Pre-fill tracked file; skips the "which files?" question |
| `/autoresearch drive {name}` | **With the neuroflow mod:** the mod drives the registered loop `{name}`, one iteration per turn, checking `ar.py status` between turns (skill → *Driven by the neuroflow mod*). Run exactly one iteration, then end the turn. Without the mod, say that `drive` needs it and offer the normal resume |
| `/autoresearch stop` | **With the neuroflow mod:** ends a drive; the current iteration finishes, no new one starts |

## Steps

### 1 — Determine phase
Read `project_config.md` for the active phase (`active_phase` in its frontmatter), or use the phase given in the invocation.

### 2 — Check the pointer registry
Read `.neuroflow/{phase}/autoresearch-loops.md` (if it exists) to find loops already running in this phase.

**Resume:** if one or more loops are listed, confirm which to resume and its caps for this run (see Resume in the skill), then read that loop's `program.md`, `__thetask__.md`, `results.md`, **and its wiki** (index + synthesis), run `ar.py begin` then `ar.py status`, and go straight to the loop. A loop that touches analysis code but has no `integrity_mode` in its config gets the integrity question first; a loop with no caps gets the caps question first.

**New loop:** run the full INIT procedure from the autoresearch-protocol skill — which files, the integrity gate (loops that touch analysis code: confirmatory or exploratory, no default), name + location (default: next to the primary tracked file), criteria (3 layers), and the loop configuration interview.

> **Do the configuration interview properly — do not rush it.** Walk the user through every option ONE AT A TIME (integrity mode for analysis-touching loops, caps — `max_iterations` and `max_wall_clock` per run, no defaults, plus `max_cost` where this session can measure usage — branching, parameter sweep, literature search + sources + budget, evaluation mode, outputs + cadence, answer channel, wiki promotion), stating the default and trade-off for each and waiting for the answer. Do not batch them into one message, do not assume silent defaults, and do not start any iteration until you have rendered the complete config block and the user has explicitly confirmed it (the INIT hard gate). When you write `program.md`, include both the `## Loop configuration` block and the `## Iteration checklist` block.

### 3 — Run the loop
The managing agent runs the loop per the protocol in the skill until a stop condition fires: RECALL (`ar.py status` — caps and plateau — then re-read program.md incl. its iteration checklist + the wiki) → DECIDE → ACT (with parameter sweep when applicable) → JUDGE → KEEP/REVERT (`ar.py keep` / `ar.py revert`) → RECORD (write wiki + refresh report.md, **every iteration, never skipped**) → STEER → repeat. It does **not** spawn worker/evaluator subagents — it is one agent holding full context, with the wiki as externalized memory. The only optional subagent is a fresh evaluator when `evaluation: fresh-eval`.

It never stops on its own judgement — a plateau means change approach — and it always stops when a cap is reached, when the user stops it (Esc / Ctrl-C or a stop message), or after `max_consecutive_errors` tool errors in a row (Stopping in the skill).

## At end (cap reached, user stop, or error limit)

- Current best tracked files remain in place (last KEPT version); `results.md` and the wiki are already current — a move cut off mid-iteration is put back with `ar.py restore`, after asking if the stop came from Esc / Ctrl-C
- `report.md` opens with the stop reason; per `promote_to_project_wiki`, offer to promote durable wiki findings to the project wiki (`.neuroflow/wiki/` via the `neuroflow:wiki-protocol` ingest workflow)
- Append the stop line to `.neuroflow/sessions/YYYY-MM-DD.md` (`## HH:MM — [autoresearch] {name} stopped ({reason}) …` or `… interrupted …`)
- Update the loop's `flow.md` and the pointer registry status to `stopped: {reason}` or `interrupted`
- Never restart the loop on your own — `/autoresearch` resumes it, with a fresh budget per run
