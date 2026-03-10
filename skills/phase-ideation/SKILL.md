---
name: phase-ideation
description: Phase guidance for the neuroflow /ideation command. Loaded automatically when /ideation is invoked to orient agent behavior, relevant skills, and workflow hints for the ideation phase.
---

# phase-ideation

The ideation phase is the entry point of a research project — sharpening a vague idea into a testable research question.

## Approach

- Identify which entry point applies (brainstorm, literature explore, formalize, proposal) before doing anything else
- Resist generating a full proposal before the research question is clear — sequence matters
- Use the `scholar` agent for any literature search; do not search manually
- Keep outputs hypothesis-driven and concise; avoid scope creep at this stage
- If `project_config.md` already has a research question, confirm whether to refine or restart

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Workflow hints

- The research question produced here anchors every downstream phase — write it precisely
- Save the final research question to `.neuroflow/ideation/research-question.md`
- Update `project_config.md` if the research question is defined or changed
