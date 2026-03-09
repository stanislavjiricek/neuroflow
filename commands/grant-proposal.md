---
name: grant-proposal
description: Write a grant application. Can follow from /ideation. Covers funding body, specific aims, significance, innovation, approach, budget, and timeline.
phase: grant-proposal
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/ideation/flow.md
  - .neuroflow/grant-proposal/flow.md
writes:
  - .neuroflow/grant-proposal/
  - .neuroflow/grant-proposal/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /grant-proposal

Follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/grant-proposal/flow.md` before starting. Also read `.neuroflow/ideation/flow.md` if it exists — load any research question or proposal document from there.

## What this command does

Helps the user write a grant application. Ask:

1. Which funding body / scheme? (e.g. NIH R01, ERC, GAČR, institutional grant)
2. What is the page / word limit and required sections?
3. Is there an existing project proposal or research question to build from? (check `.neuroflow/ideation/`)

Then produce the grant document section by section. Standard sections:

- **Specific aims** — what you will do and why it matters (usually 1 page)
- **Significance** — the problem and why it is important
- **Innovation** — what is new about this approach
- **Approach** — methods, timeline, expected outcomes, limitations and alternatives
- **Budget** — personnel, equipment, consumables (ask the user for numbers)
- **Timeline** — milestones mapped to funding period

Adapt sections to match the actual requirements of the target funding body.

---

## At end

- Save the grant document as `grant-[funder]-[date].md` in `.neuroflow/grant-proposal/`
- Update `.neuroflow/grant-proposal/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `project_config.md` if phase changed
