---
name: phase-tool-build
description: Phase guidance for the neuroflow /tool-build command. Loaded automatically when /tool-build is invoked to orient agent behavior, relevant skills, and workflow hints for the tool-build phase.
---

# phase-tool-build

The tool-build phase designs and implements lab tools or software pipelines — real-time systems, data acquisition, LSL integrations, or custom analysis pipelines.

## Approach

- Define done-criteria and the tool specification before writing any code
- Ask which type of tool is needed (acquisition, real-time processing, LSL, analysis pipeline, other)
- Write `tool-spec.md` first; get confirmation before implementation begins
- Prefer tested, modular components over monolithic scripts

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Workflow hints

- All code goes to `output_path` (`tools/`), not inside `.neuroflow/`
- Save `tool-spec.md` to `.neuroflow/tool-build/` before writing any implementation
- Note key technical decisions (library choice, architecture, interfaces) in `decisions.md`
