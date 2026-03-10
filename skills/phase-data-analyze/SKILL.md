---
name: phase-data-analyze
description: Phase guidance for the neuroflow /data-analyze command. Loaded automatically when /data-analyze is invoked to orient agent behavior, relevant skills, and workflow hints for the data-analyze phase.
---

# phase-data-analyze

The data-analyze phase applies statistical and computational methods to preprocessed data to test the research hypothesis.

## Approach

- Read `.neuroflow/ideation/` for the research question and `.neuroflow/data-preprocess/` for the preprocessing report before choosing methods
- Write an `analysis-plan.md` first; do not write analysis code before the plan is accepted
- Audit statistical assumptions explicitly (normality, sphericity, independence) before selecting tests
- Apply appropriate multiple-comparison correction; if omitted, flag it and explain why

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Workflow hints

- All code, results, and figures go to `output_path` (`scripts/analysis/`, `results/`, `figures/`), not inside `.neuroflow/`
- Save `analysis-plan.md` to `.neuroflow/data-analyze/` before running any scripts
- Log deviations from a pre-registered analysis plan in `.neuroflow/reasoning/data-analyze.json`
