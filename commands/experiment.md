---
name: experiment
description: Full experiment preparation — paradigm design (PsychoPy), recording setup, and instrument configuration.
phase: experiment
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/ideation/flow.md
  - .neuroflow/experiment/flow.md
  - .neuroflow/ethics/status.md
  - skills/phase-experiment/SKILL.md
writes:
  - .neuroflow/experiment/
  - .neuroflow/experiment/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
lifecycle: full
produces:
  - .neuroflow/experiment/experiment-plan.md
  - .neuroflow/experiment/recording-setup.md
next:
  - tool-validate
  - preregistration
---

# /experiment

Read the `neuroflow:phase-experiment` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` (and open with the version notice when the project's `plugin_version` is missing or older than the running neuroflow's version in `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` — **Command lifecycle**, step 3), `flow.md`, and `.neuroflow/experiment/flow.md` before starting. Also check `.neuroflow/ideation/` for research question and hypothesis.

## Ground rules

<!-- nf-rule: ETHICS-GATE -->
**No data collection steps before ethics status is approved.** Designing the paradigm, the recording setup and bench tests without participants need no approval (the ethics application usually needs them). Steps that involve participants — running or scheduling sessions, pilots with volunteers, allocating participants, preparing a participant run sheet — first read the frontmatter of `.neuroflow/ethics/status.md` (a legacy table-only file counts with its `Status` and `Expires` rows). If `status` is not `approved`, it was set by the model (`set_by: model`), or `expires` has passed, stop those steps and say why, pointing to `/ethics`. Projects that note `ethics: not-applicable` in the `project_config.md` frontmatter are outside the gate.

- **Participants only ever see validated software.** Stimuli, questionnaires and consent run in PsychoPy (or the software the approved protocol names), never in Claude Code's terminal: there is no vsync or verifiable onset there, and answers would reach the model and every installed plugin.
- **No agent on the acquisition PC during a recording.** Close Claude Code and other agents on the stimulus and recording machines while a participant is recorded. Paradigms run from PsychoPy or a terminal the experimenter controls.
- **No software check is a stimulation-safety interlock.** For TMS, tES or any other stimulation, safety comes from the device's hardware limits, the approved protocol and the lab's procedures. A person starts stimulation; never write code that starts it on its own, and never describe an audit, hook or guard here as protection.

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

Produce a PsychoPy script following neuroscience paradigm best practices. Save as `paradigm-[name].py` in `output_path` (from `.neuroflow/experiment/flow.md`, default: `paradigm/`) — not inside `.neuroflow/`.

Timing in the script: present visual stimuli for a number of frames, not with `core.wait()`; send markers with `win.callOnFlip(...)` so they leave with the stimulus frame (and reset parallel-port codes to 0); measure the refresh rate at start-up (`win.getActualFrameRate()`) and stop if it is not the expected one; set `win.recordFrameIntervals = True` and save the intervals.

Then audit it: `python <phase-experiment base dir>/scripts/psychopy_audit.py paradigm/` (reads `.py` and `.psyexp` statically; PsychoPy is not needed). Exit 0 = no warnings, 1 = warnings to fix or justify in `experiment-plan.md`, 2 = a file could not be read. Copy the marker map it prints (each code, and whether it is sent on the flip) into `experiment-plan.md` for `/tool-validate`.

- **Counterbalancing and allocation.** If condition orders or group allocation are part of the design, generate the schedule once from a recorded seed: `python <phase-experiment base dir>/scripts/allocation.py generate --scheme williams|latin|full|block --conditions ... --participants N --seed S --out paradigm/allocation/schedule.csv`, then hand out slots at the lab with `allocation.py next --schedule paradigm/allocation/schedule.csv --ledger paradigm/allocation/ledger.csv --participant sub-NN` (append-only ledger; a replacement takes over the slot of the person replaced with `--replaces`). Record the seed and the schedule's SHA-256 in `experiment-plan.md` and the preregistration; skipped slots and replacements are deviations. Exit 1 = refused (already allocated, schedule exhausted or changed). For non-clinical studies only: a clinical trial uses its trial unit's validated randomisation system.
- **Preflight (optional).** Offer the `preflight()` block from `<phase-experiment base dir>/references/preflight.md` for the top of the paradigm. It checks the refresh rate, free disk space, LSL streams, the trigger port and the ethics expiry, and appends a line to a local acquisition log, however the paradigm is launched.

## Recording setup

Ask:
- Modality and hardware (EEG amp, eye tracker, Pupil Labs Neon, etc.)
- Number of channels and electrode placement
- Sampling rate, reference, ground
- Mains (power-line) frequency at the site (50 or 60 Hz) and the stimulus display's refresh rate — the BIDS sidecars need the first, frame timing the second
- File format and storage location

Produce a `recording-setup.md` checklist in `.neuroflow/experiment/`.

## Instrument configuration

Cover LSL outlet/inlet setup, trigger box wiring, synchronisation between streams.

Check stream health with `python <phase-tool-validate base dir>/scripts/lsl_check.py` (lists the streams on the network; `--stream NAME --duration 10` measures rate, gaps, clock offset and latency for named streams only). Exit 0 = healthy, 1 = findings (if nothing resolves, follow its multicast and firewall hint), 2 = pylsl not installed.

---

## At end

- Update `.neuroflow/experiment/flow.md` with any new files
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `active_phase` in `project_config.md` if the phase changed
