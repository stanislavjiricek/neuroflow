# /review

> **You are the reviewer.** A colleague has sent you their paper and you need to produce a formal referee report. This command is for reviewing someone else's work — not for self-review before your own submission (use [`/paper`](paper.md) for that).

The `/review` command gathers the paper, the target journal, and your review focus, then delegates the full analysis to the [`neuroflow:review-neuro`](../skills/review-neuro/SKILL.md) skill. The result is a structured referee report saved to your `reviews/` folder.

---

## What it does

1. **Asks for the paper** — paste the text, upload a PDF, or provide a file path
2. **Asks for the target journal** — used to calibrate the referee persona and standards (optional; defaults to high general standards if not provided)
3. **Asks for review type** — full review across all six areas, or focused on specific areas (methods, statistics, writing, figures)
4. **Delegates to `neuroflow:review-neuro`** — the skill runs the complete six-area review
5. **Saves the report** to `reviews/review-[paper-title-slug]-[date].md` in your project folder

---

## What the review covers

The six areas reviewed by `neuroflow:review-neuro`:

| Area | What it checks |
|---|---|
| 1. Language & Style | Spelling, grammar, abbreviations, neuroscience terminology errors, overclaims |
| 2. Internal Consistency | Cross-references, figures, tables, numerical values in text vs results |
| 3. Claim Support & Causality | Unsupported claims, causality language from correlational data, FC over-interpretation |
| 4. Statistics & Network Inference | Power analysis, effect sizes, multiple comparisons, null models, estimator specification |
| 5. Methods Reproducibility | Ethics, demographics, modality-specific checklists (fMRI/EEG/iEEG/modelling), open data |
| 6. Contribution & Novelty | Novelty vs prior work, conceptual significance, alternative interpretations, journal fit, recommendation |

---

## Example session

```
/neuroflow:review

> Here is the paper (pasted text or uploaded PDF)
> Target journal: eLife
> Focus: full review

[review-neuro skill produces a structured referee report]

Review saved to reviews/review-default-mode-connectivity-2025-06-15.md
```

---

## Files read

| File | Purpose |
|---|---|
| `.neuroflow/project_config.md` | Active phase and project context |
| `.neuroflow/flow.md` | Project memory index |
| `skills/phase-review/SKILL.md` | Phase orientation for the reviewer role |

## Files written

| File | Contents |
|---|---|
| `reviews/review-[title-slug]-[date].md` | Full structured referee report |
| `.neuroflow/sessions/YYYY-MM-DD.md` | One-liner entry (not the full report) |

---

## Related

- [`/paper`](paper.md) — for writing and reviewing **your own** manuscript before submission
- [`neuroflow:review-neuro`](../skills/review-neuro/SKILL.md) — the core six-area review engine
