---
title: /brain-optimize
---

# `/neuroflow:brain-optimize`

**Run a parameter search or fit a computational brain model to experimental data.**

`/brain-optimize` covers two modes: systematic parameter sweeps to map model behaviour, and data fitting to match experimental recordings.

---

## When to use it

- You want to explore how model outputs change across a range of parameter values
- You want to fit model parameters to experimental data (spike rates, LFP, EEG, BOLD)
- You need a structured optimisation pipeline with a defined cost function

---

## Two modes

Claude asks which you want:

=== "Parameter sweep"

    Systematically explore a parameter space to map model behaviour.

    **Claude asks:**
    - Which parameters to sweep and their ranges (e.g. synaptic weight 0.1–2.0 mS, time constant 5–50 ms)
    - What metric to record per run (mean firing rate, burst index, oscillation frequency, correlation)
    - How many parameter combinations — grid, random, or Latin hypercube sampling
    - Run locally or via HPC/cluster

    **Output:** a sweep script that iterates over the parameter grid, runs the model for each combination, and saves per-run metrics to a results file.

=== "Data fitting"

    Optimise model parameters to match target experimental data.

    **Claude asks:**
    - What experimental data to fit to (file path or description)
    - What features to match (firing rate, ISI distribution, LFP power spectrum, coherence, ERP amplitude)
    - What optimisation algorithm (grid search, Nelder-Mead, differential evolution, Bayesian optimisation, DEAP/evolutionary)
    - What is the cost function
    - How many iterations / evaluations are acceptable

    **Output:** an optimisation script with a cost function, parameter bounds, and optimiser loop.

---

## Steps

1. Write `optimize-plan.md` — parameters being searched, target features, algorithm, cost function, convergence criteria
2. Implement the optimisation or sweep script
3. Run a minimal test (2–3 parameter combinations) to confirm the pipeline works end-to-end
4. After a full run: summarise best-fit parameters, cost value, and whether convergence was reached

Plans and result summaries go to `.neuroflow/brain-optimize/`. Scripts and raw results go to your `models/optimize/` folder.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/brain-optimize/flow.md`, `.neuroflow/brain-build/flow.md` |
| Writes | `.neuroflow/brain-optimize/`, `.neuroflow/brain-optimize/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md`, `models/optimize/` (scripts and results) |

---

## Related commands

- [`/brain-build`](brain-build.md) — assemble the model before optimising
- [`/brain-run`](brain-run.md) — run the model with best-fit parameters after optimisation
