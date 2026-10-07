---
name: phase-brain-optimize
description: Phase guidance for the neuroflow /brain-optimize command. Loaded automatically when /brain-optimize is invoked to orient agent behavior, relevant skills, and workflow hints for parameter search and model fitting.
---

# phase-brain-optimize

The brain-optimize phase covers parameter exploration and model fitting — sweeping a parameter space to map model behaviour, or optimising parameters to match experimental data.

## Approach

- Identify the goal early: exploratory sweep vs targeted fitting to experimental data
- Write `optimize-plan.md` before any code — parameters, bounds, cost function, algorithm, convergence criterion
- Always run a minimal smoke test (2–3 evaluations) before launching a full search — for grid sweeps, `sweep_run.py`'s smoke gate does it; the model's smoke record must also be fresh (`neuroflow:phase-brain-build` → *Smoke test*)
- Prefer algorithms suited to the problem: grid search for low-dimensional spaces; differential evolution or Bayesian optimisation for high-dimensional or expensive simulations
- Convergence is computed, not eyeballed: a grid sweep returns the best grid point, not an optimum (`sweep_run.py` warns when the best value sits on the grid edge); an optimiser has converged only when its own criterion in code says so (e.g. `scipy.optimize` result `success`, no improvement over the last N trials)

## Sweeps with sweep_run.py

Declare the sweep in a JSON spec next to the sweep outputs (`models/optimize/<name>/spec.json`, or anywhere in `output_path`) — the command template with `{parameter}` and `{outdir}` placeholders, the `grid` (and/or explicit `points`), the `metric` (a JSON file + key, or a stdout regex), an optional `goal` (`min`, `max` or `target`), `smoke` configurations, `out_dir`, `timeout_s`, `workers`. The full format is in the script's `--help` header.

- List first: `python <skill base dir>/scripts/sweep_run.py <spec> --dry-run` — confirm the configuration count with the person before a long sweep
- Run: `python <skill base dir>/scripts/sweep_run.py <spec>` — the smoke configuration (default: the first grid point) runs first; the sweep starts only if it exits 0 with a finite metric. `--smoke-only` runs just the gate and reports the per-run time, for estimating the sweep's duration
- Exit 0: every configuration produced its metric. Exit 1: the smoke gate failed (sweep not started — fix the model or spec) or some configurations failed (`runs/<id>/log.txt`); report them, rerun with `--resume`. Exit 2: spec or usage error
- Results: `results.csv` (one row per configuration) and `summary.json` (best configurations, edge warnings) in `out_dir` — the summary in `.neuroflow/brain-optimize/` quotes these files, never retyped numbers
- Longer than ~10 minutes: start it with `run_in_background`, or detached and registered in `.neuroflow/brain-optimize/runs.md` — `neuroflow:phase-brain-run` → `references/long-runs.md`. On a cluster, a sweep is a job (or an array job), never a login-node process (`neuroflow:phase-brain-run` → *Long runs and HPC*)

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Workflow hints

- All optimisation scripts and raw results go to `output_path` (`models/optimize/`), not inside `.neuroflow/`
- Save `optimize-plan.md` and post-run summaries to `.neuroflow/brain-optimize/`
- Log algorithm choice and cost function rationale in `.neuroflow/reasoning/brain-optimize.jsonl`
- Common libraries: DEAP, Optuna, scipy.optimize, BluePyOpt, scikit-optimize

## Slash command

`/neuroflow:brain-optimize` — runs this workflow as a slash command.
