---
title: /write-report
---

# `/neuroflow:write-report`

**Generate a structured report from `.neuroflow/` contents.**

`/write-report` produces a formatted report from your project memory — useful for progress updates, lab meeting summaries, supervision reports, or internal documentation. It can cover a single phase, multiple phases, or the whole project.

---

## When to use it

- Before a supervisory meeting or lab meeting
- For a funder progress report
- For internal project documentation
- To get a bird's-eye view of what's been done across all phases

---

## What it does

Claude asks:

1. **Which phases to cover?** (one phase, a selection, or the whole project)
2. **Recent changes only, or full overview?**
3. **Audience and format?** (supervisor, lab meeting, internal, funder)

Then Claude loads the relevant `flow.md` files and session logs, reads key documents (analysis summary, preprocessing report, etc.), and writes a structured report.

---

## Report structure

```
# Project Report — OddballStudy2026
Date: 2026-03-09
Phases: data-preprocess, data-analyze

## Data preprocessing

**What was done:**
- Standard EEG pipeline applied to 24 subjects
- 0.5–45 Hz bandpass, average reference, ICA (ocular artifacts removed)
- Epochs: -200 to 800ms around stimulus onset

**Key outputs:**
- Preprocessing script: scripts/preprocessing/preprocess.py
- QC report: .neuroflow/data-preprocess/preprocess-report.md

**Notes:**
- Subject 12: unusually high rejection rate (35%) — bridging electrode suspected
- Subjects 01–24: mean rejection rate 8.3%

## Data analysis

**What was done:**
- P300 ERP comparison: noise vs. silent condition
- Cluster permutation test, 300–600ms, central-parietal ROI

**Key findings:**
- Significant cluster at 350–520ms (p = 0.012)
- P300 amplitude reduced by 2.3 µV in noise condition (Cohen's d = 0.71)

**Open questions:**
- Time-frequency analysis still pending

## Overall status

Current phase: data-analyze
Next step: Complete time-frequency analysis, then /paper
```

---

## Output

The report is saved as `report-[date].md` in `.neuroflow/write-report/`.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/sessions/`, `.neuroflow/{phase}/flow.md` (for each covered phase) |
| Writes | `.neuroflow/write-report/`, `.neuroflow/write-report/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md` |

---

## Related commands

- [`/notes`](notes.md) — capture rough notes from a meeting
- [`/sentinel`](sentinel.md) — audit project consistency before writing a report
- [`/phase`](phase.md) — check the current phase status
