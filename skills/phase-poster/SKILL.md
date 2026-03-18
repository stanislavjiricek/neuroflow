---
name: phase-poster
description: Phase guidance for the neuroflow /poster command. LaTeX academic conference poster generation — template selection (A0/A1/A2, portrait/landscape, custom conference sizes), QR code integration, content extraction from project memory, and iterative poster-critic review loop.
---

# phase-poster

The poster phase generates a publication-ready academic conference poster as a LaTeX `.tex` file, compiled to PDF. Content is extracted from `.neuroflow/` project memory. The poster goes through an iterative critic loop (up to 3 cycles) before final output.

---

## Approach

1. Confirm conference name, target size, orientation, and QR code URL with the user before loading any files
2. Read `.neuroflow/project_config.md` and relevant phase `flow.md` files to extract title, authors, affiliations, key findings, methods, and figures
3. Select the appropriate LaTeX template (see below)
4. Generate the full `.tex` source with a QR code block if a URL is provided
5. Run the poster through the `poster-critic` agent for iterative review (worker-critic loop, max 3 cycles)
6. Save approved `.tex` and compiled PDF instructions to `.neuroflow/poster/`

---

## Template catalogue

### Template A — A0 Portrait (841 × 1189 mm) — Standard conference

```latex
% ── neuroflow poster template: A0 portrait ───────────────────────────────
\documentclass[25pt, a0paper, portrait, blockverticalspace=15mm]{tikzposter}

\usepackage[utf8]{inputenc}
\usepackage{amsmath, amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{multicol}
\usepackage{qrcode}          % QR code package
\usepackage{hyperref}

% ── Colour theme ─────────────────────────────────────────────────────────
\definecolor{nfBlue}{RGB}{30, 90, 160}
\definecolor{nfLightBlue}{RGB}{210, 230, 255}
\definecolor{nfAccent}{RGB}{220, 80, 30}

\definetitlestyle{nfTitle}{
  width=\textwidth, roundedcorners=10, linewidth=2pt,
  innersep=10pt, titletotopverticalspace=0pt,
  titletoblockverticalspace=20mm
}{
  \begin{scope}[line width=\titlelinewidth, rounded corners=\titleroundedcorners]
    \fill[color=nfBlue] (\titleposleft,\titleposbottom) rectangle (\titleposright,\titlepostop);
  \end{scope}
}

\definelayouttheme{nfTheme}{
  titlestyle=nfTitle, headerheight=0.12\textheight,
  blockstyle=Slide, backgroundstyle=Empty
}
\usetheme{nfTheme}
\colorlet{titlebgcolor}{nfBlue}
\colorlet{titlefgcolor}{white}
\colorlet{blocktitlebgcolor}{nfBlue}
\colorlet{blocktitlefgcolor}{white}
\colorlet{blockbodybgcolor}{nfLightBlue}

% ── Title block ───────────────────────────────────────────────────────────
\title{\textbf{POSTER TITLE HERE}}
\author{Author One\textsuperscript{1}, Author Two\textsuperscript{2}, Author Three\textsuperscript{1}}
\institute{\textsuperscript{1}Institution One, City, Country \quad
           \textsuperscript{2}Institution Two, City, Country}
\date{Conference Name, Month Year}

\begin{document}
\maketitle

% ── Three-column layout ───────────────────────────────────────────────────
\begin{columns}

  % ── Column 1 ─────────────────────────────────────────────────────────
  \column{0.33}

  \block{Introduction}{
    Provide the scientific background and motivation.
    State the gap your study addresses.
    Keep to 3–4 short paragraphs.
  }

  \block{Objectives}{
    \begin{itemize}
      \item Primary aim of the study
      \item Secondary aim / hypothesis 1
      \item Hypothesis 2 (if applicable)
    \end{itemize}
  }

  \block{Methods}{
    \textbf{Participants:} N = X (age range, mean ± SD; X female).\\[0.5em]
    \textbf{Design:} Brief paradigm description.\\[0.5em]
    \textbf{Recording:} Modality, equipment, sampling rate.\\[0.5em]
    \textbf{Analysis:} Key analysis steps and statistical approach.

    \begin{center}
      \includegraphics[width=0.9\linewidth]{figures/paradigm.pdf}
      \par\small Figure 1. Experimental paradigm.
    \end{center}
  }

  % ── Column 2 ─────────────────────────────────────────────────────────
  \column{0.34}

  \block{Results}{
    \textbf{Finding 1:} One-sentence statement of the result.\\[0.5em]
    \begin{center}
      \includegraphics[width=0.9\linewidth]{figures/result1.pdf}
      \par\small Figure 2. Key result with caption.
    \end{center}

    \vspace{0.5em}
    \textbf{Finding 2:} One-sentence statement of the result.
    \begin{center}
      \includegraphics[width=0.9\linewidth]{figures/result2.pdf}
      \par\small Figure 3. Secondary result with caption.
    \end{center}
  }

  % ── Column 3 ─────────────────────────────────────────────────────────
  \column{0.33}

  \block{Discussion}{
    Interpret the key findings.
    Link back to the objectives.
    Address limitations (one paragraph).
  }

  \block{Conclusions}{
    \begin{itemize}
      \item \textbf{Main takeaway} — one sentence
      \item \textbf{Implication} — one sentence
      \item \textbf{Future direction} — one sentence
    \end{itemize}
  }

  \block{References}{
    \small
    \begin{enumerate}
      \item[{[1]}] Author et al. (Year). Title. \textit{Journal}, \textbf{Vol}, pages.
      \item[{[2]}] Author et al. (Year). Title. \textit{Journal}, \textbf{Vol}, pages.
    \end{enumerate}
  }

  \block{}{
    \begin{minipage}[t]{0.65\linewidth}
      \textbf{Acknowledgements:} Funding bodies, ethics committees, participants.\\[0.5em]
      \textbf{Contact:} \texttt{corresponding.author@institution.edu}
    \end{minipage}%
    \hfill
    \begin{minipage}[t]{0.30\linewidth}
      \centering
      % ── QR code block ─────────────────────────────────────────────────
      \qrcode[height=4cm]{https://doi.org/10.XXXX/XXXXX}\\[0.3em]
      \small Scan for preprint / data
    \end{minipage}
  }

\end{columns}
\end{document}
```

---

### Template B — A0 Landscape (1189 × 841 mm) — Four-column wide format

```latex
% ── neuroflow poster template: A0 landscape ──────────────────────────────
\documentclass[25pt, a0paper, landscape, blockverticalspace=15mm]{tikzposter}

\usepackage[utf8]{inputenc}
\usepackage{amsmath, amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{qrcode}
\usepackage{hyperref}

\definecolor{nfBlue}{RGB}{30, 90, 160}
\definecolor{nfLightBlue}{RGB}{210, 230, 255}

\colorlet{titlebgcolor}{nfBlue}
\colorlet{titlefgcolor}{white}
\colorlet{blocktitlebgcolor}{nfBlue}
\colorlet{blocktitlefgcolor}{white}
\colorlet{blockbodybgcolor}{nfLightBlue}
\usetheme{Slide}

\title{\textbf{POSTER TITLE HERE}}
\author{Author One\textsuperscript{1}, Author Two\textsuperscript{2}}
\institute{\textsuperscript{1}Institution One \quad \textsuperscript{2}Institution Two}
\date{Conference Name, Month Year}

\begin{document}
\maketitle

\begin{columns}
  \column{0.25}
  \block{Introduction}{ Background and gap. }
  \block{Objectives}{ \begin{itemize}\item Aim 1 \item Aim 2 \end{itemize} }

  \column{0.25}
  \block{Methods}{
    \textbf{Participants:} N = X.\\
    \textbf{Design:} Paradigm.\\
    \textbf{Analysis:} Pipeline.
    \begin{center}\includegraphics[width=0.85\linewidth]{figures/paradigm.pdf}\end{center}
  }

  \column{0.25}
  \block{Results}{
    \textbf{Key finding.}
    \begin{center}\includegraphics[width=0.85\linewidth]{figures/result1.pdf}\end{center}
    \begin{center}\includegraphics[width=0.85\linewidth]{figures/result2.pdf}\end{center}
  }

  \column{0.25}
  \block{Discussion \& Conclusions}{
    Interpretation and implications.
    \begin{itemize}
      \item Takeaway 1
      \item Takeaway 2
      \item Future work
    \end{itemize}
  }
  \block{}{
    \begin{minipage}[t]{0.6\linewidth}
      \small \textbf{Contact:} \texttt{email@institution.edu}\\
      \textbf{Funding:} Grant agency, grant number.
    \end{minipage}\hfill
    \begin{minipage}[t]{0.35\linewidth}
      \centering
      \qrcode[height=3.5cm]{https://doi.org/10.XXXX/XXXXX}\\
      \small Preprint / data
    \end{minipage}
  }
\end{columns}
\end{document}
```

---

### Template C — A1 Portrait (594 × 841 mm) — Smaller venue / seminar

```latex
% ── neuroflow poster template: A1 portrait ───────────────────────────────
\documentclass[20pt, a1paper, portrait, blockverticalspace=10mm]{tikzposter}

\usepackage[utf8]{inputenc}
\usepackage{amsmath, amssymb}
\usepackage{graphicx}
\usepackage{qrcode}
\usepackage{hyperref}

\definecolor{nfBlue}{RGB}{30, 90, 160}
\definecolor{nfLightBlue}{RGB}{210, 230, 255}
\colorlet{titlebgcolor}{nfBlue}
\colorlet{titlefgcolor}{white}
\colorlet{blocktitlebgcolor}{nfBlue}
\colorlet{blocktitlefgcolor}{white}
\colorlet{blockbodybgcolor}{nfLightBlue}
\usetheme{Slide}

\title{\textbf{POSTER TITLE}}
\author{Author One, Author Two}
\institute{Institution, City, Country}
\date{Conference Name, Month Year}

\begin{document}
\maketitle

\begin{columns}
  \column{0.5}
  \block{Introduction}{ Background. Gap. }
  \block{Methods}{ Participants, design, analysis. }
  \block{Objectives}{ \begin{itemize}\item Aim 1 \item Aim 2\end{itemize} }

  \column{0.5}
  \block{Results}{
    \begin{center}\includegraphics[width=0.9\linewidth]{figures/result1.pdf}\end{center}
  }
  \block{Conclusions}{
    \begin{itemize}\item Main finding \item Implication\end{itemize}
  }
  \block{}{
    \centering
    \qrcode[height=3cm]{https://doi.org/10.XXXX/XXXXX}\\
    \small \textbf{Contact:} \texttt{email@inst.edu}
  }
\end{columns}
\end{document}
```

---

### Template D — Custom conference size (90 × 120 cm) — Portrait

```latex
% ── neuroflow poster template: 90×120 cm portrait ────────────────────────
\documentclass[25pt, blockverticalspace=15mm]{tikzposter}

\usepackage[utf8]{inputenc}
\usepackage{amsmath, amssymb}
\usepackage{graphicx}
\usepackage{qrcode}
\usepackage{geometry}
\geometry{paperwidth=90cm, paperheight=120cm, margin=2cm}

\definecolor{nfBlue}{RGB}{30, 90, 160}
\definecolor{nfLightBlue}{RGB}{210, 230, 255}
\colorlet{titlebgcolor}{nfBlue}
\colorlet{titlefgcolor}{white}
\colorlet{blocktitlebgcolor}{nfBlue}
\colorlet{blocktitlefgcolor}{white}
\colorlet{blockbodybgcolor}{nfLightBlue}
\usetheme{Slide}

\title{\textbf{POSTER TITLE}}
\author{Authors}
\institute{Affiliations}
\date{Conference, Date}

\begin{document}
\maketitle
\begin{columns}
  \column{0.33}
  \block{Introduction}{ Background. Gap. Motivation. }
  \block{Methods}{ Participants, design, recording, analysis. }

  \column{0.34}
  \block{Results}{
    \begin{center}\includegraphics[width=0.9\linewidth]{figures/result1.pdf}\end{center}
    \begin{center}\includegraphics[width=0.9\linewidth]{figures/result2.pdf}\end{center}
  }

  \column{0.33}
  \block{Discussion}{ Interpretation. Limitations. }
  \block{Conclusions}{
    \begin{itemize}\item Takeaway 1 \item Takeaway 2\end{itemize}
  }
  \block{}{
    \begin{minipage}[t]{0.6\linewidth}
      \small References and acknowledgements.
    \end{minipage}\hfill
    \begin{minipage}[t]{0.35\linewidth}
      \centering
      \qrcode[height=4cm]{https://doi.org/10.XXXX/XXXXX}\\
      \small Scan for more
    \end{minipage}
  }
\end{columns}
\end{document}
```

---

### Template E — 48 × 36 inches Landscape (US conference format)

```latex
% ── neuroflow poster template: 48×36 in landscape (US) ───────────────────
\documentclass[25pt, blockverticalspace=15mm]{tikzposter}

\usepackage[utf8]{inputenc}
\usepackage{amsmath, amssymb}
\usepackage{graphicx}
\usepackage{qrcode}
\usepackage{geometry}
\geometry{paperwidth=48in, paperheight=36in, margin=1.5in}

\definecolor{nfBlue}{RGB}{30, 90, 160}
\definecolor{nfLightBlue}{RGB}{210, 230, 255}
\colorlet{titlebgcolor}{nfBlue}
\colorlet{titlefgcolor}{white}
\colorlet{blocktitlebgcolor}{nfBlue}
\colorlet{blocktitlefgcolor}{white}
\colorlet{blockbodybgcolor}{nfLightBlue}
\usetheme{Slide}

\title{\textbf{POSTER TITLE}}
\author{Authors}
\institute{Affiliations}
\date{Conference, Date}

\begin{document}
\maketitle
\begin{columns}
  \column{0.25}
  \block{Introduction}{ Background. Gap. }
  \block{Objectives}{ \begin{itemize}\item Aim 1 \item Aim 2\end{itemize} }

  \column{0.25}
  \block{Methods}{ Participants, design, analysis pipeline. }

  \column{0.25}
  \block{Results}{
    \begin{center}\includegraphics[width=0.9\linewidth]{figures/result1.pdf}\end{center}
    \begin{center}\includegraphics[width=0.9\linewidth]{figures/result2.pdf}\end{center}
  }

  \column{0.25}
  \block{Conclusions}{ Main takeaways. }
  \block{}{
    \centering
    \qrcode[height=5cm]{https://doi.org/10.XXXX/XXXXX}\\[0.3em]
    \small Scan for paper / data\\
    \texttt{email@institution.edu}
  }
\end{columns}
\end{document}
```

---

## Template selection guide

| Size | Orientation | Use when |
|---|---|---|
| A0 (841×1189 mm) | Portrait | Most European conferences; SfN, Bernstein, OHBM |
| A0 (1189×841 mm) | Landscape | Wide-format boards; when you have many side-by-side figures |
| A1 (594×841 mm) | Portrait | Lab retreats, seminars, smaller venues |
| 90×120 cm | Portrait | Common European conference custom size |
| 48×36 in | Landscape | US conferences (NeurIPS, COSYNE, SfN US booths) |

When the user does not specify a size, ask. Default to A0 Portrait if they are unsure.

---

## QR code integration

The `qrcode` LaTeX package is used for QR code generation. Install via TeX Live / MiKTeX:

```
tlmgr install qrcode
```

Usage in templates:

```latex
\qrcode[height=4cm]{https://your-url-here.com}
```

Recommended QR code targets:
- OSF preregistration URL
- bioRxiv preprint DOI (`https://doi.org/10.1101/XXXX.XX.XX.XXXXXXXX`)
- GitHub repository URL
- Personal lab page

If the user has not provided a URL, ask. If they want to skip the QR code, remove the `\qrcode` block from the footer.

---

## Compilation

Compile with `pdflatex` (recommended for tikzposter):

```bash
pdflatex poster.tex
```

Or with `latexmk` for automatic dependency resolution:

```bash
latexmk -pdf poster.tex
```

**Dependencies:** `tikzposter`, `qrcode`, `graphicx`, `booktabs`, `amsmath`. All available in TeX Live ≥ 2020 and MiKTeX.

**Figure formats:** Use `.pdf` or `.eps` for vector figures, `.png`/`.jpg` for bitmaps. Avoid `.svg` directly (convert to `.pdf` first via Inkscape: `inkscape figure.svg --export-pdf=figure.pdf`).

---

## Content extraction from `.neuroflow/`

When populating poster fields, read in this order:

1. `.neuroflow/project_config.md` — project title, PI, affiliation, modality, target journal
2. `.neuroflow/ideation/` — research question, hypotheses, key references
3. `.neuroflow/data-analyze/` or latest analysis `flow.md` — key results, effect sizes, figure paths
4. `.neuroflow/preregistration/` — objectives and analysis plan (if available)
5. `.neuroflow/paper/` — if a draft exists, extract the abstract and conclusions

If figures are referenced in flow.md files, list them for the user — do not attempt to embed binary image files; output their paths as `\includegraphics` stubs so the user can place the actual files.

---

## Output paths

Save poster files to `.neuroflow/poster/`:

```
.neuroflow/poster/
├── poster-YYYY-MM-DD.tex          ← LaTeX source
├── figures/                       ← symlinks or stubs for figures
└── critic-log.md                  ← iterative review log
```

If a same-date `.tex` file exists, append `-v2`, `-v3`, etc.

---

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules
- `neuroflow:stop-slop` — apply to all text blocks (Introduction, Methods, Results, Discussion, Conclusions) to eliminate AI writing patterns and filler phrases before saving the `.tex` file

## Slash command

`/neuroflow:poster` — runs this workflow as a slash command.
