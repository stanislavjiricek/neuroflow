---
name: paper-write
description: Generate a manuscript draft from analysis results and figures.
phase: paper-write
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/ideation/flow.md
  - .neuroflow/data-analyze/flow.md
  - .neuroflow/paper-write/flow.md
  - skills/phase-paper-write/SKILL.md
writes:
  - .neuroflow/paper-write/
  - .neuroflow/paper-write/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /paper-write

Read the `neuroflow:phase-paper-write` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/paper-write/flow.md` before starting. Load context from `.neuroflow/ideation/` (research question, hypothesis) and `.neuroflow/data-analyze/` (results summary).

## What this command does

Produces a manuscript draft. Ask:
1. What is the target journal?
2. LaTeX or Word format?
3. Are figures ready or do they still need to be generated?
4. Which sections does the user want to draft first, or should it be the full paper?

For LaTeX output, use standard `article` or journal-specific document class. Adapt formatting to the target journal's author guidelines.

---

## Sections

Write sections in this order if doing the full paper:

1. **Title + authors** — ask the user
2. **Abstract** — write last, summarise after other sections are done
3. **Introduction** — background, gap, research question, hypothesis; use `.neuroflow/ideation/` content
4. **Methods** — participants, recording setup, paradigm, preprocessing, analysis; pull from `.neuroflow/experiment/`, `.neuroflow/data/`, `.neuroflow/data-preprocess/`, `.neuroflow/data-analyze/`
5. **Results** — present findings without interpretation; reference figures
6. **Discussion** — interpret findings, compare to prior work, limitations, future directions
7. **References** — pull from `.neuroflow/ideation/` (literature collected via scholar agent)

Adapt to journal word limits and section requirements.

---

## At end

- Save the draft as `manuscript-[date].md` or `.tex` in `output_path` (from `.neuroflow/paper-write/flow.md`, default: `manuscript/`) — not inside `.neuroflow/`
- Update `.neuroflow/paper-write/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `project_config.md` if phase changed
