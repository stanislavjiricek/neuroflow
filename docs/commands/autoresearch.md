---
title: /autoresearch
---

# `/neuroflow:autoresearch`

**Infinite improvement loop — point it at any file(s) and one managing agent improves them indefinitely, keeping or reverting each change based on whether it improved the artifact. Its memory is a per-loop wiki it reads before and writes after every move.**

Inspired by Andrej Karpathy's autoresearch. Runs until you interrupt it.

---

## When to use it

- You want to improve a hypothesis, paper section, grant aim, or analysis script overnight
- You want to leave something running and come back to a better version
- You want a knowledge base of everything that was tried — what worked and what didn't
- You want to explore what "continuous improvement" looks like for a research artifact

---

## How it works

### One agent, one brain

A **single managing agent** runs the whole loop and holds the thread of all iterations — it makes the change and judges it, no subagent fan-out. Its long-term memory is a **per-loop wiki** that it reads before deciding every move and writes after every move. The wiki is what lets a single agent run an infinite loop and *compound* — without it the agent would re-tread dead ends forever. Failures are recorded as deliberately as wins, because knowing what fails is what prunes the search.

### First run — initialization

1. Claude determines the active phase from `project_config.md`
2. You name the files to improve (or use `--target path/to/file.py`)
3. You confirm the **loop name and location** — the folder defaults to sitting next to the artifact (e.g. `scripts/analysis/connectivity_autoresearch/`), overridable
4. Criteria are built in three layers: phase defaults → context-inferred → your additions
5. A **configuration interview** sets the loop's behaviour, one option at a time: branching, parameter sweep (scan a parameter's values within a single iteration; default on), literature search, evaluation mode, outputs, answer channel, wiki promotion. The full config is shown back to you for explicit sign-off — **no iteration runs until you confirm it**
6. The wiki is initialized, a baseline snapshot saved to `history/v000/`, and a pointer added to `.neuroflow/{phase}/autoresearch-loops.md`

### The loop — never stops until you interrupt

Each iteration:
1. **Recall** — read the wiki (current thesis, prior attempts on this criterion) so the next move is informed, not blind
2. **Decide** — pick the weakest criterion and one focused move; if the move tunes a scannable parameter, sweep several values within the iteration and keep the best; if out of ideas, optionally search the literature and ingest findings into the wiki
3. **Act** — make one surgical change
4. **Judge** — compare to the current best; `BETTER / WORSE / NO CHANGE`
5. **Keep or revert** — BETTER archives to `history/vNNN/`; otherwise restore the best
6. **Record** — write an attempt page to the wiki (what, why, outcome, reasoning), update the report and results table

### Steering it while it runs

The agent asks you questions without ever stopping. Open questions sit at the top of `report.md`. Answer them in the session (`A3: eLife`) or via the `answers.md` inbox — the agent picks up the answer on the next iteration, acts on it, and removes the question. Because every state is a snapshot, it can re-branch from an earlier best if you steer it elsewhere.

---

## Invocation forms

| Form | Behaviour |
|---|---|
| `/autoresearch` | Uses active phase from `project_config.md` |
| `/autoresearch paper` | Targets the paper phase explicitly |
| `/paper autoresearch` | Any phase command + `autoresearch` keyword triggers this |
| `/paper autoresearch --target manuscript/intro.md` | Pre-fills the tracked file |

---

## Outputs

Each surface has one job; all are optional except `report.md`.

| File | Audience | Job |
|---|---|---|
| `report.md` | you | narrative + open questions — the steering surface |
| `report.pdf` | you | optional read-only snapshot |
| `results.md` | dashboard | numeric iteration table |
| `server.py` | you | optional live dashboard at `localhost:8765` — renders the report (open questions + narrative) and the trend charts on one page; auto-refresh with `?watch=1` |
| `wiki/` | the agent | its brain — every attempt, pattern, and ingested paper |

---

## Files created

```
{location}/{name}_autoresearch/        e.g. scripts/analysis/connectivity_autoresearch/
├── wiki/               # the agent's brain (attempts, concepts, sources, synthesis)
├── program.md          # task + criteria + config block (edit to guide the loop)
├── __thetask__.md      # pointer to tracked files
├── results.md          # iteration table → dashboard
├── report.md           # human report + open questions
├── answers.md          # your answer inbox
├── server.py           # optional dashboard
├── flow.md
└── history/            # v000 baseline, then a snapshot per KEPT iteration

.neuroflow/{phase}/autoresearch-loops.md   # pointer registry only
```

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, the pointer registry, tracked external files, the loop's `program.md` / `wiki/` / `results.md` / `history/` |
| Writes | the loop folder next to the artifact, tracked external files (on KEPT), `history/vNNN/`, the pointer registry, session log |

---

## Related

- [`neuroflow:autoresearch` skill](../skills/autoresearch/SKILL.md) — full protocol, wiki format, criteria, dashboard template
- [`neuroflow:wiki`](../skills/wiki/SKILL.md) — the page format the loop wiki uses; durable findings are promoted here
- [`/paper`](paper.md) — uses the worker-critic loop (bounded, 3 iterations) for section drafting
- [`/pipeline`](pipeline.md) — multi-step orchestration across phases
