---
name: phase-tool-validate
description: Phase guidance for the neuroflow /tool-validate command. Loaded automatically when /tool-validate is invoked to orient agent behavior, relevant skills, and workflow hints for the tool-validate phase.
---

# phase-tool-validate

The tool-validate phase creates and runs a testing pipeline to verify that a tool or paradigm works correctly — timing, markers, data output, and edge cases.

## Approach

- Read `.neuroflow/tool-build/` outputs before planning validation — understand what was built first
- Write a `validation-plan.md` before running any tests
- Cover timing accuracy, marker integrity, data output format, and known edge cases
- Report results objectively — include failures, not just passes

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Workflow hints

- Test scripts and logs go to `output_path` (`tools/`), not inside `.neuroflow/`
- Save `validation-report-[date].md` to `.neuroflow/tool-validate/` summarizing pass/fail status
- If validation reveals a design flaw, log the finding in `.neuroflow/reasoning/tool-validate.json` and loop back to tool-build
