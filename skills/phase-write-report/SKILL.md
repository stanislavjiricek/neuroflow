---
name: phase-write-report
description: Phase guidance for the neuroflow /write-report command. Loaded automatically when /write-report is invoked to orient agent behavior, relevant skills, and workflow hints for the write-report phase.
---

# phase-write-report

The write-report phase generates a structured report from `.neuroflow/` contents — for a specific phase, multiple phases, or the whole project.

## Approach

- Confirm scope (which phase(s)), audience, and depth before loading any files
- Use `flow.md` files to navigate `.neuroflow/` rather than reading all content up front
- Synthesize across phases when the report spans multiple — do not list files, narrate progress

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Writing style

- Do not use dashes as punctuation (-- or ---); use a comma `,` or semicolon `;` instead

## Workflow hints

- Save the report to `results/` or the phase folder specified by the user — confirm `output_path` before writing
- Keep the report concise; a summary of key decisions and outputs is more useful than exhaustive detail
