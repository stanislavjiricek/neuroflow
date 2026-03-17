---
title: /poster
---

# `/neuroflow:poster`

**Generate a LaTeX conference poster from project memory.**

`/poster` builds a publication-ready academic conference poster as a `.tex` file from your `.neuroflow/` project memory. Choose a template size, optionally add a QR code, and Claude will extract your title, authors, methods, key results, and conclusions — then run the draft through an iterative `poster-critic` review loop before saving.

---

## When to use it

- Before a conference (SfN, OHBM, Bernstein, COSYNE, NeurIPS…)
- For a lab retreat or departmental poster session
- When you want a print-ready poster tied directly to your project data

---

## What it does

Claude asks:

1. **Conference name** — used to infer the standard poster size if not specified
2. **Template size** — five options (see below)
3. **QR code URL** — preprint DOI, OSF page, GitHub repo, or skip
4. **Authors and affiliations** — confirmed or updated from `project_config.md`
5. **Which sections to include** — all five standard sections or a subset

Then Claude reads the relevant `.neuroflow/` phase files, populates the template, and submits the draft to the `poster-critic` agent for iterative review (up to 3 cycles).

---

## Template sizes

| Option | Size | Orientation | Typical use |
|---|---|---|---|
| A | A0 (841 × 1189 mm) | Portrait | Most European conferences; SfN, OHBM, Bernstein |
| B | A0 (1189 × 841 mm) | Landscape | Wide-format boards; side-by-side figures |
| C | A1 (594 × 841 mm) | Portrait | Lab retreats, seminars, smaller venues |
| D | 90 × 120 cm | Portrait | Common European conference custom size |
| E | 48 × 36 in | Landscape | US conferences (COSYNE, NeurIPS, SfN US booths) |

All templates use the `tikzposter` LaTeX class with a consistent blue colour theme and support the `qrcode` package for QR code generation.

---

## QR code

If you provide a URL, Claude inserts a `\qrcode{}` block in the poster footer. The `poster-critic` agent will flag a missing or placeholder QR URL if you requested one.

Recommended targets:

- bioRxiv preprint: `https://doi.org/10.1101/XXXX`
- OSF preregistration URL
- GitHub repository
- Lab or personal page

---

## Iterative critic review

The generated `.tex` source is reviewed by the `poster-critic` agent against a five-area rubric before the file is saved:

1. **Content accuracy** — title, authors, objectives, N, methods, results with numerical values, references
2. **Visual balance** — column proportions, section density, title prominence
3. **Scientific communication** — claims stated with statistics, figure captions, appropriate jargon level
4. **QR code** — present and non-placeholder (if requested)
5. **LaTeX correctness** — column fractions ≤ 1.0, required packages, no unclosed environments

The loop runs up to 3 iterations. Unresolved issues are logged to `.neuroflow/poster/critic-log.md`.

---

## Compilation

After saving, compile with:

```bash
cd .neuroflow/poster
pdflatex poster-YYYY-MM-DD.tex
```

Or with latexmk:

```bash
latexmk -pdf poster-YYYY-MM-DD.tex
```

**Required packages:** `tikzposter`, `qrcode`, `graphicx`, `booktabs`, `amsmath` — all in TeX Live ≥ 2020 and MiKTeX.

**Figures:** Replace each `\includegraphics{figures/...}` stub with the actual figure file. Use `.pdf` or `.eps` for vector graphics; `.png`/`.jpg` for bitmaps.

---

## Output

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/ideation/flow.md`, `.neuroflow/data-analyze/flow.md`, `.neuroflow/paper/flow.md`, `.neuroflow/preregistration/flow.md` |
| Writes | `.neuroflow/poster/poster-YYYY-MM-DD.tex`, `.neuroflow/poster/critic-log.md`, `.neuroflow/sessions/YYYY-MM-DD.md` |

If a same-date `.tex` file exists, a version suffix is added (`-v2`, `-v3`, etc.).

---

## Related commands

- [`/slideshow`](slideshow.md) — build a talk slide deck for the same conference
- [`/paper`](paper.md) — write up the results as a manuscript
- [`/write-report`](write-report.md) — generate a prose summary of the project
- [`/output`](output.md) — package the poster file for sharing or archiving
