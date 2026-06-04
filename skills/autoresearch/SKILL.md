---
name: autoresearch
description: Infinite improvement loop for any research artifact in any phase — a single managing agent makes one focused change per iteration, judges it against the previous best, keeps or reverts. Its memory is a per-loop wiki it reads before every move and writes after every move. The loop never stops until the human interrupts it. Inspired by Andrej Karpathy's autoresearch (MIT).
---

<!-- Inspired by Andrej Karpathy's autoresearch (MIT) — https://github.com/karpathy/autoresearch -->

# autoresearch

An infinite, multi-session improvement loop for any research artifact. **One managing agent** runs the whole loop — it makes a focused change, judges it against the current best, keeps the winner and reverts the rest. Its long-term memory is a **per-loop wiki** that it consults before every move and updates after every move. The loop never stops on its own.

---

## Core rule — NEVER STOP

**The loop runs until the human interrupts it. Period.**

- Never decide the artifact is "good enough" and exit
- Never stop because the score plateaued or iterations look repetitive
- Plateau is a signal to change direction (new angle, branch, or literature search) — not to stop
- Open questions to the human are **non-blocking** — park them, keep going on a best guess
- The only valid exit is the human pressing Ctrl-C or typing a stop command

---

## Architecture — one agent, one brain

Two principles define this loop. Hold both.

**1. One managing agent — no subagent fan-out.** A single agent runs the entire loop and holds the thread of all iterations. It plays worker (makes the change) and evaluator (judges it) itself. The only optional exception is the evaluation step, which can use one fresh subagent when `evaluation: fresh-eval` is set (see [Evaluation](#evaluation)). Everything else is one agent, because context continuity across iterations is what lets it reason about the whole search instead of one move at a time.

**2. The wiki is the brain.** A single agent running an infinite loop will exhaust its context window. The per-loop **wiki** is the externalized memory that survives that — context is working memory, the wiki is long-term memory. This is not optional decoration. **The agent reads the wiki before deciding every move and writes to it after every move.** Without the wiki the agent is amnesiac: it re-treads dead ends, forgets why something failed, and goes in circles forever instead of getting smarter. The wiki is what makes an infinite single-agent loop *compound* rather than *wander*.

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
    ├── v000/              ← baseline snapshot of tracked files
    ├── v001/              ← snapshot saved on each KEPT iteration
    └── ...

.neuroflow/{phase}/autoresearch-loops.md   ← POINTER REGISTRY ONLY (in project memory)
```

**Naming:** `{name}` defaults to a slug derived from the primary tracked file (`connectivity.py` → `connectivity`), always overridable at setup. Multiple loops can coexist — e.g. `intro_autoresearch/` and `methods_autoresearch/` both under `manuscript/`.

**Location:** defaults to the directory of the primary tracked file. Always overridable (the user can put it in `.neuroflow/`, a sibling folder, anywhere). Everything — wiki, history, reports — travels with the artifact.

**Pointer registry** (`.neuroflow/{phase}/autoresearch-loops.md`) keeps project memory aware of every loop without holding the loop itself:

```markdown
# Autoresearch loops — {phase}

| Name | Location | Iterations | Best | Status |
|------|----------|-----------|------|--------|
| connectivity | scripts/analysis/connectivity_autoresearch/ | 47 | v031 | running |
| intro | manuscript/intro_autoresearch/ | 12 | v009 | paused |
```

---

## The wiki — the agent's brain

The loop wiki follows the `neuroflow:wiki` page format (frontmatter, `index.md`, `log.md`, wikilinks) but is **scoped to this one loop** and lives inside the loop folder. It is the fourth wiki level — local and disposable, with durable findings promoted up to the project wiki at loop end.

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
- `ask` (default) — at loop end / interruption, surface durable findings and ask which to promote
- `on` — promote durable findings automatically
- `off` — keep everything local

A "durable finding" is a `synthesis/` page or a confirmed `concept` that generalizes beyond this artifact (e.g. "averaging EEG reference before ICA consistently improves component separability"). Promote via `neuroflow:wiki` ingest into `.neuroflow/wiki/`. Micro-experiment `attempts/` pages stay local — they would only clutter the project wiki.

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
promote_to_project_wiki: ask          # on | off | ask
branching: agent-decided              # off | agent-decided
max_alive_branches: 3                 # cost cap when branching
parameter_sweep: true                 # when a move tunes a scannable parameter, scan several values in ONE iteration and pick the best
literature_search: when-stuck         # off | when-stuck | agent-decided
literature_sources: pubmed, biorxiv   # MCP sources to query
literature_budget: 1 per 5 iterations # rate cap
evaluation: self                      # self | fresh-eval
output_dashboard: off                 # on | off
output_report_md: on                  # on | off
output_report_pdf: off                # on | off
report_cadence: every-round           # every-round | every-N
answer_channel: both                  # session | inbox | both
notify_on_plateau: true

## Iteration checklist — DO ALL, EVERY TIME, NEVER SKIP
<!-- This block is the contract. It is re-read at the start of every iteration so it
     can never drift out of context. Skipping ANY item is a loop failure. -->
1. RECALL — read this program.md (incl. this checklist), __thetask__.md, the wiki (index → synthesis → relevant attempts), and check answers.md + session for new answers
2. DECIDE — pick the weakest criterion and ONE move, informed by the wiki (never re-try a move the wiki shows failed)
3. SWEEP — if the move tunes a scannable parameter and parameter_sweep is on, scan several values this iteration and pick the best
4. ACT — make the change
5. JUDGE — compare to history/vBEST/ against the criteria → BETTER | WORSE | NO CHANGE + delta
6. KEEP/REVERT — snapshot to history/vNNN/ on BETTER, else restore from vBEST/; append a row to results.md
7. WIKI — write an attempts/ page (what, why, verdict, delta, reasoning — especially failures); update synthesis/ on a pattern; update index.md + log.md
8. REPORT — rewrite report.md (open questions on top); update the pointer registry; regenerate PDF/dashboard per cadence
9. Items 7 and 8 are NOT optional and are NOT once-at-baseline — they run every single iteration. If you ever notice you skipped one, do it now before the next move.
```

**The agent reads this config AND the iteration checklist at the start of every iteration and honors both exactly** — check `literature_budget` before searching, respect `branching` / `max_alive_branches` / `parameter_sweep`, use the configured `evaluation` mode, refresh outputs per `report_cadence`, and complete every checklist item including the wiki write and report refresh.

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
```

Paths are relative to the loop folder. The agent modifies the real files; the evaluator compares current state to `history/vBEST/`.

---

## INIT — setup interview (first run only)

> **HARD GATE — the loop must NOT begin until the user has explicitly signed off on the full config block.** Never set silent defaults and jump into iterations. Every configuration option below is *asked* one at a time, not assumed — branching, parameter sweep, literature search (+ sources + budget), evaluation mode, outputs (dashboard / report.md / PDF) + cadence, answer channel, and wiki promotion. If the user gives a partial answer, ask the rest; if they say "use defaults", still show the resulting config block and get an explicit "yes" before iterating. Starting iterations with any unasked option is the failure mode this gate exists to prevent.

1. Read `project_config.md` → determine active phase
2. **Which files should this loop improve?** (or infer from `--target`)
3. **Name and location:** derive a default name from the primary tracked file and a default location = that file's directory. Show both: *"Loop folder: `scripts/analysis/connectivity_autoresearch/`. OK, or change name/location?"*
4. **Build criteria** — Layer 1 (phase defaults from `references/phase-criteria.md`) + Layer 2 (context-inferred) + Layer 3 (user input) → `program.md`
5. **Loop configuration interview — go slowly, ONE question at a time.** Ask each option as a separate message (or a clearly numbered walk-through), state the default and the trade-off, wait for the answer, then move to the next. Do NOT batch all options into one wall of text and do NOT rush to the loop — a hurried interview is exactly the failure this step guards against. Record each answer into the config block:
   - *Branching:* "When you see two equally promising directions, may I try both and keep the winner? (agent-decided / single-track)" → if agent-decided, "max directions to keep open at once?"
   - *Parameter sweep (default yes):* "When a move tunes a parameter that makes sense to scan over a range — a threshold, filter cutoff, number of components, regularization strength — may I scan several values within a single iteration and pick the best, instead of one value per iteration? (yes / no)"
   - *Literature search:* "May I search papers when I run out of ideas or want grounding? (when-stuck / anytime / off)" → sources? → budget (e.g. 1 per 5 iterations)?
   - *Evaluation:* "Should I judge my own changes (faster, full context) or have a fresh independent check each time (slower, unbiased)? (self / fresh-eval)"
   - *Outputs:* "Live dashboard server? Human report.md (default on)? Also a PDF snapshot?" → cadence?
   - *Answers:* "Answer my questions in this session, via an answers.md inbox, or both?"
   - *Wiki promotion:* "At loop end, promote durable findings to the project wiki? (ask / auto / off)"
6. **Confirm the full config (the gate).** Render the complete `## Loop configuration` block back to the user with every value filled in, and ask for an explicit go-ahead: *"This is the full configuration. Confirm to start the loop, or tell me what to change."* **Do not proceed to step 7 until the user confirms.** No iteration runs before this sign-off.
7. Create the loop folder at the chosen location; initialize `wiki/` (index.md, log.md, schema.md, pages/ subfolders) — write a starter `schema.md` describing the artifact, the criteria, and the wikilink convention
8. Snapshot tracked files → `history/v000/`; write baseline row to `results.md`
9. Write `program.md` (with the confirmed config block **and the "## Iteration checklist" block — both are mandatory**), `__thetask__.md` (with the iteration reminder at top), `flow.md`
10. Add a row to `.neuroflow/{phase}/autoresearch-loops.md` (create the registry if absent)
11. If `output_dashboard: on`, write `server.py` from `scripts/server.py` in this skill and tell the user the URL
12. Write the first `report.md`
13. Start the loop

---

## Loop protocol — NEVER STOP

```
REPEAT FOREVER until the human interrupts:

  RECALL
    a. Read program.md — INCLUDING its "## Iteration checklist" — + __thetask__.md (resolve tracked paths).
       The checklist is the contract for this iteration; follow every item, never skip the wiki write or report refresh.
    b. Read tracked files (current state) + history/vBEST/ (current best)
    c. Read the wiki: index.md → synthesis/ → attempts/ for the target criterion → relevant concepts/sources
    d. Check answers.md and the session for new human answers (match Q-ids; see Q&A channel)

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

  JUDGE  (self, or one fresh subagent if evaluation: fresh-eval)
    i. Compare current tracked files to history/vBEST/ against the criteria.
       Return: VERDICT (BETTER | WORSE | NO CHANGE), Delta (−5..+5),
               per-criterion notes, numeric values if applicable,
               and the single weakest area to target next.
       If self-evaluating: judge it COLD — be skeptical of your own change.

  KEEP / REVERT
    j. If BETTER: snapshot tracked files → history/vNNN/; update __thetask__.md
                  (iterations, best snapshot); append KEPT row to results.md.
       If WORSE / NO CHANGE: restore tracked files from history/vBEST/; append REVERTED row.

  RECORD  (the brain — mandatory, EVERY round, no exceptions)
    k. Write an attempts/ page (what, why, verdict, delta, reasoning — especially for failures).
       Update synthesis/ if a pattern emerged. Update index.md + log.md.
    l. Refresh ALL THREE every round: the wiki (k above), results.md, AND report.md
       (open questions on top). report.md is not write-once-at-baseline — it is rewritten
       each iteration so the human's live view and open-questions list stay current.
       Update the pointer registry. Regenerate report.pdf / dashboard data per cadence.

  STEER
    m. Plateau (5 consecutive REVERTs): if notify_on_plateau, note it in report.md and the session,
       then CHANGE APPROACH — new angle from the wiki, a branch, or a literature search. DO NOT STOP.

  n. Go to RECALL. Never stop on your own.
```

---

## Evaluation

| Mode | Behaviour | Trade-off |
|------|-----------|-----------|
| `self` (default) | The managing agent judges its own change cold against `vBEST` + criteria | Keeps full context, faster; instruct it to be skeptical of its own work; the wiki catches "you rejected this before" |
| `fresh-eval` | One fresh general-purpose subagent judges the change with no loop context | Independent, unbiased; the only place a subagent is spawned; slower |

The bias risk of `self` is real — an agent grading its own work tends to like it. Mitigations: judge against the explicit `vBEST` snapshot and named criteria, and let the wiki hold it honest. Choose `fresh-eval` when evaluation rigor matters more than speed.

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

Running: KEPT adds delta; REVERTED leaves it unchanged. Append numeric columns (power, R², word_count…) after `Next focus` for phases with numeric criteria.

### report.md format — human steering surface

Open questions lead the file. Answered questions are **deleted** from the report (their resolution goes to the wiki, not an archive section here).

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
- Loop start: `## HH:MM — [autoresearch/{name}] started — tracking {N} file(s) at {location}`
- Every 10 iterations: `## HH:MM — [autoresearch/{name}] iter {N} — running {R} — best {snapshot}`
- Plateau: `## HH:MM — [autoresearch/{name}] PLATEAU — changing approach`
- Interrupt: `## HH:MM — [autoresearch/{name}] interrupted at iter {N} — best {snapshot}`

Keep the pointer registry (`.neuroflow/{phase}/autoresearch-loops.md`) current: iterations, best, status (running / paused / interrupted).

---

## Criteria initialization

Build `program.md` criteria in three layers on first run:

- **Layer 1 — Phase defaults.** Always included. Full per-phase criteria tables are in **`references/phase-criteria.md`** — read it during INIT and copy the active phase's criteria into `program.md`.
- **Layer 2 — Context-inferred.** Read existing `.neuroflow/` files and add relevant criteria:

  | If this exists | Add criterion |
  |---|---|
  | `.neuroflow/ideation/research-question.md` | Alignment with the stated research question |
  | `.neuroflow/preregistration/` | Adherence to preregistered hypotheses / analysis plan |
  | `project_config.md` has `target_journal:` | Meets [journal] editorial standards |
  | `.neuroflow/grant-proposal/` names a funder | Meets [funder] reviewer criteria |
  | `.neuroflow/data-analyze/analysis-plan.md` | Covers all hypotheses in the analysis plan |
  | `.neuroflow/objectives.md` | Addresses all project objectives |

- **Layer 3 — User input.** After printing layers 1+2, ask: *"Add your own criteria? (Enter to skip)"* → append under `## User criteria`.

---

## Resume

If `.neuroflow/{phase}/autoresearch-loops.md` lists one or more loops:
- One loop → confirm: *"Resume autoresearch '{name}' at {location}? {N} iterations logged, best {snapshot}."*
- Multiple → list them and ask which to resume
- On resume: read that loop's `program.md`, `__thetask__.md`, `results.md`, and **the wiki** (index + synthesis), then go straight to the loop (skip INIT)

---

## Slash command

`/autoresearch` or any phase command invoked with the keyword `autoresearch` in the prompt.

---

## Bundled resources

- **`references/phase-criteria.md`** — per-phase Layer 1 default criteria (read during INIT)
- **`scripts/server.py`** — optional dashboard template (write to the loop folder only if `output_dashboard: on`)
