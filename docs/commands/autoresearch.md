---
title: /autoresearch
---

# `/neuroflow:autoresearch`

**Open-ended improvement loop — point it at any file(s) and one managing agent keeps improving them, keeping or reverting each change based on whether it improved the artifact. Its memory is a per-loop wiki it reads before and writes after every move.**

Inspired by Andrej Karpathy's autoresearch. Runs until it reaches the caps you set — or until you stop it.

---

## When to use it

- You want to improve a hypothesis, paper section, grant aim, or analysis script overnight
- You want to leave something running and come back to a better version
- You want a knowledge base of everything that was tried — what worked and what didn't
- You want to explore what "continuous improvement" looks like for a research artifact

---

## How it works

### One agent, one brain

A **single managing agent** runs the whole loop and holds the thread of all iterations — it makes the change and judges it, no subagent fan-out. Its long-term memory is a **per-loop wiki** that it reads before deciding every move and writes after every move. The wiki is what lets a single agent run a long loop and *compound* — without it the agent would re-tread dead ends forever. Failures are recorded as deliberately as wins, because knowing what fails is what prunes the search.

### First run — initialization

1. Claude determines the active phase from `project_config.md`
2. You name the files to improve (or use `--target path/to/file.py`)
3. **Integrity gate** — if the files compute results from your study data, you choose what the loop is for: **confirmatory** or **exploratory** (see [Research integrity](#research-integrity)). There is no default
4. You confirm the **loop name and location** — the folder defaults to sitting next to the artifact (e.g. `scripts/analysis/connectivity_autoresearch/`), overridable
5. Criteria are built in three layers: phase defaults → context-inferred → your additions
6. A **configuration interview** sets the loop's behaviour, one option at a time: **caps** (the most iterations and the longest wall-clock time per run, plus a cost limit where usage can be measured — no defaults; a loop without a cap is never started), branching, parameter sweep (scan a parameter's values within a single iteration; default on, off for confirmatory loops), literature search, evaluation mode, outputs, answer channel, wiki promotion. The full config is shown back to you for explicit sign-off — **no iteration runs until you confirm it**
7. The wiki is initialized, a baseline snapshot saved to `history/v000/`, and a pointer added to `.neuroflow/{phase}/autoresearch-loops.md`

### The loop — runs until a cap, or until you stop it

Each iteration:
1. **Recall** — read the wiki (current thesis, prior attempts on this criterion) so the next move is informed, not blind
2. **Decide** — pick the weakest criterion and one focused move; if the move tunes a scannable parameter, sweep several values within the iteration and keep the best; if out of ideas, optionally search the literature and ingest findings into the wiki
3. **Act** — make one surgical change
4. **Judge** — compare to the current best; `BETTER / WORSE / NO CHANGE`
5. **Keep or revert** — BETTER archives to `history/vNNN/`; otherwise restore the best
6. **Record** — write an attempt page to the wiki (what, why, outcome, reasoning), update the report and results table

The bookkeeping — snapshots, restores, the results table, the iteration counters, the caps check — is done by a small tested script that ships with the skill (`ar.py`), so it cannot drift; without Python, the agent does the same steps by hand.

### When it stops

The loop never stops on its own judgement: a plateau (five reverts in a row) makes it change approach, not quit. It always stops when:

- a **cap** is reached — the iteration or wall-clock limit for this run (or the cost limit, where usage can be measured)
- **you stop it** — press Esc, or tell it to stop, in any language
- **tool errors** keep happening — several in a row (3 by default)

It leaves the best version in place, puts the reason at the top of `report.md`, and waits for you. It never restarts on its own — `/autoresearch` resumes it with a fresh budget.

### Steering it while it runs

The agent asks you questions without ever stopping. Open questions sit at the top of `report.md`. Answer them in the session (`A3: eLife`) or via the `answers.md` inbox — the agent picks up the answer on the next iteration, acts on it, and removes the question. Because every state is a snapshot, it can re-branch from an earlier best if you steer it elsewhere.

### Driving it one iteration per turn (with the neuroflow mod)

With the [neuroflow mod](../concepts/mods.md) set to `runtime: on`, `/autoresearch drive {name}` hands a registered loop
to the mod: each turn runs exactly one iteration, and between turns the mod checks the loop's caps with `ar.py status`
before it starts the next one. The band above the prompt shows `↻ driving autoresearch "{name}" · turn N` with a stop
key (`s`); Esc interrupts the current turn and ends the drive; `/autoresearch stop` ends it too. Short turns keep the
context small and make every iteration a clean point to stop at. The dashboard's loop tab (`/dashboard loop`) shows the
quality curve and the open questions.

---

## Research integrity

A loop that edits analysis code, scores each version by its results, and keeps the winner would be automated p-hacking. So when a loop touches code that computes results from your study data, it first asks which job it has:

| Mode | What the loop may do | What it never does |
|---|---|---|
| **Confirmatory** | Improve the correctness, robustness, and reproducibility of a fixed analysis — running it only on simulated data, label-shuffled data, or an excluded pilot subset | Run on your real labelled data, score effect sizes or p-values, or touch anything the preregistration or analysis plan fixes |
| **Exploratory** | Search over analysis choices, on a fork of any confirmatory script, with outputs in `exploratory/` folders | Edit a confirmatory script, or hide a specification — every one it tries is logged with its result to `.neuroflow/data-analyze/multiverse.md` |

Exploratory reports carry an `EXPLORATORY — N specifications tried` header, and `/data-analyze` and `/paper` treat anything from the ledger as exploratory. If a preregistration exists, every loop — analysis or not — keeps the preregistered hypotheses, primary outcomes, and confirmatory/exploratory labels unchanged.

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
| Writes | the loop folder next to the artifact, tracked external files (on KEPT), `history/vNNN/`, the pointer registry, session log, the integrity decision in `.neuroflow/reasoning/`, and — exploratory loops only — `.neuroflow/data-analyze/multiverse.md` |

---

## Related

- [`neuroflow:autoresearch` skill](../skills/autoresearch/SKILL.md) — full protocol, wiki format, criteria, dashboard template
- [`neuroflow:wiki`](../skills/wiki/SKILL.md) — the page format the loop wiki uses; durable findings are promoted here
- [`/paper`](paper.md) — uses the worker-critic loop (bounded, 3 iterations) for section drafting
- [`/pipeline`](pipeline.md) — multi-step orchestration across phases
