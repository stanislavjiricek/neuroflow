---
name: brain-optimize
description: Run a parameter search or fit a computational brain model to experimental data.
phase: brain-optimize
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/brain-optimize/flow.md
  - .neuroflow/brain-build/flow.md
  - skills/phase-brain-optimize/SKILL.md
writes:
  - .neuroflow/brain-optimize/
  - .neuroflow/brain-optimize/flow.md
  - .neuroflow/brain-optimize/runs.md
  - .neuroflow/reasoning/brain-optimize.jsonl
  - .neuroflow/sessions/YYYY-MM-DD.md
lifecycle: full
requires:
  - .neuroflow/brain-build/model-spec.md
produces:
  - .neuroflow/brain-optimize/optimize-plan.md
next:
  - brain-run
---

# /brain-optimize

Read the `neuroflow:phase-brain-optimize` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` (and open with the version notice when the project's `plugin_version` is missing or older than the running neuroflow's version in `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` — **Command lifecycle**, step 3), `flow.md`, and `.neuroflow/brain-optimize/flow.md` before starting. Also check `.neuroflow/brain-build/` for the existing model spec and code location.

**Earlier runs first:** if `.neuroflow/brain-optimize/runs.md` exists, check it (`python <skill base dir>/../phase-brain-run/scripts/runs.py check --file .neuroflow/brain-optimize/runs.md`; exit 1 = something finished or failed) and inspect finished sweeps before starting new ones.

## What this command does

Runs a parameter search or fits the model to experimental data. Two main modes — ask which the user wants:

1. **Parameter sweep** — systematically explore a parameter space to map model behaviour
2. **Data fitting** — optimise model parameters to match target experimental data (spike rates, LFP, EEG, BOLD)

---

## Parameter sweep

Ask:
- Which parameters to sweep and their ranges? (e.g. synaptic weight 0.1–2.0 mS, time constant 5–50 ms)
- What metric to record per run? (mean firing rate, burst index, oscillation frequency, correlation)
- How many parameter combinations? Grid, random, or Latin hypercube sampling?
- Run locally or via HPC/cluster?

Declare the sweep as a spec and run it with `sweep_run.py` (skill → *Sweeps with sweep_run.py*): it iterates over the parameter grid, runs the model for each combination behind a smoke-test gate, and saves per-run metrics to `results.csv`. For random or Latin hypercube sampling, generate the points in code and pass them as the spec's `points`.

## Data fitting

Ask:
- What experimental data to fit to? (file path or description)
- What features to match? (firing rate, ISI distribution, LFP power spectrum, coherence, ERP amplitude)
- What optimisation algorithm? (grid search, Nelder-Mead, differential evolution, Bayesian optimisation, DEAP/evolutionary)
- What is the cost function?
- How many iterations / evaluations are acceptable?

Produce an optimisation script with a cost function, parameter bounds, and optimiser loop.

---

## Steps

1. Write an `optimize-plan.md` — parameters being searched, target features, algorithm, cost function, convergence criteria
2. Implement the optimisation script, or the sweep spec
3. Run a minimal test (2–3 parameter combinations) to confirm the pipeline works end-to-end before a full run — for sweeps, `sweep_run.py`'s smoke gate (`--smoke-only` also times one run). Long or HPC runs follow the skill's pointer to the long-run convention (`runs.md`, no compute on login nodes)
4. After a full run: summarise best-fit parameters, cost value, and whether convergence was reached — from `results.csv`/`summary.json` or the optimiser's own output, computed in code, never asserted from a plot

Save plans and result summaries in `.neuroflow/brain-optimize/`. Write scripts and raw results to `output_path` (from `.neuroflow/brain-optimize/flow.md`, default: `models/optimize/`) — not inside `.neuroflow/`.

---

## At end

- Update `.neuroflow/brain-optimize/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Log key parameter decisions in `.neuroflow/reasoning/brain-optimize.jsonl`
- Update `active_phase` in `project_config.md` if the phase changed
