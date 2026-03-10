---
name: phase-grant-proposal
description: Phase guidance for the neuroflow /grant-proposal command. Loaded automatically when /grant-proposal is invoked to orient agent behavior, relevant skills, and workflow hints for the grant-proposal phase.
---

# phase-grant-proposal

The grant-proposal phase translates a defined research question into a fundable proposal for a specific funding body.

## Approach

- Read `.neuroflow/ideation/` outputs before starting — the research question and any literature must exist first
- Ask about the funder, scheme, and page/word limits before drafting anything
- Structure the proposal section by section; do not write all sections in one pass
- Align significance and innovation language to the funder's stated priorities

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Workflow hints

- All drafted content (aims, narrative, budget tables) goes to `output_path` (`grant/`), not inside `.neuroflow/`
- Save a brief grant summary to `.neuroflow/grant-proposal/` so future commands know funding context
- Log funder, scheme, and deadline in `project_config.md` if not already there
