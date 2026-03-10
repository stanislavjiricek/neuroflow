---
name: phase-paper-write
description: Phase guidance for the neuroflow /paper-write command. Loaded automatically when /paper-write is invoked to orient agent behavior, relevant skills, and workflow hints for the paper-write phase.
---

# phase-paper-write

The paper-write phase generates a manuscript draft from analysis results, figures, and project memory accumulated across all prior phases.

## Approach

- Read upstream phase flows (ideation, data-analyze, experiment) before drafting — pull facts from memory, not from recall
- Confirm the target journal before writing; it determines structure, length, and style
- Draft section by section in logical order; write the abstract last
- Distinguish what the results show from what they mean — keep interpretation in Discussion

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Workflow hints

- The manuscript draft goes to `output_path` (`manuscript/`), not inside `.neuroflow/`
- Save `manuscript-plan.md` to `.neuroflow/paper-write/` with journal target, section outline, and author list
- Log any framing or scope decisions in `decisions.md` if they differ from the original research question
