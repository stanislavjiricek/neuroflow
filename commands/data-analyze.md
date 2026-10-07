---
name: data-analyze
description: Run an analysis pipeline on preprocessed data — ERPs, time-frequency, connectivity, decoding, GLM, or other modality-appropriate analyses.
phase: data-analyze
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/ideation/flow.md
  - .neuroflow/data-preprocess/flow.md
  - .neuroflow/data-analyze/flow.md
  - .neuroflow/preregistration/flow.md
  - .neuroflow/preregistration/status.md
  - skills/phase-data-analyze/SKILL.md
writes:
  - .neuroflow/data-analyze/
  - .neuroflow/data-analyze/flow.md
  - .neuroflow/data-analyze/multiverse.md
  - .neuroflow/data-analyze/runs.md
  - .neuroflow/reasoning/data-analyze.jsonl
  - .neuroflow/preregistration/deviations.md
  - .neuroflow/sessions/YYYY-MM-DD.md
lifecycle: full
requires:
  - .neuroflow/data-preprocess/preprocess-report.md
produces:
  - .neuroflow/data-analyze/analysis-plan.md
  - .neuroflow/data-analyze/analysis-summary.md
next:
  - paper
  - write-report
---

# /data-analyze

Read the `neuroflow:phase-data-analyze` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/data-analyze/flow.md` before starting. Also check `.neuroflow/ideation/` for the research question and hypothesis, and `.neuroflow/data-preprocess/` for the preprocessing report.

**Earlier runs first:** if `.neuroflow/data-analyze/runs.md` exists, check it (`python <skill base dir>/../phase-brain-run/scripts/runs.py check --file .neuroflow/data-analyze/runs.md`; exit 1 = something finished or failed) and inspect finished runs before starting new ones.

## What this command does

Runs the analysis pipeline on preprocessed data. Ask:
1. What is the analysis goal? (ERP, time-frequency, connectivity, decoding, GLM, other)
2. Where is the preprocessed data?
3. Is there a pre-registered analysis plan to follow?

**If `.neuroflow/preregistration/` exists:** read its `flow.md` and the latest prereg document **before** writing the analysis plan. The analysis plan must state which pre-registered analyses it implements. Any departure from the registered plan is a **deviation**: append it to `.neuroflow/preregistration/deviations.md` and write a `reasoning/data-analyze.jsonl` entry at the moment it happens (mandatory trigger in `neuroflow-core`) — never discover drift after the fact.

**Peeking check — before any confirmatory test:** read `planned_n` from the frontmatter of `.neuroflow/preregistration/status.md`. If the test would include fewer participants than `planned_n`, stop and say so: a confirmatory test on a partial sample is an interim look, and looking before the sample is complete inflates the false-positive rate. Run it only if the person confirms; then append the interim look (date, N analysed of `planned_n`, which test, why) to `deviations.md` and write a reasoning entry. A preregistration that plans interim analyses (a sequential design with its alpha spending) is followed as registered instead. Without `planned_n` there is nothing to compare — say in `analysis-summary.md` that no sample size was registered.

Apply the appropriate analysis approach for the goal:
- ERPs, time-frequency, connectivity → MNE-Python (Epochs, AverageTFR, spectral_connectivity)
- Decoding / classification → scikit-learn (LDA, SVM, cross-validation)
- Permutation testing → MNE permutation_cluster_test or custom permutation
- fMRI GLM → nilearn FirstLevelModel / SecondLevelModel
- Multimodal (iEEG, ECG, eye tracking) → modality-appropriate tooling

---

## Steps

1. Write an `analysis-plan.md` — what will be computed, which comparisons, which statistical tests, what the expected output is; label each analysis confirmatory (preregistered) or exploratory
2. Write and run the analysis scripts — each records its provenance with `nf_provenance` (skill → *Provenance*); runs longer than ~10 minutes follow the long-run convention the skill points to; notebooks follow the skill's *Notebooks*
3. Collect results — figures, tables, statistical outputs, taken from the files the scripts wrote
4. Audit the statistical approach — verify test assumptions, multiple comparison correction, effect size reporting
5. Optional, exploratory: test robustness across defensible analysis choices with `multiverse.py` (skill → *Multiverse*); every specification lands in `multiverse.md`
6. Optional, before `/paper --submit` or `/output --archive`: reproduce the confirmatory results from a fresh clone with `cleanroom.py` (skill → *Clean-room reproduction*)

Save the analysis plan and results summary in `.neuroflow/data-analyze/`. Write analysis scripts, computed results, and figures to `output_path` (from `.neuroflow/data-analyze/flow.md`, default: `scripts/analysis/` for code, `results/` for outputs, `figures/` for plots) — not inside `.neuroflow/`.

---

## At end

- Save `analysis-summary.md` — key findings, figures produced, open questions. If `.neuroflow/data-analyze/multiverse.md` exists, label every result that came from it as exploratory and state how many specifications were tried — the ledger's rows, which cover only analyses logged through autoresearch or `multiverse.py`; say so
- **Reproducibility manifest** — `environment.md` next to the analysis scripts in `output_path`, plus one run record per run in `provenance/`, both written by `nf_provenance` as the scripts run: Python version, exact versions of every imported package, OS, the random seeds the scripts declare (permutations, CV splits, decoding), and the git commit with a dirty flag. Never write or edit them by hand; every rerun regenerates `environment.md`, so it always answers "which MNE/sklearn versions produced Figure 2"
- Update `.neuroflow/data-analyze/flow.md`
- Log statistical-model and analysis-approach choices to `.neuroflow/reasoning/data-analyze.jsonl` (test selection, correction method, rejected alternatives) — these are mandatory reasoning triggers
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `active_phase` in `project_config.md` if the phase changed

