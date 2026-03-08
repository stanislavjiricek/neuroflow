---
name: journal-styles
description: Use when formatting a neuroscience manuscript for a specific journal — word limits, section requirements, figure formatting, LaTeX class files, citation style, or author guidelines. Triggers on "format for NeuroImage", "journal requirements", "submission guidelines", "word limit", "author guidelines", "journal LaTeX template", "format for Nature Neuroscience", "Brain journal format", "JNeurosci format", "frontiers neuroscience format".
version: 1.0.0
---

# Journal-Specific Formatting Guide

## Purpose

Adapt manuscript formatting and LaTeX structure to meet specific journal requirements for top neuroscience journals.

---

## Journal Comparison Table

| Journal | IF | Format | Word limit | Refs | Open access |
|---|---|---|---|---|---|
| **Nature Neuroscience** | ~25 | Article/Letter | 3000 (Letter) / 5000 (Article) | 50 | Optional |
| **Neuron** | ~17 | Article | 5000–8000 | 80 | Optional |
| **eLife** | ~7 | Research Article | No limit | No limit | Yes (CC-BY) |
| **NeuroImage** | ~5 | Full paper | 8000–10000 | 80 | Optional |
| **Journal of Neuroscience** | ~5 | Articles | 15000 words | 100 | Optional |
| **Cerebral Cortex** | ~5 | Original Article | 6000 | 70 | Optional |
| **Brain** | ~14 | Original Article | 4500 (main) | 60 | Optional |
| **Human Brain Mapping** | ~4 | Research Article | 8000 | 80 | Yes |
| **Frontiers in Neuroscience** | ~3.5 | Original Research | 12000 | 100 | Yes |
| **PLOS ONE** | ~3 | Article | No limit | No limit | Yes |

---

## NeuroImage / Cerebral Cortex (Elsevier)

```latex
\documentclass[preprint,12pt]{elsarticle}
% Or use Word template from journal

% Sections: Abstract (250w), Introduction, Materials and Methods,
%           Results, Discussion, Conclusion (optional)
% Figures: TIFF/EPS, min 300 DPI print, 600 DPI line art
% References: numbered [1], [2] or author–year
% Word limit: NeuroImage ~8000 words text only

% Highlights (NeuroImage-specific): 3–5 bullet points (85 char each)
\begin{highlights}
\item EEG recorded during auditory oddball paradigm in 40 adults
\item N200 amplitude correlated with behavioral conflict monitoring
\item Cluster-based permutation tests confirmed at 200–250 ms at Fz
\end{highlights}
```

---

## Journal of Neuroscience (JNeurosci)

```latex
% Use JNeurosci Word/LaTeX template from journal website
% Structure: Abstract (250w), Significance Statement (120w),
%            Introduction (~400w), Materials and Methods,
%            Results, Discussion

% Significance Statement (mandatory):
\begin{quote}
\textbf{Significance Statement:}
This study demonstrates that [2–3 sentences, plain language,
no abbreviations, max 120 words, explain why neuroscientists
and general public should care].
\end{quote}

% Figures: EPS/PDF/TIFF, 600 DPI, ≤ 8.5 cm (single col) or 17 cm (double col)
% Citations: (Author et al., year) — APA style
```

---

## eLife

```latex
% LaTeX template: https://github.com/eLife-publishing/eLife-journals-template
\documentclass[9pt]{elife}

% Required: Abstract (<150w), Introduction, Results, Discussion,
%           Methods (at end), Data availability

% eLife specifics:
% - Methods section AFTER discussion (not in middle)
% - No conclusion section
% - Preprint strongly encouraged (bioRxiv)
% - Reviewer comments published alongside paper

% Citation: (Smith and Doe, 2024) — author-year
```

---

## Nature Neuroscience / Nature Methods

```latex
% No custom LaTeX class — use standard article
% Article: max 5000 words (intro+results+discussion), 6 display items
% Letter: max 3000 words, 4 display items

% Structure (Article):
% Abstract (150w, no references)
% [No section headers except Methods]
% Methods (after main text, not counted in word limit)
% References (numbered, [1])
% Extended Data Figures (up to 10, numbered ED Fig. 1-10)

% Figure formatting:
% Single column: 89 mm wide; Double column: 183 mm wide
% Min resolution: 300 DPI (half-tone), 1200 DPI (line art)
% Font size in figures: ≥ 7 pt

\bibliographystyle{naturemag}
```

---

## Brain (Oxford UP)

```latex
% Standard LaTeX, Oxford UP submission via ScholarOne
% Word limit: 4500 (main text) + Methods (no limit)
% Abstract: structured (Background, Methods, Results, Conclusion) ≤ 250w
% References: Vancouver style (numbered [1])

% Sections: Introduction, Materials and Methods, Results, Discussion
% Figures: EPS/TIFF, 600 DPI (greyscale), 300 DPI (color)
% Color figures: charged unless Open Access
```

---

## PLOS ONE / PLOS Biology

```latex
\documentclass[10pt]{article}
% Use PLOS LaTeX template

% No word limit; comprehensive Methods required
% Reporting standards: CONSORT (RCT), PRISMA (systematic review),
%                      ARRIVE (animal), STROBE (observational)
% Data sharing: mandatory
% Preregistration: encouraged

% Citation: (Smith and Doe 2024) — no comma before year
\bibliographystyle{plos2015}
```

---

## Figure Preparation Checklist

- [ ] Resolution ≥ 300 DPI (print), ≥ 600 DPI (line art)
- [ ] Font size ≥ 7 pt in all figure panels
- [ ] Color figures: RGB for online, CMYK for print if required
- [ ] Figure width matches journal column (single: ~85 mm, double: ~170 mm)
- [ ] All panels labeled (A, B, C…)
- [ ] Axes labeled with units in parentheses: Time (ms), Power (dB)
- [ ] Error bars defined in caption (±SEM, ±SD, or 95% CI)
- [ ] Color-blind friendly palette (avoid red/green combinations)

---

## Submission Checklist

- [ ] Word count within limit (excluding Methods/References if specified)
- [ ] Abstract within word limit
- [ ] Significance Statement / Impact Statement written (if required)
- [ ] All authors have ORCID IDs
- [ ] Preprint uploaded to bioRxiv (if required/recommended)
- [ ] Ethics statement included
- [ ] Data availability statement included
- [ ] Conflict of interest declared
- [ ] Supplementary materials prepared separately
