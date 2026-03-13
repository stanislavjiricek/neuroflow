---
name: review
description: Peer review a colleague's neuroscience paper — structured referee report with major/minor issues, calibrated to the target journal.
phase: review
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - skills/phase-review/SKILL.md
writes:
  - reviews/
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /review

Read the `neuroflow:phase-review` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` and `flow.md` before starting.

> **This command is for when YOU are the reviewer** — a colleague has sent you their paper and you need to produce a formal referee report. This is not for reviewing your own manuscript before submission (use `/neuroflow:paper` for that).

## What this command does

Gather the inputs below, then invoke the `neuroflow:review-neuro` skill to run the full six-area review. Do not perform the review yourself — delegate entirely to the skill.

Ask:
1. **Paper** — paste the full text, upload the PDF, or provide a file path.
2. **Target journal** — which journal is it being submitted to? (If unknown, apply high general standards.)
3. **Review type** — full review across all six areas, or focus on specific areas (methods, statistics, writing, figures)?

Once you have the answers, pass them to the `neuroflow:review-neuro` skill and let it drive the review procedure from start to finish.

---

## At end

- Save the review report as `review-[paper-title-slug]-[date].md` in the `reviews/` folder in the project directory (not inside `.neuroflow/`)
- Create `reviews/` if it does not exist
- Append a **single one-liner** to `.neuroflow/sessions/YYYY-MM-DD.md`, e.g.:
  `- [review] Referee report for "[Paper title]" ([Journal]) saved to reviews/review-[title-slug]-[date].md`
- Do not paste the review content into the session log
- Confirm the save path with the user before writing
