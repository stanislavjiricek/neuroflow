# Integrity gate — confirmatory or exploratory

Read during INIT step 3, and when resuming an analysis-touching loop whose config has no `integrity_mode`.

A loop that edits analysis code, scores each version by its results, and keeps the winner is an automated walk through the garden of forking paths: run it long enough and it finds a specification that "works" on noise. The gate makes the loop pick one honest job before its first iteration.

---

## When the gate applies

A loop is **analysis-touching** if any of these holds:

1. Its phase is `data-analyze` or `data-preprocess`
2. A tracked file loads, preprocesses, or analyses the study's data — typically under `scripts/analysis/` or `scripts/preprocessing/`, or the `output_path` in `.neuroflow/data-analyze/flow.md` / `.neuroflow/data-preprocess/flow.md`
3. A preregistration exists (`.neuroflow/preregistration/prereg-*.md` or `registered-report.md`) and a tracked file implements a preregistered analysis

When the files don't make it clear, ask: *"Does any tracked file compute results from your study data?"*

Not analysis-touching (manuscript text, grant aims, slides, model code that never touches study data) → `integrity_mode: n/a`. No question; only the last section, *Preregistered projects*, applies.

---

## The question

Its own step, one question, no default — "use defaults" does not answer it:

> *"This loop edits code that computes results from your study data. Which job is it?*
> *(a) **Confirmatory** — improve the correctness, robustness, and reproducibility of a fixed analysis. I run it only on blinded inputs and never score results, so the loop cannot drift toward a better p-value.*
> *(b) **Exploratory** — search over analysis choices. Everything is labelled exploratory, every specification I try is logged with its result, and confirmatory scripts are forked, never edited."*

Record the answer as `integrity_mode: confirmatory | exploratory` in the config block, and log it as a decision in `.neuroflow/reasoning/{phase}.json`.

**Outcome-blind**, as used below: a value that would not change if the labels linking the data to the hypothesis — conditions, groups, or the outcome variable — were shuffled. Rejection rates, SNR pooled across conditions, runtime, tests passing, and ground-truth recovery on simulated data are outcome-blind. Effect sizes, p-values, decoding accuracy, and condition contrasts are not.

---

## confirmatory

The analysis is fixed; the loop improves how it is implemented.

- **Blind inputs only.** Run tracked code only on (a) simulated data with known ground truth, (b) the study data with its labels shuffled — in a copy or at load time; the pipeline runs end to end, true effects are destroyed — or (c) a pilot subset that the preregistration or analysis plan excludes from confirmatory testing. Never on the real labelled data. Never read results the confirmatory analysis already produced (`results/`, `figures/`, logs, caches).
- **Outcome-blind criteria only.** Score correctness, robustness, reproducibility, fidelity to the plan, and code quality. Drop any criterion that scores a result on the study data. A larger effect, a smaller p-value, or more significant tests is never BETTER.
- **Frozen plan.** Everything the preregistration or `.neuroflow/data-analyze/analysis-plan.md` fixes — hypotheses, tests, thresholds, exclusion rules, ROIs, time windows, frequency bands, correction method — goes into `## Out of scope`. With no plan document, list the analysis choices as the code currently implements them and freeze those. A move that would change a frozen item is a deviation: raise it as an open question, never make it.
- **`parameter_sweep` defaults to off.** If the user turns it on, sweeps run on blind inputs against outcome-blind criteria only — e.g. a solver tolerance chosen by ground-truth recovery on simulated data.
- **`evaluation` defaults to `fresh-eval`.** The evaluator receives the diff and the blind-input check outputs, nothing else.

No evaluation mode can make an agent unsee results it has already seen — that is why the blind-input rule exists, and why it is not optional.

---

## exploratory

The loop searches over analysis choices — legitimate, as long as the search is disclosed in full.

- **Fork, never edit, confirmatory scripts.** If a preregistration exists, or the user marks tracked files as confirmatory, copy them to an exploratory fork — by default sibling files with an `_exploratory` suffix, imports adjusted in the fork only — track the fork, and add the originals to `## Out of scope`. Create the fork after the config is confirmed (INIT step 8). The loop never copies a fork back over a confirmatory script; if the user wants an exploratory choice in the confirmatory analysis, that is a preregistration deviation — `/preregistration` → Deviation log, plus a reasoning entry.
- **Separate outputs.** Code the loop runs writes to an `exploratory/` subfolder of its usual output location (e.g. `results/exploratory/`), never over confirmatory outputs.
- **Log every specification.** Every value a sweep tries and every variant an iteration runs on the study data — kept or reverted — goes into the multiverse ledger with its result, before judging. Rows are never edited or deleted: a deleted row is a hidden forking path.
- **Label everything.** `report.md` and `results.md` open with `EXPLORATORY — {N} specifications tried — ledger: .neuroflow/data-analyze/multiverse.md`. The kept specification won a search, so its effect is optimistic — say so wherever it is reported.
- **`parameter_sweep` keeps its usual default (on).**
- **Holdout (recommended).** Before the first iteration, suggest reserving a subset of the data — or independent data — that the loop never reads. After the loop, the chosen specification runs on it once; that run is the only result that can be called confirmatory, and it goes into the ledger too.

### Multiverse ledger

`.neuroflow/data-analyze/multiverse.md` — one per project, shared by every exploratory loop (preprocessing choices belong to the multiverse too). Create it on first use and list it in `.neuroflow/data-analyze/flow.md`; if that folder doesn't exist yet, create it with its `flow.md` and add it to `.neuroflow/flow.md`.

```markdown
# Analysis multiverse — EXPLORATORY
Specifications tried: 37 · Loops: connectivity, erp-window

> Every analysis specification an autoresearch loop ran on the study data, with its result — kept and discarded.
> Nothing here is confirmatory. A result that came from this search is reported together with this ledger or its summary.

| Date | Loop | Iter | Choice | Value | Result | Kept |
|------|------|------|--------|-------|--------|------|
| 2026-10-07 | connectivity | 012 | band-pass low cutoff | 1 Hz | d = 0.41, p = .03 | no |
| 2026-10-07 | connectivity | 012 | band-pass low cutoff | 0.5 Hz | d = 0.52, p = .01 | yes |
```

Update the `Specifications tried` count with every append.

---

## Preregistered projects — every loop

If a preregistration exists, every loop — analysis-touching or not — writes this line into `## Out of scope`:

> Preregistered hypotheses, primary outcomes, and confirmatory/exploratory labels — never changed, dropped, or relabelled.

Plan adherence is a constraint, not a criterion: a criterion can be traded against other gains, a constraint cannot.

---

Background: Gelman & Loken, *The garden of forking paths* (2013); Steegen et al., *Increasing transparency through a multiverse analysis*, Perspectives on Psychological Science (2016); MacCoun & Perlmutter, *Blind analysis: hide results to seek the truth*, Nature (2015).
