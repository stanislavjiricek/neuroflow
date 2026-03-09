---
name: tool-validate
description: Create a comprehensive testing pipeline to verify that a tool or paradigm works correctly — timing, markers, data output, edge cases.
phase: tool-validate
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/tool-build/flow.md
  - .neuroflow/experiment/flow.md
  - .neuroflow/tool-validate/flow.md
writes:
  - .neuroflow/tool-validate/
  - .neuroflow/tool-validate/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /tool-validate

Follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/tool-validate/flow.md` before starting. Also check `.neuroflow/tool-build/` and `.neuroflow/experiment/` for relevant specs and code.

## What this command does

Creates a testing pipeline to verify a tool or paradigm is working correctly before real data collection begins.

Ask:
1. What needs to be validated? (paradigm timing, marker accuracy, LSL streaming, data output format, hardware integration, edge cases)
2. What is the tool / paradigm under test? (point to the relevant file or folder)
3. What does "correct" look like — what are the pass/fail criteria?

---

## Steps

1. Write a `validation-plan.md` — what is being tested, how, and what the pass criteria are
2. Build the test scripts or procedures
3. Run the validation and record results
4. For paradigm-specific checks (timing, markers, edge cases), audit the PsychoPy script directly — verify trial timing, marker codes, response handling, and edge cases

Save all output in `.neuroflow/tool-validate/`.

---

## At end

- Update `.neuroflow/tool-validate/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `project_config.md` if phase changed
