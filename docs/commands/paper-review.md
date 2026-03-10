---
title: /paper-review
---

# `/neuroflow:paper-review`

**Pre-submission peer review of a neuroscience manuscript.**

`/paper-review` performs a rigorous pre-submission review of your manuscript — scientific logic, methods, statistics, writing quality, and figures — before you submit to a journal. It delegates the review to the `neuroflow:review-neuro` skill, which is specifically designed for neuroscience manuscript evaluation.

---

## When to use it

- Before journal submission — catch problems early
- After `/paper-write` — review the draft you just generated
- When you want an independent check on a manuscript from any source

---

## What it does

Claude gathers the inputs, then hands off entirely to the `review-neuro` skill, which performs a structured neuroscience peer review.

Claude asks:

1. **Where is the manuscript?** (file path, paste content, or URL)
2. **What is the target journal?**
3. **Specific concern to focus on, or a full review?**

---

## What the review covers

The `review-neuro` skill performs a comprehensive evaluation:

| Area | What is checked |
|---|---|
| **Scientific logic** | Hypothesis clearly stated, supported by results, conclusions match data |
| **Methods** | Sample size, experimental design, controls, reproducibility |
| **Statistics** | Test selection, assumptions met, multiple comparisons, effect sizes |
| **Writing** | Clarity, structure, abstract, figure captions |
| **Figures** | Readability, appropriate plot types, error bars, color accessibility |
| **References** | Key citations present, appropriate citing style |

---

## Example session

```
/neuroflow:paper-review
```

```
Claude: Where is the manuscript?

You: manuscript/draft-2026-03-09.md

Claude: Target journal?

You: PLOS ONE

Claude: Full review or specific concern?

You: Full review, but particularly concerned about the statistics.

Claude: [delegates to review-neuro skill]

        --- REVIEW ---

        MAJOR ISSUES

        1. Statistics (Methods, p.4): The permutation cluster test is appropriate
           for the ERP comparison, but the correction for multiple comparisons in
           the time-frequency analysis (Table 2) uses uncorrected p-values.
           FDR or cluster correction should be applied.

        2. Effect size (Results, p.6): Cohen's d is reported for the main effect
           but missing for the supplementary analyses. All pairwise comparisons
           need effect sizes.

        MINOR ISSUES

        3. Abstract (p.1): The abstract reports p = 0.012 but the main text
           reports the cluster p-value differently. Verify consistency.

        4. Figure 2: The color scale for the TFR plot is not colorblind-safe.
           Suggest replacing jet colormap with RdBu_r.

        Overall: Solid study with clear hypothesis and appropriate methods.
        Address statistics and effect size reporting before submission.
```

---

## Output

The review is saved as `review-[date].md` in `.neuroflow/paper-review/`.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/paper-write/flow.md`, `.neuroflow/paper-review/flow.md` |
| Writes | `.neuroflow/paper-review/`, `.neuroflow/paper-review/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md` |

---

## Related commands

- [`/paper-write`](paper-write.md) — generate the manuscript before reviewing it
- [`/data-analyze`](data-analyze.md) — verify statistical approach before writing
