---
name: phase-brain-optimize
description: Phase guidance for the neuroflow /brain-optimize command. Loaded automatically when /brain-optimize is invoked to orient agent behavior, relevant skills, and workflow hints for parameter search and model fitting.
---

# phase-brain-optimize

The brain-optimize phase covers parameter exploration and model fitting — sweeping a parameter space to map model behaviour, or optimising parameters to match experimental data.

## Approach

- Identify the goal early: exploratory sweep vs targeted fitting to experimental data
- Write `optimize-plan.md` before any code — parameters, bounds, cost function, algorithm, convergence criterion
- Always run a minimal smoke test (2–3 evaluations) before launching a full search
- Prefer algorithms suited to the problem: grid search for low-dimensional spaces; differential evolution or Bayesian optimisation for high-dimensional or expensive simulations

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Workflow hints

- All optimisation scripts and raw results go to `output_path` (`models/optimize/`), not inside `.neuroflow/`
- Save `optimize-plan.md` and post-run summaries to `.neuroflow/brain-optimize/`
- Log algorithm choice and cost function rationale in `.neuroflow/reasoning/brain-optimize.json`
- Common libraries: DEAP, Optuna, scipy.optimize, BluePyOpt, scikit-optimize
