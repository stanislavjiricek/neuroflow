---
name: phase-paper-review
description: Phase guidance for the neuroflow /paper-review command. Loaded automatically when /paper-review is invoked to orient agent behavior, relevant skills, and workflow hints for the paper-review phase.
---

# phase-paper-review

The paper-review phase runs a rigorous pre-submission peer review of a neuroscience manuscript.

## Approach

- Gather all three inputs (manuscript, target journal, specific focus or full review) before invoking the review skill
- Delegate the entire review procedure to `neuroflow:review-neuro` — do not conduct the review independently
- Check `.neuroflow/paper-write/` for the current draft before asking the user where the manuscript is

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules
- `neuroflow:review-neuro` — invoke this skill to perform the review; pass manuscript, journal, and focus as inputs

## Workflow hints

- The review is saved automatically by `review-neuro` to `.neuroflow/paper-review/review-[date].md` — do not duplicate this
- Append only a single one-liner to the session log referencing the saved file path
