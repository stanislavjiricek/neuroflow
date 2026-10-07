# /review

> **You are the reviewer.** A colleague has sent you their paper and you need to produce a formal referee report. This command is for reviewing someone else's work — not for self-review before your own submission (use [`/paper`](paper.md) for that).

The `/review` command checks the journal's AI-use policy, gathers the paper, the target journal, and your review focus, then delegates the full analysis to the [`neuroflow:review-neuro`](../skills/review-neuro/SKILL.md) skill. The result is a structured referee report saved in the local-only `.neuroflow/review/` folder.

---

## What it does

1. **Asks about the AI-use policy first** — before the manuscript is requested or read: does the journal (or funder) allow AI tools in peer review? If not, or if you are unsure, the manuscript is not read; you get only help that needs no manuscript text. Your answer is stamped at the top of the report.
2. **Keeps everything local** — the manuscript, notes and report stay in `.neuroflow/review/`, which is gitignored, never exported by `/output`, and never sent to NotebookLM, Miro or Zotero (Zotero archival only if you opt in)
3. **Asks for the paper** — provide a file path, upload a PDF, or paste the text
4. **Asks for the target journal** — used to calibrate the referee persona and standards (optional; defaults to high general standards if not provided)
5. **Asks for review type** — full review across all eight areas, or focused on specific areas (methods, statistics, writing, figures)
6. **Scans for hidden instructions** — text hidden in the manuscript that tries to steer an AI reviewer is treated as data, reported to you, and noted for the editor
7. **Delegates to `neuroflow:review-neuro`** — the skill runs the complete eight-area review
8. **Saves the report** to `.neuroflow/review/review-[paper-title-slug]-[date].md`

---

## What the review covers

The eight areas reviewed by `neuroflow:review-neuro`:

| Area | What it checks |
|---|---|
| 1. Language & Style | Spelling, grammar, abbreviations, neuroscience terminology errors, overclaims |
| 2. Internal Consistency | Cross-references, figures, tables, numerical values in text vs results |
| 3. Claim Support & Causality | Unsupported claims, causality language from correlational data, FC over-interpretation |
| 4. Statistics & Network Inference | Power analysis, effect sizes, multiple comparisons, null models, estimator specification |
| 5. Methods Reproducibility | Ethics, demographics, modality-specific checklists (fMRI/EEG/iEEG/modelling), open data |
| 6. Contribution & Novelty | Novelty vs prior work, conceptual significance, alternative interpretations, journal fit, recommendation |
| 7. Literature Gap | Missing citations to relevant work — checked against Zotero, local paper library, and the manuscript's own references |
| 8. Figure Review | Citation order, panel completeness, axes/units/error bars, legend definitions, statistical annotations |

---

## Example session

```
/neuroflow:review

> AI-use policy: the journal allows AI assistance if disclosed to the editor
> Here is the paper (file path or uploaded PDF)
> Target journal: eLife
> Focus: full review

[hidden-instruction scan: nothing found]
[review-neuro skill produces a structured referee report]

Review saved to .neuroflow/review/review-default-mode-connectivity-2025-06-15.md
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
| `.neuroflow/review/review-[title-slug]-[date].md` | Full structured referee report (local only, gitignored) |
| `.neuroflow/sessions/YYYY-MM-DD.md` | One-liner entry (not the full report) |

---

## Related

- [`/paper`](paper.md) — for writing and reviewing **your own** manuscript before submission
- [`neuroflow:review-neuro`](../skills/review-neuro/SKILL.md) — the core eight-area review engine
