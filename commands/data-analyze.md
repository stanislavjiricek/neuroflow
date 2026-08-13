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
  - skills/phase-data-analyze/SKILL.md
writes:
  - .neuroflow/data-analyze/
  - .neuroflow/data-analyze/flow.md
  - .neuroflow/reasoning/data-analyze.json
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /data-analyze

Read the `neuroflow:phase-data-analyze` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/data-analyze/flow.md` before starting. Also check `.neuroflow/ideation/` for the research question and hypothesis, and `.neuroflow/data-preprocess/` for the preprocessing report.

## What this command does

Runs the analysis pipeline on preprocessed data. Ask:
1. What is the analysis goal? (ERP, time-frequency, connectivity, decoding, GLM, other)
2. Where is the preprocessed data?
3. Is there a pre-registered analysis plan to follow?

**If `.neuroflow/preregistration/` exists:** read its `flow.md` and the latest prereg document **before** writing the analysis plan. The analysis plan must state which pre-registered analyses it implements. Any departure from the registered plan is a **deviation**: log it to the preregistration deviations file and write a `reasoning/data-analyze.json` entry at the moment it happens (mandatory trigger in `neuroflow-core`) — never discover drift after the fact.

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
- **Write a reproducibility manifest** `environment.md` next to the analysis scripts in `output_path`: Python/MATLAB version, exact package versions of everything imported, OS, random seeds (permutations, CV splits, decoding), and the git commit hash if tracked. Regenerate on every rerun — it must always answer "which MNE/sklearn versions produced Figure 2"
- Update `.neuroflow/data-analyze/flow.md`
- Log statistical-model and analysis-approach choices to `.neuroflow/reasoning/data-analyze.json` (test selection, correction method, rejected alternatives) — these are mandatory reasoning triggers
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `project_config.md` if phase changed

