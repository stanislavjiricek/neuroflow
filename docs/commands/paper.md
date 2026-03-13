---
title: /paper
---

# `/neuroflow:paper`

**Draft and internally review every section of your manuscript — nothing is saved without critic approval.**

`/paper` is the unified manuscript command. It replaces two separate steps (draft, then review) with a single brutal loop: the `paper-writer` agent drafts each section, the `paper-critic` agent applies the full six-area peer-review methodology, and the loop iterates up to 3 times per section. Only approved sections reach disk.

---

## When to use it

- After `/data-analyze` — results and figures are ready
- You want to produce a manuscript that has been through rigorous internal review before it reaches a real journal
- You want drafting and critique in one integrated workflow with automatic critic approval gates

---

## What it does

Claude reads your project memory and asks:

1. **Target journal?**
2. **Format?** LaTeX or Markdown/Word
3. **Which section(s)?** — or full paper
4. **Review focus?** — full six-area critique on every section, or specific areas

---

## The write→critique loop

Every section goes through this loop before it is saved:

```
paper-writer → draft v1
paper-critic → [STATUS: APPROVED] or [STATUS: REJECTED] + actionable feedback

if APPROVED → section saved to manuscript/
if REJECTED → paper-writer revises → draft v2
              paper-critic → verdict

if APPROVED → section saved
if REJECTED → paper-writer revises → draft v3
              paper-critic → verdict

if APPROVED → section saved
if REJECTED (3rd) → loop halts; unresolved critique logged to .neuroflow/paper/critic-log.md
                    user decides whether to accept the draft or stop
```

Maximum 3 iterations per section. Nothing is written to `manuscript/` without `[STATUS: APPROVED]` or explicit user acceptance.

---

## Critic standards

The `paper-critic` agent applies the full `neuroflow:review-neuro` six-area methodology to every draft:

| Area | What is checked |
|---|---|
| Language & Terminology | Spelling, grammar, neuroscience terminology errors, causality language |
| Internal Consistency | Figure/table references, value consistency across sections |
| Claim Support & Causality | Overclaims, causality creep, FC over-interpretation |
| Statistics | Effect sizes, multiple-comparison correction, null models, estimator specification |
| Methods Reproducibility | COBIDAS/ARRIVE compliance, artefact thresholds, data/code availability |
| Contribution & Novelty | Novelty claims, prior work comparison, journal fit |

A section is approved only if it would survive peer review at a top-tier neuroscience journal. The bar is not "acceptable draft" — it is "ready for submission".

---

## Drafting order

For a full paper, sections are drafted in this order:

| Order | Section | Source material |
|---|---|---|
| 1 | **Methods** | `.neuroflow/experiment/`, `.neuroflow/data-preprocess/`, `.neuroflow/data-analyze/` |
| 2 | **Results** | `.neuroflow/data-analyze/` (analysis outputs, figures) |
| 3 | **Introduction** | `.neuroflow/ideation/` (research question, literature) |
| 4 | **Discussion** | All prior sections plus interpretation |
| 5 | **Abstract** | Always last — summarises after all other sections are approved |

---

## Output

Approved sections are saved to `manuscript/` (or the path set in `.neuroflow/paper/flow.md`). Loop state is tracked in `.neuroflow/paper/critic-log.md`.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/ideation/flow.md`, `.neuroflow/data-analyze/flow.md`, `.neuroflow/paper/flow.md` |
| Writes | `.neuroflow/paper/`, `.neuroflow/paper/flow.md`, `.neuroflow/paper/critic-log.md`, `.neuroflow/sessions/YYYY-MM-DD.md`, `manuscript/` (approved drafts) |

---

## Related commands

- [`/data-analyze`](data-analyze.md) — generate the results that go into the paper
- [`/review`](review.md) — peer review a colleague's paper using the same six-area methodology
