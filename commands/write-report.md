---
name: write-report
description: Generate a structured report from .neuroflow/ contents — for a specific phase, multiple phases, or the whole project.
phase: write-report
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/sessions/
  - .neuroflow/{phase}/flow.md    # for each phase covered in the report
  - skills/phase-write-report/SKILL.md
writes:
  - .neuroflow/write-report/
  - .neuroflow/write-report/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /write-report

Read the `neuroflow:phase-write-report` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` and `flow.md` before starting.

## What this command does

Generates a structured report from `.neuroflow/` contents. Useful for progress updates, lab meeting summaries, supervision reports, or internal documentation.

---

## Steps

1. Ask:
   - Which phase(s) to cover? (one phase, a selection, or the whole project)
   - Focus on recent changes only or full overview?
   - Any specific audience or format? (e.g. for supervisor, for lab meeting, internal)

2. Load the relevant `flow.md` files and session logs for the selected phases. Read key documents (analysis summary, preprocess report, etc.) as needed — use `flow.md` to navigate, load full files only when necessary.

3. Write the report:
   - **Header** — project name, date, phases covered
   - **Per phase** — what was done, key outputs, open questions
   - **Overall status** — current phase, what's next

4. Save as `report-[date].md` in `.neuroflow/write-report/`.

---

## At end

- Update `.neuroflow/write-report/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
