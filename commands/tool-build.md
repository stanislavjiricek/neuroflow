---
name: tool-build
description: Build a lab tool or software pipeline — real-time systems, data acquisition, LSL integrations, custom analysis pipelines, or other technical infrastructure.
phase: tool-build
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/tool-build/flow.md
  - skills/phase-tool-build/SKILL.md
writes:
  - .neuroflow/tool-build/
  - .neuroflow/tool-build/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
lifecycle: full
produces:
  - .neuroflow/tool-build/tool-spec.md
next:
  - tool-validate
---

# /tool-build

Read the `neuroflow:phase-tool-build` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/tool-build/flow.md` before starting.

## What this command does

Helps the user design and build a lab tool or software pipeline. No research question driving it — the output is working code and documentation.

Ask:
1. What kind of tool? (real-time EEG feedback, data acquisition pipeline, BCI system, LSL integration, paradigm, preprocessing pipeline, other)
2. What hardware or software does it interface with? (amplifier, eye tracker including Pupil Labs Neon, PsychoPy, BrainFlow, LSL, MNE, other)
3. What programming language?
4. Standalone or integrates with an existing setup?
5. What is the definition of "done" — what must the tool do to be considered working?

---

## Steps

1. Write a `tool-spec.md` — what the tool does, inputs/outputs, hardware requirements, constraints
2. Plan the implementation: architecture, key modules, data flow
3. Build the tool iteratively — write code, test, refine
4. Apply domain best practices for the tech stack involved (LSL, PsychoPy, BrainFlow, MNE, etc.)

Save specs and notes (`tool-spec.md`, code plan) in `.neuroflow/tool-build/`. Write the actual tool code to `output_path` (from `.neuroflow/tool-build/flow.md`, default: `tools/`) — not inside `.neuroflow/`.

## Real-time and closed-loop tools

- **A latency budget is a done-criterion.** Write it into `tool-spec.md` as a number, e.g. "p95 end-to-end latency ≤ 50 ms, max ≤ 100 ms".
- **Make latency measurable.** Push every output with the timestamp of the newest input sample it was computed from (`outlet.push_sample(x, timestamp=source_ts)`), and use `inlet.time_correction()` for streams from other machines; without that, latency numbers are confidently wrong.
- **Measure it:** `python <phase-tool-validate base dir>/scripts/lsl_check.py --stream <output stream> --duration 60 --budget-ms 50 --log latency.csv` reports p50 / p95 / max against the budget (exit 1 = over budget or stream problems). This is processing and transport latency; stimulus-to-photon latency needs a photodiode (`/tool-validate`).
- **Recordings do not depend on an agent.** A tool used during participant sessions runs on its own (a script or app the experimenter starts), never inside or driven by a Claude Code session on the acquisition PC.
- **Stimulation hardware.** For TMS, tES or other stimulators, a person starts stimulation: never write code that triggers it on its own, and never describe a software check, hook or guard as a safety interlock — the device's hardware limits, the approved protocol and the lab's procedures are the protection.

---

## At end

- Update `.neuroflow/tool-build/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `active_phase` in `project_config.md` if the phase changed
