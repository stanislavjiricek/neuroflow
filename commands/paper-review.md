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

Runs a rigorous pre-submission review of a manuscript. Use the `neuroflow:review-neuro` skill for the full review procedure.

Ask:
1. Where is the manuscript? (path to file, or paste content)
2. What is the target journal?
3. Is there a specific concern to focus on, or a full review?

---

## Review areas

- **Scientific logic** — does the hypothesis follow from the background? Do the methods answer the research question? Does the discussion match the results?
- **Methods completeness** — are all preprocessing and analysis steps documented clearly enough to reproduce?
- **Statistics** — correct tests, assumptions met, multiple comparisons handled, effect sizes reported
- **Writing quality** — clarity, concision, structure
- **Figures** — do they match what is described in the text? Are they legible?
- **Journal fit** — word limit, required sections, citation style

---

## At end

- Save review as `review-[date].md` in `.neuroflow/paper-review/`
- Update `.neuroflow/paper-review/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
