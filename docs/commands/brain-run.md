---
title: /brain-run
---

# `/neuroflow:brain-run`

**Run a computational brain model simulation — configure run parameters, launch, and collect outputs.**

`/brain-run` handles everything after the model is built: configuring a run, launching the simulation, inspecting outputs, and saving results.

---

## When to use it

- You want to run a simulation of an assembled model
- You need to configure simulation duration, time step, and recording targets
- You want to submit a run to HPC or a cluster
- You need to inspect and summarise simulation outputs

---

## What it does

Claude asks:

1. Which model to run — path to model code, or picks it up from `.neuroflow/brain-build/`
2. What simulation duration and time step
3. What inputs / stimuli to apply during this run
4. What outputs to record (spike trains, membrane voltage, LFP, population rate, BOLD signal)
5. Run locally or submit to HPC/cluster

---

## Steps

1. Write `run-config.md` — model path, duration, dt, inputs, recording targets, output directory
2. Confirm or generate a run script (`run_sim.py` or equivalent) that loads the model and applies the run config
3. Run the simulation (or prepare the HPC submission script)
4. After the run: load and inspect outputs — check for obvious errors (no spikes, unbounded activity, NaN values), produce a brief summary plot or statistics
5. Write `run-summary.md` — duration, time step, key output statistics (mean firing rate, dominant frequency), path to output files

Configs and summaries go to `.neuroflow/brain-run/`. Simulation output files (spike data, voltage traces, figures) go to `models/results/`.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/brain-run/flow.md`, `.neuroflow/brain-build/flow.md` |
| Writes | `.neuroflow/brain-run/`, `.neuroflow/brain-run/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md`, `models/results/` (simulation outputs) |

---

## Related commands

- [`/brain-build`](brain-build.md) — assemble the model before running
- [`/brain-optimize`](brain-optimize.md) — fit parameters before a final run
