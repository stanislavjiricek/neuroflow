---
name: phase-brain-run
description: Phase guidance for the neuroflow /brain-run command. Loaded automatically when /brain-run is invoked to orient agent behavior, relevant skills, and workflow hints for running brain model simulations.
user-invocable: false
---

# phase-brain-run

The brain-run phase covers configuring and executing a simulation run — setting duration, time step, inputs, and recording targets, then collecting and sanity-checking outputs.

## Approach

- Locate the model code from `.neuroflow/brain-build/` before configuring a run
- Write `run-config.md` first — make run parameters explicit and reproducible
- **No full run without a fresh smoke record:** `python <skill base dir>/../phase-brain-build/scripts/smoke_test.py status --record .neuroflow/brain-build/smoke-record.json` — exit 0: go; exit 1 (stale, failing or missing): run the smoke test first (`neuroflow:phase-brain-build` → *Smoke test*)
- **Guards live in the run script:** `run_sim.py` stops with a non-zero exit and a one-line reason on NaN, silence or runaway rates (silence can be legitimate in stimulus-off periods — set the guard from `run-config.md`), and writes the run's statistics (mean rate, CV, Fano factor, dominant frequency — whichever apply) to a metrics JSON in the run folder. It records its own provenance with `nf_provenance` (`neuroflow:phase-data-analyze` → *Provenance*)
- Sanity-check outputs immediately after the run: look for no-spike silence, runaway activity, NaN values, or implausible rates before storing results — `python <skill base dir>/../phase-brain-build/scripts/smoke_test.py check <run folder>/metrics.json`; exit 1 names the failed check: report it, do not store the run as valid
- `run-summary.md` copies its numbers from the metrics JSON — never retype or estimate them
- Keep run configs versioned in `.neuroflow/brain-run/` so runs are reproducible

## Long runs and HPC

<!-- nf-rule: LOGIN-NODE -->
- **Never run heavy compute on an HPC login node.** A login node has a scheduler (`sbatch` or `qsub` on PATH) but no job around you (`SLURM_JOB_ID` and `PBS_JOBID` unset — check with `command -v sbatch qsub; echo "${SLURM_JOB_ID}${PBS_JOBID}"`). There, edit, commit and submit only: no simulations, sweeps, preprocessing or fitting, nothing that runs longer than about a minute. Submit a job, or ask for an interactive one (`srun --pty bash`, `qsub -I`) and run inside it.
- **Long runs** (more than ~10 minutes, or must outlive the session) follow `references/long-runs.md`: in-session runs use `run_in_background`; detached and HPC runs are registered in `.neuroflow/brain-run/runs.md` with `python <skill base dir>/scripts/runs.py add …`
- **At the start of /brain-run**, if `.neuroflow/brain-run/runs.md` exists: `python <skill base dir>/scripts/runs.py check --file .neuroflow/brain-run/runs.md` — exit 1: inspect the finished or failed runs and summarize them before new work, then mark each `reviewed` (`runs.py set`); exit 0: continue
- **Job scripts** start from `templates/job-slurm.sh` or `templates/job-pbs.sh` (resources from the smoke test's runtime and memory, mail on end and failure, optional node-local scratch); fill every placeholder

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Workflow hints

- All simulation output files (spike data, voltage traces, figures) go to `output_path` (`models/results/`), not inside `.neuroflow/`
- Save `run-config.md` and `run-summary.md` to `.neuroflow/brain-run/`
- Note any run that produces qualitatively new or unexpected behaviour in `.neuroflow/reasoning/brain-run.jsonl`
- For HPC submission: produce a job script (SLURM/PBS, from `templates/`) alongside `run_sim.py` and save both to `output_path`
- `runs.md` (long-run registry) lives in `.neuroflow/brain-run/` — list it in the phase `flow.md`

## Slash command

`/neuroflow:brain-run` — runs this workflow as a slash command.
