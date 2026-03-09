---
name: tool-build
description: Build a lab tool or software pipeline — real-time systems, data acquisition, LSL integrations, custom analysis pipelines, or other technical infrastructure.
phase: tool-build
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/tool-build/flow.md
writes:
  - .neuroflow/tool-build/
  - .neuroflow/tool-build/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /tool-build

Follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/tool-build/flow.md` before starting.

## What this command does

Helps the user design and build a lab tool or software pipeline. No research question driving it — the output is working code and documentation.

Ask:
1. What kind of tool? (real-time EEG feedback, data acquisition pipeline, BCI system, LSL integration, paradigm, preprocessing pipeline, other)
2. What hardware or software does it interface with? (amplifier, eye tracker, PsychoPy, BrainFlow, LSL, MNE, other)
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

---

## At end

- Update `.neuroflow/tool-build/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `project_config.md` if phase changed
