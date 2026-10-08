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
  - .neuroflow/brain-run/runs.md
  - .neuroflow/sessions/YYYY-MM-DD.md
lifecycle: full
requires:
  - .neuroflow/brain-build/model-spec.md
produces:
  - .neuroflow/brain-run/run-config.md
  - .neuroflow/brain-run/run-summary.md
next:
  - paper
  - write-report
---

# /brain-run

Read the `neuroflow:phase-brain-run` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` (and open with the version notice when the project's `plugin_version` is behind the running neuroflow, whose version is in `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` — **Command lifecycle**, step 3), `flow.md`, and `.neuroflow/brain-run/flow.md` before starting. Also check `.neuroflow/brain-build/` to find the model code and `output_path`.

## What this command does

Configures and launches a simulation run of an existing computational brain model, then helps collect, inspect, and save the outputs.

Ask:
1. Which model to run? (path to model code, or pick up from `.neuroflow/brain-build/`)
2. What simulation duration and time step?
3. What inputs / stimuli to apply during this run?
4. What outputs to record? (spike trains, membrane voltage, LFP, population rate, BOLD signal)
5. Run locally or submit to HPC/cluster?

**Earlier runs first:** if `.neuroflow/brain-run/runs.md` exists, check it before configuring anything new (`runs.py check`, skill → *Long runs and HPC*) and inspect what finished.

---

## Steps

1. Write a `run-config.md` — model path, duration, dt, inputs, recording targets, output directory
2. Confirm or generate a run script (`run_sim.py` or equivalent) that loads the model and applies the run config — with the in-script guards, metrics JSON and provenance the skill describes
3. Confirm the smoke record is fresh (`smoke_test.py status`, see the skill), then run the simulation. Short runs: in the foreground. Long runs: `run_in_background`, or detached and registered in `.neuroflow/brain-run/runs.md`. HPC: a job script from the skill's templates, registered with its job id — follow the skill's *Long runs and HPC*
4. After the run: load and inspect outputs — check for obvious errors (no spikes, unbounded activity, NaN values) with `smoke_test.py check` on the run's metrics JSON, produce a brief summary plot or statistics
5. Save a `run-summary.md` — duration, time step, key output statistics (mean firing rate, dominant frequency, etc.) copied from the metrics JSON, path to output files and to the run record (`provenance/…json`)

Save configs and summaries in `.neuroflow/brain-run/`. Write simulation output files (spike data, voltage traces, figures) to `output_path` (from `.neuroflow/brain-run/flow.md`, default: `models/results/`) — not inside `.neuroflow/`.

---

## At end

- Update `.neuroflow/brain-run/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `active_phase` in `project_config.md` if the phase changed
