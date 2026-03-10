---
title: /paper-write
---

# `/neuroflow:paper-write`

**Generate a full manuscript draft from your analysis results and figures.**

`/paper-write` produces a complete manuscript draft, pulling context from your project memory — research question from ideation, methods from experiment and preprocessing, results from analysis — so you don't have to re-explain everything from scratch.

---

## When to use it

- After `/data-analyze` — you have results and figures
- You want to draft individual sections (Introduction, Methods, Results)
- You need a full paper from scratch

---

## What it does

Claude reads your project memory and asks:

1. **Target journal?**
2. **Format?** LaTeX or Word/Markdown
3. **Are figures ready** or do they still need to be generated?
4. **Which sections first,** or should it draft the full paper?

---

## Sections

Claude writes sections in this order for a full paper:

| Section | Source material |
|---|---|
| **Title + authors** | You provide this |
| **Abstract** | Written last — summarizes after other sections are done |
| **Introduction** | Background, gap, research question, hypothesis from `.neuroflow/ideation/` |
| **Methods** | Participants, recording setup, paradigm, preprocessing, analysis from `.neuroflow/experiment/`, `.neuroflow/data/`, `.neuroflow/data-preprocess/`, `.neuroflow/data-analyze/` |
| **Results** | Findings without interpretation; references to figures |
| **Discussion** | Interpretation, prior work comparison, limitations, future directions |
| **References** | Pulled from `.neuroflow/ideation/` (literature from scholar agent) |

---

## Format support

=== "Markdown"

    Default output — clean Markdown that converts easily to any format.

    ```markdown
    # Does Background Noise Modulate P300 Amplitude?

    ## Abstract
    ...

    ## Introduction
    Selective auditory attention is a fundamental cognitive process...
    ```

=== "LaTeX"

    For journal submission, Claude generates a LaTeX document using the standard `article` class or a journal-specific template.

    ```latex
    \documentclass{article}
    \usepackage{graphicx, amsmath, hyperref}

    \title{Does Background Noise Modulate P300 Amplitude?}
    \author{First Author \and Second Author}

    \begin{document}
    \maketitle

    \begin{abstract}
    ...
    \end{abstract}
    ```

---

## Example session

```
/neuroflow:paper-write
```

```
Claude: I have the following context:
        - Research question: "Does noise reduce P300 amplitude?"
        - Methods: 64-ch EEG, oddball paradigm, MNE preprocessing
        - Results: Significant cluster at 350-520ms, Cohen's d = 0.71
        - Figures: figures/erp_comparison.png ready

        Target journal?

You: PLOS ONE

Claude: PLOS ONE style (APA references, 250-word abstract limit).
        Starting with Methods section (I have the most context there)...

        [drafts Methods section using preprocessing config and analysis plan]

        Methods done. Moving to Results...

        [drafts Results with figure references]

        Ready to draft Introduction and Discussion?
```

---

## Output

The draft is saved as `manuscript-[date].md` (or `.tex`) in your `manuscript/` folder (or the path detected by `/start`).

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/ideation/flow.md`, `.neuroflow/data-analyze/flow.md`, `.neuroflow/paper-write/flow.md` |
| Writes | `.neuroflow/paper-write/`, `.neuroflow/paper-write/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md`, `manuscript/` (draft output) |

---

## Related commands

- [`/data-analyze`](data-analyze.md) — generate the results that go into the paper
- [`/paper-review`](paper-review.md) — pre-submission peer review of the draft
