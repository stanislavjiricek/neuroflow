---
name: paper-review
description: Pre-submission peer review of a neuroscience manuscript — scientific logic, methods, statistics, writing, and figures.
phase: paper-review
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/paper-write/flow.md
  - .neuroflow/paper-review/flow.md
writes:
  - .neuroflow/paper-review/
  - .neuroflow/paper-review/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /paper-review

Follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/paper-review/flow.md` before starting. Check `.neuroflow/paper-write/` for the manuscript draft.

## What this command does

Gather the inputs below, then invoke the `neuroflow:review-neuro` skill to run the full review.  Do not perform the review yourself — delegate entirely to the skill.

Ask:
1. Where is the manuscript? (path to file, paste content, or URL)
2. What is the target journal?
3. Is there a specific concern to focus on, or a full review?

Once you have the answers, pass them to the `neuroflow:review-neuro` skill and let the skill drive the review procedure from start to finish.

---

## At end

- Save review as `review-[date].md` in `.neuroflow/paper-review/`
- Update `.neuroflow/paper-review/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
