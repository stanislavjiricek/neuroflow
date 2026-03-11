---
name: phase-experiment
description: Phase guidance for the neuroflow /experiment command. Loaded automatically when /experiment is invoked to orient agent behavior, relevant skills, and workflow hints for the experiment phase.
---

# phase-experiment

The experiment phase covers paradigm design, recording setup, and instrument configuration — everything needed before data collection begins.

## Approach

- Identify which sub-task applies (paradigm design, recording setup, instrument config) and handle one at a time
- Read `.neuroflow/ideation/` for the research question and hypothesis before designing anything
- Confirm modality (EEG, fMRI, eye-tracking, ECG, etc.) early; it constrains all downstream decisions
- Write a brief design rationale — not just the implementation

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Workflow hints

- PsychoPy scripts and config files go to `output_path` (`paradigm/`), not inside `.neuroflow/`
- Save `experiment-plan.md` to `.neuroflow/experiment/` covering design choices and recording parameters
- Log any paradigm design decision that deviates from the pre-registered plan in `.neuroflow/reasoning/experiment.json`

## Slash command

`/neuroflow:experiment` — runs this workflow as a slash command.
