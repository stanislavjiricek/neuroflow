---
name: phase-brain-run
description: Phase guidance for the neuroflow /brain-run command. Loaded automatically when /brain-run is invoked to orient agent behavior, relevant skills, and workflow hints for running brain model simulations.
---

# phase-brain-run

The brain-run phase covers configuring and executing a simulation run — setting duration, time step, inputs, and recording targets, then collecting and sanity-checking outputs.

## Approach

- Locate the model code from `.neuroflow/brain-build/` before configuring a run
- Write `run-config.md` first — make run parameters explicit and reproducible
- Sanity-check outputs immediately after the run: look for no-spike silence, runaway activity, NaN values, or implausible rates before storing results
- Keep run configs versioned in `.neuroflow/brain-run/` so runs are reproducible

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Workflow hints

- All simulation output files (spike data, voltage traces, figures) go to `output_path` (`models/results/`), not inside `.neuroflow/`
- Save `run-config.md` and `run-summary.md` to `.neuroflow/brain-run/`
- Note any run that produces qualitatively new or unexpected behaviour in `.neuroflow/reasoning/brain-run.json`
- For HPC submission: produce a job script (SLURM/PBS) alongside `run_sim.py` and save both to `output_path`

## Slash command

`/neuroflow:brain-run` — runs this workflow as a slash command.
