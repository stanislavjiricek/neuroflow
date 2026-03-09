---
name: experiment
description: Full experiment preparation — paradigm design (PsychoPy), recording setup, and instrument configuration.
phase: experiment
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/ideation/flow.md
  - .neuroflow/experiment/flow.md
writes:
  - .neuroflow/experiment/
  - .neuroflow/experiment/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /experiment

Follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/experiment/flow.md` before starting. Also check `.neuroflow/ideation/` for research question and hypothesis.

## What this command does

Covers everything needed before data collection starts. Three areas — ask which the user wants to work on:

1. **Paradigm design** — design the experiment structure and produce a PsychoPy script
2. **Recording setup** — define recording parameters, electrode placement, sampling rate, reference, file format
3. **Instrument configuration** — LSL integration, trigger/marker setup, hardware connections

---

## Paradigm design

Ask:
- What paradigm type? (oddball, N-back, go/no-go, resting state, custom)
- How many trials / blocks / conditions?
- What stimuli? (visual, auditory, tactile)
- What responses are collected?
- Timing requirements (ISI, SOA, jitter)?
- Markers needed — what events must be tagged?

Produce a PsychoPy script following neuroscience paradigm best practices. Save as `paradigm-[name].py` in `.neuroflow/experiment/`.

## Recording setup

Ask:
- Modality and hardware (EEG amp, eye tracker, etc.)
- Number of channels and electrode placement
- Sampling rate, reference, ground
- File format and storage location

Produce a `recording-setup.md` checklist in `.neuroflow/experiment/`.

## Instrument configuration

Cover LSL outlet/inlet setup, trigger box wiring, synchronisation between streams.

---

## At end

- Update `.neuroflow/experiment/flow.md` with any new files
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `project_config.md` if phase changed
