---
name: brain-run
description: Run a computational brain model simulation — configure run parameters, launch the simulation, and collect outputs.
phase: brain-run
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/brain-run/flow.md
  - .neuroflow/brain-build/flow.md
  - skills/phase-brain-run/SKILL.md
writes:
  - .neuroflow/brain-run/
  - .neuroflow/brain-run/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /brain-run

Read the `neuroflow:phase-brain-run` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/brain-run/flow.md` before starting. Also check `.neuroflow/brain-build/` to find the model code and `output_path`.

## What this command does

Configures and launches a simulation run of an existing computational brain model, then helps collect, inspect, and save the outputs.

Ask:
1. Which model to run? (path to model code, or pick up from `.neuroflow/brain-build/`)
2. What simulation duration and time step?
3. What inputs / stimuli to apply during this run?
4. What outputs to record? (spike trains, membrane voltage, LFP, population rate, BOLD signal)
5. Run locally or submit to HPC/cluster?

---

## Steps

1. Write a `run-config.md` — model path, duration, dt, inputs, recording targets, output directory
2. Confirm or generate a run script (`run_sim.py` or equivalent) that loads the model and applies the run config
3. Run the simulation (or prepare the submission script for HPC)
4. After the run: load and inspect outputs — check for obvious errors (no spikes, unbounded activity, NaN values), produce a brief summary plot or statistics
5. Save a `run-summary.md` — duration, time step, key output statistics (mean firing rate, dominant frequency, etc.), path to output files

Save configs and summaries in `.neuroflow/brain-run/`. Write simulation output files (spike data, voltage traces, figures) to `output_path` (from `.neuroflow/brain-run/flow.md`, default: `models/results/`) — not inside `.neuroflow/`.

---

## At end

- Update `.neuroflow/brain-run/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `project_config.md` if phase changed
