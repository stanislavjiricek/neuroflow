---
name: autoresearch-protocol
description: Open-ended improvement loop for any research artifact in any phase — a single managing agent makes one focused change per iteration, judges it against the previous best, keeps or reverts. Its memory is a per-loop wiki it reads before every move and writes after every move. The loop never stops on its own judgement — only at the caps set at setup (iterations, wall-clock time, cost where measurable), when the human stops it, or after repeated tool errors. Inspired by Andrej Karpathy's autoresearch (MIT).
---

<!-- Inspired by Andrej Karpathy's autoresearch (MIT) — https://github.com/karpathy/autoresearch -->

# autoresearch-protocol

An open-ended, multi-session improvement loop for any research artifact. **One managing agent** runs the whole loop — it makes a focused change, judges it against the current best, keeps the winner and reverts the rest. Its long-term memory is a **per-loop wiki** that it consults before every move and updates after every move. The loop never stops on its own judgement, and it always stops at the caps the human set.

---

## Core rule — never stop on your own judgement, always stop at the caps

**The loop runs until a stop condition fires — never earlier, never later.**

- Never decide the artifact is "good enough" and exit
- Never stop because the score plateaued or iterations look repetitive
- Plateau is a signal to change direction (new angle, branch, or literature search) — not to stop
- Open questions to the human are **non-blocking** — park them, keep going on a best guess
- **Always stop** when a stop condition fires: a cap set at INIT is reached (`max_iterations`, `max_wall_clock`, `max_cost`), the human stops the loop, or `max_consecutive_errors` tool errors happen in a row — see [Stopping](#stopping). A loop without a cap is never started.

---

## Architecture — one agent, one brain

Two principles define this loop. Hold both.

**1. One managing agent — no subagent fan-out.** A single agent runs the entire loop and holds the thread of all iterations. It plays worker (makes the change) and evaluator (judges it) itself. The only optional exception is the evaluation step, which can use one fresh subagent when `evaluation: fresh-eval` is set (see [Evaluation](#evaluation)). Everything else is one agent, because context continuity across iterations is what lets it reason about the whole search instead of one move at a time.

**2. The wiki is the brain.** A single agent running a long loop will exhaust its context window. The per-loop **wiki** is the externalized memory that survives that — context is working memory, the wiki is long-term memory. This is not optional decoration. **The agent reads the wiki before deciding every move and writes to it after every move.** Without the wiki the agent is amnesiac: it re-treads dead ends, forgets why something failed, and goes in circles forever instead of getting smarter. The wiki is what makes a long single-agent loop *compound* rather than *wander*.

> Treat the wiki the way you treat your own memory: you would never re-run an experiment you already know failed. Neither should the loop. Query the wiki first, always.

---

## Folder structure

The loop folder is named `{name}_autoresearch/` and lives **next to the artifact being improved** — not inside `.neuroflow/` by default. Only a small pointer registry lives in project memory.

```
{location}/{name}_autoresearch/        ← e.g. scripts/analysis/connectivity_autoresearch/
├── wiki/                  ← THE BRAIN — read before every move, written after every move
│   ├── index.md           ← catalog of all pages
│   ├── log.md             ← append-only: ## [iter NNN] {op} | {title}
│   ├── schema.md          ← this loop's domain, criteria, conventions
│   └── pages/
│       ├── attempts/      ← one page per meaningful direction: what, why, verdict, delta, reasoning (wins AND dead-ends)
│       ├── concepts/      ← domain knowledge about the artifact and each criterion
│       ├── sources/       ← distilled findings from literature search
│       └── synthesis/     ← patterns: "what consistently works / fails here", the current thesis
├── program.md             ← task + criteria + config block (read every iteration)
├── __thetask__.md         ← pointer manifest — which external files are tracked
├── results.md             ← iteration table (numbers) → dashboard source
├── report.md              ← human-readable report — open questions on top, refreshed each round
├── report.pdf             ← optional read-only snapshot (pandoc)
├── answers.md             ← human answer inbox (detached mode)
├── server.py              ← optional dashboard (only written if output_dashboard: on)
├── flow.md
└── history/
    ├── v000/              ← baseline snapshot of tracked files (+ .ar-manifest.json: original path + sha256 per file)
    ├── v001/              ← snapshot saved on each KEPT iteration
    └── ...

.neuroflow/{phase}/autoresearch-loops.md   ← POINTER REGISTRY ONLY (in project memory)
.neuroflow/data-analyze/multiverse.md      ← exploratory analysis loops only — every specification tried, with its result
```

**Naming:** `{name}` defaults to a slug derived from the primary tracked file (`connectivity.py` → `connectivity`), always overridable at setup. Multiple loops can coexist — e.g. `intro_autoresearch/` and `methods_autoresearch/` both under `manuscript/`.

**Location:** defaults to the directory of the primary tracked file. Always overridable (the user can put it in `.neuroflow/`, a sibling folder, anywhere). Everything — wiki, history, reports — travels with the artifact.

**Pointer registry** (`.neuroflow/{phase}/autoresearch-loops.md`) keeps project memory aware of every loop without holding the loop itself:

```markdown
# Autoresearch loops — {phase}

| Name | Location | Iterations | Best | Status |
|------|----------|-----------|------|--------|
| connectivity | scripts/analysis/connectivity_autoresearch/ | 47 | v031 | running |
| intro | manuscript/intro_autoresearch/ | 12 | v009 | stopped: max_wall_clock |
```

---

## The wiki — the agent's brain

The loop wiki follows the `neuroflow:wiki-protocol` page format (frontmatter, `index.md`, `log.md`, wikilinks) but is **scoped to this one loop** and lives inside the loop folder. It is the fourth wiki level — local and disposable, with durable findings promoted up to the project wiki at loop end.

### Page format

Every page in `pages/` uses this frontmatter:

```yaml
---
title: Citation density in Discussion plateaus after 3 additions
type: attempt            # attempt | concept | source | synthesis
iter: 042                # iteration this page was created / last touched
criterion: claim-support # which program.md criterion it relates to (if any)
verdict: WORSE           # attempt pages only: BETTER | WORSE | NO CHANGE
delta: -1                # attempt pages only
status: current          # current | superseded
created: YYYY-MM-DD
updated: YYYY-MM-DD
related: []              # file paths; in-body refs use [[Page Title]]
---
```

**Wikilinks are mandatory** for all in-body cross-references: `[[Page Title]]`, never plain Markdown links. This is what makes the brain navigable.

### Page types

| Type | Folder | What it holds |
|------|--------|---------------|
| `attempt` | `pages/attempts/` | One page per meaningful direction tried. Records what changed, **why** it was tried, verdict, delta, and the reasoning for the outcome. **Failures are the most valuable pages** — they prune the search space. |
| `concept` | `pages/concepts/` | Knowledge about the artifact and each criterion — what "good" looks like here, constraints, domain facts learned along the way. |
| `source` | `pages/sources/` | One page per paper found via literature search — distilled claims and how they apply to this artifact. Keeps the bulk out of context. |
| `synthesis` | `pages/synthesis/` | Patterns across attempts: "every citation-density change plateaus", "the weakest criterion is consistently X", the loop's evolving thesis on how to improve this artifact. |

### How the agent works the wiki (every iteration)

**RECALL (before deciding a move) — mandatory:**
1. Read `wiki/index.md` — the full map
2. Read the `synthesis/` pages — the current thesis on what works and fails here
3. Read `attempts/` pages relevant to the criterion being targeted — "have I tried anything near this? did it fail? why?"
4. Read relevant `concepts/` and `sources/` pages if the move touches them

**RECORD (after the move is judged) — mandatory:**
1. Write a new `attempts/` page: what changed, why, verdict, delta, and the reasoning (especially for failures)
2. If a pattern emerged (e.g. third plateau on the same axis), create or update a `synthesis/` page
3. If a human answer resolved an assumption, capture the decision in a `concepts/` or `synthesis/` page
4. Update `index.md` (add/update the row) and append to `log.md` (`## [iter NNN] {op} | {title}`)

**This read-then-write discipline is the loop's intelligence.** Skipping RECALL makes the agent re-propose failed moves. Skipping RECORD makes the next iteration blind. Neither is ever skipped.

### Promotion to the project wiki

Per `promote_to_project_wiki` in the config:
- `ask` (default) — when the loop stops or is interrupted, surface durable findings and ask which to promote
- `on` — promote durable findings automatically
- `off` — keep everything local

A "durable finding" is a `synthesis/` page or a confirmed `concept` that generalizes beyond this artifact (e.g. "averaging EEG reference before ICA consistently improves component separability"). Promote via the `neuroflow:wiki-protocol` ingest workflow into `.neuroflow/wiki/`. Micro-experiment `attempts/` pages stay local — they would only clutter the project wiki.

---

## program.md — task, criteria, and config

Read at the top of **every** iteration. Holds the task, the criteria (three layers — see [Criteria](#criteria-initialization)), and the machine-followable config block.

```markdown
# Autoresearch Program — {name} ({phase})
Started: YYYY-MM-DD

## Task
{one sentence: what is being improved and why}

## Tracked files
{listed from __thetask__.md for reference}

## Default criteria (phase: {phase})
{phase-specific criteria — see references/phase-criteria.md}

## User criteria
<!-- user additions, e.g. "Target Nature Neuroscience", "keep under 500 words" -->

## Improvement direction
{what "better" looks like — the guiding instruction each iteration}

## Out of scope
{what must NOT change between iterations}

## Loop configuration
loop_name: connectivity
artifact_location: scripts/analysis/connectivity_autoresearch/
integrity_mode: confirmatory          # confirmatory | exploratory | n/a — set by the INIT integrity gate (references/integrity.md)
max_iterations: 40                    # CAP — iterations per run (a run = one start or resume); asked at INIT, no default
max_wall_clock: 8h                    # CAP — time per run (90m, 8h, 1d); asked at INIT, no default
max_cost: n/a                         # CAP — usage or spend per run (e.g. 20 USD) — only where this session can measure it, else n/a
max_consecutive_errors: 3             # stop after this many tool errors in a row
promote_to_project_wiki: ask          # on | off | ask
branching: agent-decided              # off | agent-decided
max_alive_branches: 3                 # cost cap when branching
parameter_sweep: false                # when a move tunes a scannable parameter, scan several values in ONE iteration and pick the best (default on; off when confirmatory)
literature_search: when-stuck         # off | when-stuck | agent-decided
literature_sources: pubmed, biorxiv   # MCP sources to query
literature_budget: 1 per 5 iterations # rate cap
evaluation: fresh-eval                # self | fresh-eval (default self; fresh-eval when confirmatory)
output_dashboard: off                 # on | off
output_report_md: on                  # on | off
output_report_pdf: off                # on | off
report_cadence: every-round           # every-round | every-N
answer_channel: both                  # session | inbox | both
notify_on_plateau: true

## Iteration checklist — DO ALL, EVERY TIME, NEVER SKIP
<!-- This block is the contract. It is re-read at the start of every iteration so it
     can never drift out of context. Skipping ANY item is a loop failure. -->
1. RECALL — first run `ar.py status` (the autoresearch-protocol skill's scripts/ar.py; exit 1 → a cap is reached or the loop state needs attention: Stopping in the skill); read this program.md (incl. this checklist), __thetask__.md, the wiki (index → synthesis → relevant attempts), and check answers.md + session for new answers and for a stop request
2. DECIDE — pick the weakest criterion and ONE move, informed by the wiki (never re-try a move the wiki shows failed)
3. SWEEP — if the move tunes a scannable parameter and parameter_sweep is on, scan several values this iteration and pick the best
4. ACT — make the change
5. JUDGE — compare to history/vBEST/ against the criteria → BETTER | WORSE | NO CHANGE + delta
6. KEEP/REVERT — `ar.py keep` on BETTER (snapshot to history/vNNN/), else `ar.py revert` (restore from vBEST/); both append the results.md row and update the __thetask__.md counters
7. WIKI — write an attempts/ page (what, why, verdict, delta, reasoning — especially failures); update synthesis/ on a pattern; update index.md + log.md
8. REPORT — rewrite report.md (open questions on top); update the pointer registry; regenerate PDF/dashboard per cadence
9. Items 7 and 8 are NOT optional and are NOT once-at-baseline — they run every single iteration. If you ever notice you skipped one, do it now before the next move.
10. INTEGRITY — whenever integrity_mode is not n/a, this binds steps 3–6 (rules: references/integrity.md in the neuroflow:autoresearch-protocol skill):
    confirmatory → run tracked code only on blind inputs; never touch an item frozen in Out of scope; judge outcome-blind criteria only — a larger effect, smaller p-value, or more significant tests is never BETTER
    exploratory → every specification run on the study data — each sweep value included — goes into .neuroflow/data-analyze/multiverse.md with its result before JUDGE; ledger rows are never edited or deleted
11. STOP — at a cap, on a human stop, or after max_consecutive_errors tool errors in a row: stop (Stopping in the skill). Never stop for any other reason — a plateau means change approach.
```

**The agent reads this config AND the iteration checklist at the start of every iteration and honors both exactly** — stop at the caps, check `literature_budget` before searching, respect `branching` / `max_alive_branches` / `parameter_sweep`, apply the `integrity_mode` rules, use the configured `evaluation` mode, refresh outputs per `report_cadence`, and complete every checklist item including the wiki write and report refresh.

---

## __thetask__.md — tracked-file manifest

```markdown
# Task Manifest

> EVERY ITERATION: follow the "## Iteration checklist" in program.md in full —
> including the wiki write (step 7) and report.md refresh (step 8). Never skip them.

## Tracked files
- `../connectivity.py`
- `../helpers/graph_metrics.py`

## Task description
Improve the connectivity analysis until it is reproducible and statistically sound.

## Current best snapshot
history/v031/

## Iterations run
47 (last: YYYY-MM-DD)

## Current run
started: 2026-10-07T21:04:00+02:00
iterations at start: 40
```

Paths are relative to the loop folder. The agent modifies the real files; the evaluator compares current state to `history/vBEST/`. `ar.py` keeps the last three sections (`ar.py begin` writes `## Current run` — the caps count from it).

---

## INIT — setup interview (first run only)

> **HARD GATE — the loop must NOT begin until the user has explicitly signed off on the full config block.** Never set silent defaults and jump into iterations. Every configuration option below is *asked* one at a time, not assumed — the integrity mode (analysis-touching loops, step 3), the caps (no defaults), branching, parameter sweep, literature search (+ sources + budget), evaluation mode, outputs (dashboard / report.md / PDF) + cadence, answer channel, and wiki promotion. If the user gives a partial answer, ask the rest; if they say "use defaults", still show the resulting config block and get an explicit "yes" before iterating. Starting iterations with any unasked option is the failure mode this gate exists to prevent.

1. Read `project_config.md` → determine active phase (`active_phase` in its frontmatter)
2. **Which files should this loop improve?** (or infer from `--target`)
3. **Integrity gate.** Read `references/integrity.md` and decide whether the loop is *analysis-touching* — phase `data-analyze` / `data-preprocess`, a tracked file that computes results from study data, or a tracked file implementing a preregistered analysis. If it is, ask the integrity question as its own step: **confirmatory** (a fixed analysis improved on blind inputs, scored only on outcome-blind criteria) or **exploratory** (confirmatory scripts forked, everything labelled exploratory, every specification logged with its result to `.neuroflow/data-analyze/multiverse.md`). There is no default — "use defaults" does not answer it. Record `integrity_mode`, log the choice to `.neuroflow/reasoning/{phase}.jsonl`, and apply the mode's rules in every later step: forked tracked files, frozen items in `## Out of scope`, outcome-blind criteria, sweep and evaluation defaults. Not analysis-touching → `integrity_mode: n/a`, no question.
4. **Name and location:** derive a default name from the primary tracked file and a default location = that file's directory. Show both: *"Loop folder: `scripts/analysis/connectivity_autoresearch/`. OK, or change name/location?"*
5. **Build criteria** — Layer 1 (phase defaults from `references/phase-criteria.md`) + Layer 2 (context-inferred) + Layer 3 (user input) → `program.md`
6. **Loop configuration interview — go slowly, ONE question at a time.** Ask each option as a separate message (or a clearly numbered walk-through), state the default and the trade-off, wait for the answer, then move to the next. Do NOT batch all options into one wall of text and do NOT rush to the loop — a hurried interview is exactly the failure this step guards against. Record each answer into the config block:
   - *Caps (no defaults — "use defaults" does not answer them; suggest a starting point such as 30 iterations / 4h):* "How long may each run of this loop go? A maximum number of iterations, and a maximum wall-clock time — one of them may be 'none', not both." → `max_iterations`, `max_wall_clock`. Then: "A cost or usage limit too?" — record it as `max_cost` only if this session can measure its usage or cost, otherwise record `n/a` and say that the iteration and time caps bound the run. Stop after `max_consecutive_errors` tool errors in a row (default 3). Caps count per run: each start or resume gets the full budget.
   - *Branching:* "When you see two equally promising directions, may I try both and keep the winner? (agent-decided / single-track)" → if agent-decided, "max directions to keep open at once?"
   - *Parameter sweep (default yes; no when `integrity_mode: confirmatory`):* "When a move tunes a parameter that makes sense to scan over a range — a threshold, filter cutoff, number of components, regularization strength — may I scan several values within a single iteration and pick the best, instead of one value per iteration? (yes / no)"
   - *Literature search:* "May I search papers when I run out of ideas or want grounding? (when-stuck / anytime / off)" → sources? → budget (e.g. 1 per 5 iterations)?
   - *Evaluation (default self; fresh-eval when `integrity_mode: confirmatory`):* "Should I judge my own changes (faster, full context) or have a fresh independent check each time (slower, unbiased)? (self / fresh-eval)"
   - *Outputs:* "Live dashboard server? Human report.md (default on)? Also a PDF snapshot?" → cadence?
   - *Answers:* "Answer my questions in this session, via an answers.md inbox, or both?"
   - *Wiki promotion:* "At loop end, promote durable findings to the project wiki? (ask / auto / off)"
7. **Confirm the full config (the gate).** Render the complete `## Loop configuration` block back to the user with every value filled in — and, when `integrity_mode` is not `n/a`, the frozen `## Out of scope` items and any planned fork — and ask for an explicit go-ahead: *"This is the full configuration. Confirm to start the loop, or tell me what to change."* **Do not proceed to step 8 until the user confirms.** No iteration runs before this sign-off.
8. Create the loop folder at the chosen location — and, for an exploratory fork, the `_exploratory` copies of the confirmatory files (`references/integrity.md`); initialize `wiki/` (index.md, log.md, schema.md, pages/ subfolders) — write a starter `schema.md` describing the artifact, the criteria, and the wikilink convention
9. Write `program.md` (with the confirmed config block **and the "## Iteration checklist" block — both are mandatory**), `__thetask__.md` (with the iteration reminder at top), `flow.md`
10. Baseline: `python <skill base dir>/scripts/ar.py init {loop folder}` — snapshots the tracked files to `history/v000/`, writes `results.md` with the baseline row, and sets the counters in `__thetask__.md` (see [Bookkeeping with ar.py](#bookkeeping-with-arpy))
11. Add a row to `.neuroflow/{phase}/autoresearch-loops.md` (create the registry if absent). If `integrity_mode: exploratory`, create `.neuroflow/data-analyze/multiverse.md` if absent (format in `references/integrity.md`) and list it in `.neuroflow/data-analyze/flow.md`
12. If `output_dashboard: on`, write `server.py` from `scripts/server.py` in this skill and tell the user the URL
13. Write the first `report.md`
14. `python <skill base dir>/scripts/ar.py begin {loop folder}` — the caps count from here — then start the loop

---

## Loop protocol

```
REPEAT until a stop condition fires (see Stopping):

  RECALL
    a. Run ar.py status. Exit 1 → handle its findings before anything else (a cap → Stopping).
       It also prints this iteration's number (next) and the REVERTs in a row.
       Read program.md — INCLUDING its "## Iteration checklist" — + __thetask__.md (resolve tracked paths).
       The checklist is the contract for this iteration; follow every item, never skip the wiki write or report refresh.
    b. Read tracked files (current state) + history/vBEST/ (current best)
    c. Read the wiki: index.md → synthesis/ → attempts/ for the target criterion → relevant concepts/sources
    d. Check answers.md and the session for new human answers (match Q-ids; see Q&A channel),
       and for a stop request in any language ("stop", "pause", "that's enough") → Stopping.

  DECIDE
    e. Pick the single weakest criterion and ONE focused move to improve it,
       informed by the wiki — do NOT re-propose a move the wiki shows already failed.
    f. If out of fresh ideas OR the wiki shows the obvious moves are exhausted:
         - If literature_search allows and budget permits → search papers (MCP tools),
           distill into wiki/sources/, synthesize a new direction, record it.
    g. If branching is enabled and two directions look equally promising:
         - Try one this iteration; note the fork so the other is tried next from the SAME vBEST.
           Keep at most max_alive_branches forks open; prune losers once a winner emerges.

  ACT
    h. Make ONE surgical change to the tracked files. Not a rewrite — one move.
       PARAMETER SWEEP: if parameter_sweep is on AND the move is tuning a parameter with a
       sensible range of values (threshold, filter cutoff, n_components, regularization,
       k folds, window length, learning rate, …), scan several values WITHIN THIS ONE
       iteration: try each, measure each against the criteria, and pick the best value to
       apply. The scan is internal scratch — only the chosen value is written to the tracked
       files. Record the swept values and the choice in one wiki attempts/ page (the curve).
       A sweep is one axis × many values; branching (g) is many competing directions — don't conflate them.
       INTEGRITY (integrity_mode ≠ n/a — references/integrity.md):
         confirmatory → run tracked code only on blind inputs (simulated data, shuffled labels,
                        or an excluded pilot subset); never touch an item frozen in Out of scope.
         exploratory  → append every specification run on the study data — each sweep value
                        included — to the multiverse ledger with its result, before JUDGE.

  JUDGE  (self, or one fresh subagent if evaluation: fresh-eval)
    i. Compare current tracked files to history/vBEST/ against the criteria.
       Return: VERDICT (BETTER | WORSE | NO CHANGE), Delta (−5..+5),
               per-criterion notes, numeric values if applicable,
               and the single weakest area to target next.
       If self-evaluating: judge it COLD — be skeptical of your own change.
       If integrity_mode is confirmatory: outcome-blind criteria only — a larger effect,
       a smaller p-value, or more significant tests is never BETTER.

  KEEP / REVERT  (one ar.py call — see Bookkeeping with ar.py)
    j. If BETTER: ar.py keep --iter N --delta D --focus "…" → snapshot tracked files → history/vNNN/,
                  KEPT row in results.md (Running = previous + delta), __thetask__.md iterations + best.
       If WORSE / NO CHANGE: ar.py revert --iter N --verdict WORSE|"NO CHANGE" --delta D --focus "…"
                  → restore tracked files from history/vBEST/, REVERTED row, iterations counter.

  RECORD  (the brain — mandatory, EVERY round, no exceptions)
    k. Write an attempts/ page (what, why, verdict, delta, reasoning — especially for failures).
       Update synthesis/ if a pattern emerged. Update index.md + log.md.
    l. Refresh ALL THREE every round: the wiki (k above), results.md, AND report.md
       (open questions on top). report.md is not write-once-at-baseline — it is rewritten
       each iteration so the human's live view and open-questions list stay current.
       Update the pointer registry. Regenerate report.pdf / dashboard data per cadence.

  STEER
    m. Plateau (5 consecutive REVERTs — ar.py status reports it): if notify_on_plateau, note it in report.md
       and the session, then CHANGE APPROACH — new angle from the wiki, a branch, or a literature search. DO NOT STOP.

  n. Go to RECALL. Never stop on your own judgement — stop only when a stop condition fires.
```

---

## Stopping

The loop never ends on its own judgement — and it always ends on one of these:

| Stop condition | How it is detected |
|---|---|
| `max_iterations` reached | `ar.py status` at RECALL — iterations this run ≥ the cap |
| `max_wall_clock` reached | `ar.py status` at RECALL — time since `ar.py begin` ≥ the cap (checked between iterations, so a long iteration can overrun it by its own length) |
| `max_cost` reached | only where this session can measure its usage or cost; `n/a` otherwise |
| The human stops it | Esc / Ctrl-C, or a stop message in any language ("stop", "pause", "that's enough") |
| `max_consecutive_errors` tool errors in a row | your own count of failed tool calls — a command that cannot start, a refused write, a failing search tool or API, a rate limit. Retry a failed call once before counting it; a finished iteration resets the count. A change that breaks the tracked code is **not** an error — it is a WORSE verdict, and the loop goes on |

**At a cap or the error limit:** leave the loop clean — the last judged move's KEEP/REVERT and RECORD done, an unjudged change put back with `ar.py restore` — so the tracked files equal the best snapshot and the wiki is current. Then put `STOPPED — {reason} — iteration {N} — best {snapshot}` at the top of `report.md`, right under the title, set the registry status to `stopped: {reason}`, log the stop line (Session logging), offer wiki promotion per `promote_to_project_wiki`, and end the turn with a short summary: why it stopped, iterations this run, best snapshot, open questions, and that `/autoresearch` resumes it with a fresh budget.

**On a human stop:** start nothing new. If the current move is already judged, finish its KEEP/REVERT and RECORD; if not, put the tracked files back (`ar.py restore`) and note the discarded move in `wiki/log.md`. Set the registry status to `interrupted` and log the interrupt line. After Esc / Ctrl-C nothing more can happen in that turn — on the next message, run `ar.py status` first and tidy up the same way, asking before you restore a cut-off change.

**Never restart on your own.** After any stop, the loop runs again only when the human asks for it (`/autoresearch` → Resume).

### Driven by the neuroflow mod — one iteration per turn

When the neuroflow mod is live and the human starts a loop with `/autoresearch drive {name}`, the mod drives it: the
mod has already run `ar.py begin`, so the caps count from now. **Your job each turn is exactly one iteration** — one
full pass of the iteration checklist (resume path first in the first turn: program.md, __thetask__.md, results.md, the
wiki) — **then end your turn.** Do not start the next iteration yourself: the mod checks `ar.py status` after every
answered turn and starts the next one only on exit 0, and stops at a cap, after `max_consecutive_errors` errored turns,
on Esc, or when the human presses stop. The stop rules above still apply inside your turn. Without the mod, `drive` is
not available: run the loop in the normal way (`/autoresearch` → Resume). `/autoresearch stop` ends a drive.

---

## Bookkeeping with ar.py

Snapshots, restores, the `results.md` rows and the `__thetask__.md` counters are done by a tested script, not by hand: one call per step, every file replaced atomically, and repeating a call with the same `--iter` is safe. Run it as `python <skill base dir>/scripts/ar.py <command> {loop folder}` — the skill base dir is the folder holding this SKILL.md.

| Command | When | What it does |
|---|---|---|
| `init` | INIT step 10 | snapshots the tracked files to `history/v000/` (with `.ar-manifest.json`), writes `results.md` with the baseline row, sets the counters |
| `begin` | INIT step 14, every resume | records the run start under `## Current run` in `__thetask__.md` — the caps count from here |
| `status` | RECALL, every iteration | iterations, next iteration number, best snapshot, running total, REVERTs in a row (plateau at 5), the caps, tracked files vs best |
| `keep --iter N --delta D --focus "…"` | BETTER | snapshot → `history/vNNN/`, KEPT row, best + iterations in `__thetask__.md` |
| `revert --iter N --verdict WORSE\|"NO CHANGE" --delta D --focus "…"` | WORSE / NO CHANGE | restores the tracked files from the best snapshot, REVERTED row, iterations counter |
| `restore` | a cut-off move the human wants discarded | puts the tracked files back to the best snapshot; no row |
| `adopt --iter N --focus "…"` | outside edits the human wants kept | snapshots the current files as the new best; row `KEPT (outside edit)` |

`--value V` (repeatable) fills extra numeric columns; `--json` gives machine-readable output.

**Exit codes.** `0` — done; go on. `1` — findings (`status`, `begin`), each with a kind: `cap` → stop ([Stopping](#stopping)); `no-cap` / `cap-unreadable` → ask the human for caps; `no-run` → run `ar.py begin`; `dirty` → the tracked files differ from the best snapshot at RECALL, so a move was cut off or someone edited them — ask the human, then `restore` or `adopt`, never decide alone; `missing` / `not-in-best` / `best-missing` → halt and ask the human to fix `__thetask__.md`, the file or the snapshot; `not-initialized` → run `ar.py init`. `2` — the call was refused or failed and nothing was half-written: read the message, fix the cause, run the same call again.

**No Python?** Do each step by hand as the table says — copy the files, append the row (Running: KEPT adds delta, REVERTED leaves it unchanged), update the counters — and track the caps yourself: note the run start time and count this run's iterations.

---

## Evaluation

| Mode | Behaviour | Trade-off |
|------|-----------|-----------|
| `self` (default) | The managing agent judges its own change cold against `vBEST` + criteria | Keeps full context, faster; instruct it to be skeptical of its own work; the wiki catches "you rejected this before" |
| `fresh-eval` | One fresh general-purpose subagent judges the change with no loop context | Independent, unbiased; the only place a subagent is spawned; slower |

The bias risk of `self` is real — an agent grading its own work tends to like it. Mitigations: judge against the explicit `vBEST` snapshot and named criteria, and let the wiki hold it honest. Choose `fresh-eval` when evaluation rigor matters more than speed.

With `integrity_mode: confirmatory`, `fresh-eval` is the default and the evaluator sees only the diff and the blind-input check outputs. No evaluation mode can make an agent unsee results it has already seen — that is what the confirmatory blind-input rule is for (`references/integrity.md`).

---

## Outputs

Each surface has one job. All optional except `report.md`.

| File | Audience | Job |
|------|----------|-----|
| `results.md` | dashboard | numeric iteration table (verdict, delta, running) |
| `report.md` | human | narrative + **open questions** — the steering surface |
| `report.pdf` | human | optional read-only snapshot (`pandoc report.md -o report.pdf`) |
| `server.py` | human | optional live dashboard at `localhost:8765` — renders **both** the report (open questions pinned at top + narrative) **and** the numeric trend charts on one page; template in `scripts/server.py` |
| `wiki/` | agent | the brain |

The dashboard is the one-stop web view: it reads `report.md` and `results.md` on every request, so a glance shows the quality curve *and* the open questions awaiting an answer. Use `?watch=1` for auto-refresh.

### results.md format

```markdown
# Autoresearch Results — {name}
Started: YYYY-MM-DD HH:MM

| # | Verdict | Δ | Running | Decision | Next focus |
|---|---------|---|---------|----------|------------|
| 000 | — | 0 | 0 | KEPT (baseline) | — |
| 001 | BETTER | +3 | 3 | KEPT | Intro–methods transition |
| 002 | WORSE | -1 | 3 | REVERTED | Overcomplicated methods |
```

Running: KEPT adds delta; REVERTED leaves it unchanged. Append numeric columns (power, R², word_count…) after `Next focus` for phases with numeric criteria. `ar.py` writes every row: `init --column NAME` adds a numeric column, `keep` / `revert --value V` fills it.

### report.md format — human steering surface

Open questions lead the file. Answered questions are **deleted** from the report (their resolution goes to the wiki, not an archive section here). In an exploratory loop (`integrity_mode: exploratory`), the line under the title — in `report.md` and `results.md` alike — reads `EXPLORATORY — {N} specifications tried — ledger: .neuroflow/data-analyze/multiverse.md`.

```markdown
# Autoresearch Report — {name}
Iteration 47 · Best: v031 · Running quality: +18 · Updated HH:MM

## Open questions for you
- **Q7** — about to delete the third control analysis (~200 lines, hard to reconstruct). Confirm? (iter 46)
- **Q3** — Target Nature Neuro or eLife? Affects how aggressively I trim. (iter 40)

## This round
Tried tightening the methods reproducibility statement. Verdict BETTER (+2), kept as v031.

## Current direction
Citation density in the Discussion is the weakest criterion — working that next.
```

---

## Q&A channel

The loop asks the human questions without ever stopping.

- **All open questions sit in the top section of `report.md`.** Short, live list.
- **Persistent, stable ids.** A question keeps its id forever (Q3 stays Q3, never renumbered) so "answer 3) ..." always maps to the right one.
- **Non-blocking.** The agent asks, makes its best-guess move, keeps going. It revisits when the answer arrives — and because every state is a `history/` snapshot, it can re-branch from an earlier `vBEST` if the human steers it elsewhere.
- **Answering:** depending on `answer_channel` —
  - `session`: human types `A3: eLife` or `answer 3) eLife` → agent reads it at the next RECALL
  - `inbox`: human writes the same into `answers.md` → agent reads it each RECALL
  - `both`: either works
- **On resolution:** the agent acts on the answer, **deletes** the question from `report.md`, and records the decision + what it did in the wiki (a `concepts/` or `synthesis/` page). Knowledge survives; the report stays clean.

A costly/irreversible move (large deletion, expensive recompute) should be raised as a question *before* doing it, placed at the top of the open-questions list. The loop still doesn't block — it proceeds on its best guess and the snapshot makes it reversible — but the human sees it first.

---

## Session logging & registry

Append to `.neuroflow/sessions/YYYY-MM-DD.md`:
- Loop start or resume: `## HH:MM — [autoresearch] {name} started — tracking {N} file(s) at {location} — integrity: {integrity_mode} — caps: {max_iterations} iterations / {max_wall_clock}`
- Every 10 iterations: `## HH:MM — [autoresearch] {name} iter {N} — running {R} — best {snapshot}`
- Plateau: `## HH:MM — [autoresearch] {name} PLATEAU — changing approach`
- Stop at a cap or the error limit: `## HH:MM — [autoresearch] {name} stopped ({reason}) at iter {N} — best {snapshot}`
- Interrupt: `## HH:MM — [autoresearch] {name} interrupted at iter {N} — best {snapshot}`

Keep the pointer registry (`.neuroflow/{phase}/autoresearch-loops.md`) current: iterations, best, status (running / paused / stopped: {reason} / interrupted).

---

## Criteria initialization

Build `program.md` criteria in three layers on first run:

- **Layer 1 — Phase defaults.** Always included. Full per-phase criteria tables are in **`references/phase-criteria.md`** — read it during INIT and copy the active phase's criteria into `program.md`. The `data-analyze` and `data-preprocess` defaults are outcome-blind by design; a confirmatory loop keeps every layer that way (`references/integrity.md`).
- **Layer 2 — Context-inferred.** Read existing `.neuroflow/` files and add relevant criteria:

  | If this exists | Add criterion |
  |---|---|
  | `.neuroflow/ideation/research-question.md` | Alignment with the stated research question |
  | `.neuroflow/preregistration/` | Not a criterion — a constraint: write the preregistration line from `references/integrity.md` into `## Out of scope` |
  | `project_config.md` has `target_journal:` | Meets [journal] editorial standards |
  | `.neuroflow/grant-proposal/` names a funder | Meets [funder] reviewer criteria |
  | `.neuroflow/data-analyze/analysis-plan.md` | Covers all hypotheses in the analysis plan |
  | `.neuroflow/objectives.md` | Addresses all project objectives |

- **Layer 3 — User input.** After printing layers 1+2, ask: *"Add your own criteria? (Enter to skip)"* → append under `## User criteria`.

---

## Resume

If `.neuroflow/{phase}/autoresearch-loops.md` lists one or more loops:
- One loop → confirm: *"Resume autoresearch '{name}' at {location}? {N} iterations logged, best {snapshot}. Caps for this run: {max_iterations} iterations / {max_wall_clock} — keep them?"*
- Multiple → list them and ask which to resume
- On resume: read that loop's `program.md`, `__thetask__.md`, `results.md`, and **the wiki** (index + synthesis), run `ar.py begin` (a new run — the caps count from here), then `ar.py status`. If the tracked files differ from the best snapshot (`dirty`), an earlier run was cut off or someone edited them — ask whether to `restore` or `adopt` before anything else. Then go straight to the loop (skip INIT)
- Exception: if the loop's config has no `integrity_mode` (it predates the integrity gate) and the loop is analysis-touching, run INIT step 3 first and write the answer — plus the mode's frozen items, fork, and checklist item 10 — into `program.md` before the next iteration
- Exception: if the loop's config has no caps (it predates them), ask the caps question (INIT step 6) and write the caps — plus checklist item 11 and the `ar.py` calls in items 1 and 6 — into `program.md` before the next iteration. Snapshots made before `ar.py` work as they are (files are found by name)

---

## Slash command

`/autoresearch` or any phase command invoked with the keyword `autoresearch` in the prompt.

---

## Bundled resources

- **`references/phase-criteria.md`** — per-phase Layer 1 default criteria (read during INIT)
- **`references/integrity.md`** — the integrity gate: when it applies, confirmatory vs exploratory rules, the multiverse ledger format (read during INIT step 3)
- **`scripts/ar.py`** — the loop's bookkeeping: snapshots, restores, results rows, counters, caps and plateau status (see [Bookkeeping with ar.py](#bookkeeping-with-arpy)); run it from the skill, never copy it into the loop folder
- **`scripts/server.py`** — optional dashboard template (write to the loop folder only if `output_dashboard: on`)
