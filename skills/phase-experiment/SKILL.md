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
- Keep the `/experiment` ground rules in view: the ethics gate before any step with participants, participants only see validated software (never Claude Code), no agent on acquisition PCs during recordings, and no software check is a stimulation-safety interlock
- Audit every generated paradigm with `scripts/psychopy_audit.py` before handing it over

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules
- `neuroflow:pupil-labs-neon-realtime` — load when Pupil Labs Neon eye tracker is part of the recording setup

## Workflow hints

- PsychoPy scripts and config files go to `output_path` (`paradigm/`), not inside `.neuroflow/`
- Save `experiment-plan.md` to `.neuroflow/experiment/` covering design choices, recording parameters, the marker map, and the allocation seed and schedule hash
- Log any paradigm design decision that deviates from the pre-registered plan in `.neuroflow/reasoning/experiment.jsonl`

## Scripts and references

- `scripts/psychopy_audit.py` — static audit of `.py` and `.psyexp` paradigms (frame vs time timing, markers outside `win.callOnFlip`, unreset ports, hard-coded refresh rates, blocking calls, missing logs) plus the marker map; `--csv` checks a run's frame-interval log or trial CSV for dropped frames and off-by-a-frame durations. `python <skill base dir>/scripts/psychopy_audit.py paradigm/` — exit 0 = clean, 1 = warnings, 2 = unreadable input.
- `scripts/allocation.py` — seeded counterbalancing / group allocation schedule with an append-only ledger (`generate`, `next`, `verify`); non-clinical studies only. Exit 0 = done, 1 = refused or findings, 2 = usage error.
- `references/preflight.md` — optional `preflight()` block for the top of a paradigm, plus a manual run-sheet checklist.

## Slash command

`/neuroflow:experiment` — runs this workflow as a slash command.
