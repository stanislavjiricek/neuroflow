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
- For real-time and closed-loop tools, make the latency budget a measurable done-criterion and stamp outputs with their source timestamp (`/tool-build` → Real-time and closed-loop tools)
- Stimulation hardware is started by a person; no software check is a safety interlock

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules
- `neuroflow:pupil-labs-neon-realtime` — if the tool involves Pupil Labs Neon hardware, use this skill for device discovery, multi-threaded streaming architecture, and real-time data collection
- `neuroflow:phase-tool-validate` — its `scripts/lsl_check.py` lists LSL streams and measures rate, gaps and latency against a budget

## Workflow hints

- All code goes to `output_path` (`tools/`), not inside `.neuroflow/`
- Save `tool-spec.md` to `.neuroflow/tool-build/` before writing any implementation
- Note key technical decisions (library choice, architecture, interfaces) in `.neuroflow/reasoning/tool-build.jsonl`

## Slash command

`/neuroflow:tool-build` — runs this workflow as a slash command.
