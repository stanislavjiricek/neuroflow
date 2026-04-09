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
  - skills/phase-data-analyze/SKILL.md
writes:
  - .neuroflow/data-analyze/
  - .neuroflow/data-analyze/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /data-analyze

Read the `neuroflow:phase-data-analyze` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/data-analyze/flow.md` before starting. Also check `.neuroflow/ideation/` for the research question and hypothesis, and `.neuroflow/data-preprocess/` for the preprocessing report.

## What this command does

Runs the analysis pipeline on preprocessed data. Ask:
1. What is the analysis goal? (ERP, time-frequency, connectivity, decoding, GLM, other)
2. Where is the preprocessed data?
3. Is there a pre-registered analysis plan to follow?

Apply the appropriate analysis approach for the goal:
- ERPs, time-frequency, connectivity → MNE-Python (Epochs, AverageTFR, spectral_connectivity)
- Decoding / classification → scikit-learn (LDA, SVM, cross-validation)
- Permutation testing → MNE permutation_cluster_test or custom permutation
- fMRI GLM → nilearn FirstLevelModel / SecondLevelModel
- Multimodal (iEEG, ECG, eye tracking) → modality-appropriate tooling

---

## Steps

1. Write an `analysis-plan.md` — what will be computed, which comparisons, which statistical tests, what the expected output is
2. Write and run the analysis scripts
3. Collect results — figures, tables, statistical outputs
4. Audit the statistical approach — verify test assumptions, multiple comparison correction, effect size reporting

Save the analysis plan and results summary in `.neuroflow/data-analyze/`. Write analysis scripts, computed results, and figures to `output_path` (from `.neuroflow/data-analyze/flow.md`, default: `scripts/analysis/` for code, `results/` for outputs, `figures/` for plots) — not inside `.neuroflow/`.

---

## At end

- Save `analysis-summary.md` — key findings, figures produced, open questions
- Update `.neuroflow/data-analyze/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `project_config.md` if phase changed

If `.neuroflow/flowie/wiki/` exists, add a closing nudge:

```
Consider synthesizing key findings into your personal wiki:
  /flowie --wiki-ingest .neuroflow/data-analyze/analysis-summary.md
```
