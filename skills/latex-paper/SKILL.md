---
name: latex-paper
description: Use when writing, generating, or formatting a scientific neuroscience paper in LaTeX — document structure, sections (Abstract, Introduction, Methods, Results, Discussion), BibTeX references, figure inclusion, table formatting, equation writing, or converting manuscript to LaTeX format. Triggers on "write paper LaTeX", "generate LaTeX", "LaTeX article", "LaTeX neuroscience paper", "BibTeX", "LaTeX methods section", "LaTeX figure", "manuscript LaTeX", "compile PDF from LaTeX".
version: 1.0.0
---

# LaTeX Scientific Paper Generation

## Purpose

Generate and structure neuroscience manuscripts in LaTeX with correct section hierarchy, citation management, figure/table formatting, and journal-ready output.

## Article Template (Standard)

```latex
\documentclass[12pt, a4paper]{article}

% Packages
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath, amssymb}
\usepackage{graphicx}
\usepackage{booktabs}           % Professional tables
\usepackage{hyperref}
\usepackage[margin=2.5cm]{geometry}
\usepackage{lineno}             % Line numbers (review)
\usepackage{setspace}           % Double spacing (review)
\usepackage{natbib}             % APA citations
\usepackage{caption}
\usepackage{subcaption}         % Subfigures
\usepackage{siunitx}            % SI units (\SI{500}{\ms})
\usepackage{microtype}

% Bibliography style
\bibliographystyle{apalike}     % or: apa, plainnat, unsrt

\linenumbers
\doublespacing

\begin{document}

\title{Your Neuroscience Paper Title}
\author{First Author\textsuperscript{1}, Second Author\textsuperscript{2}\\
  \textsuperscript{1}Department, Institution, City, Country\\
  \textsuperscript{2}Department, Institution, City, Country}
\date{}
\maketitle

\begin{abstract}
Background: ...
Methods: ...
Results: ...
Conclusion: ...
\\[6pt]
\textbf{Keywords:} EEG, P300, oddball paradigm, permutation test
\end{abstract}

\section{Introduction}
...

\section{Methods}
\subsection{Participants}
\subsection{Experimental Paradigm}
\subsection{EEG Recording}
\subsection{Preprocessing}
\subsection{Analysis}
\subsection{Statistical Analysis}

\section{Results}
...

\section{Discussion}
...

\section{Conclusion}
...

\section*{Acknowledgements}
...

\section*{Funding}
...

\section*{Conflicts of Interest}
None declared.

\section*{Data Availability}
Data are available at \url{https://openneuro.org/...}

\bibliography{references}

\end{document}
```

---

## Figure Inclusion

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.8\textwidth]{figures/erp_grand_average.pdf}
  \caption{Grand-average ERP waveforms at Pz.
           Shaded regions indicate ±1 SEM across participants.
           The P300 component is marked between 300 and 600 ms.
           Significant time windows (cluster-based permutation test, $p < .05$)
           are indicated by horizontal bars.}
  \label{fig:erp_grand}
\end{figure}

% Reference in text: (see Figure~\ref{fig:erp_grand})
```

## Tables

```latex
\begin{table}[htbp]
  \centering
  \caption{Participant demographics and behavioral performance.}
  \label{tab:demographics}
  \begin{tabular}{lcc}
    \toprule
    & \textbf{Group A} & \textbf{Group B} \\
    \midrule
    N & 20 & 20 \\
    Age (years) & $24.3 \pm 3.2$ & $25.1 \pm 2.8$ \\
    Sex (M/F) & 10/10 & 11/9 \\
    Accuracy (\%) & $94.2 \pm 4.1$ & $92.8 \pm 5.3$ \\
    RT (ms) & $342 \pm 48$ & $361 \pm 52$ \\
    \bottomrule
  \end{tabular}
\end{table}
```

---

## Statistics Reporting

```latex
% t-test
$t(38) = 3.42$, $p = .001$, $d = 0.76$

% ANOVA
$F(2, 57) = 8.34$, $p < .001$, $\eta^2_p = .23$

% Permutation test
Cluster-based permutation test: $p_{\text{cluster}} = .018$,
cluster range: 320--580\,ms

% Correlation
$r(38) = .64$, $p < .001$, 95\% CI [.42, .80]

% Effect sizes (always report)
Cohen's $d = 0.82$ (large), $\eta^2_p = .15$ (medium)
```

---

## BibTeX Management

```bibtex
@article{Smith2024,
  author  = {Smith, J. and Doe, A.},
  title   = {N200 reflects conflict monitoring in auditory oddball},
  journal = {NeuroImage},
  year    = {2024},
  volume  = {281},
  pages   = {120--135},
  doi     = {10.1016/j.neuroimage.2024.120135},
}
```

Citation in text:
```latex
\citep{Smith2024}   % (Smith & Doe, 2024)
\citet{Smith2024}   % Smith & Doe (2024)
\citealt{Smith2024} % Smith & Doe, 2024 (no parentheses)
```

---

## Methods Section Template

```latex
\subsection{EEG Recording and Preprocessing}
Continuous EEG was recorded at \SI{1000}{\Hz} using a 64-channel
BrainProducts actiCHamp system (BrainProducts GmbH, Munich, Germany).
Electrodes were placed according to the 10–10 system, referenced online
to the nose tip. Impedances were kept below \SI{10}{\kohm}.

Data were preprocessed using MNE-Python \citep{Gramfort2013} (v1.7).
A \SI{1}{\Hz} high-pass filter was applied, followed by a
\SI{50}{\Hz} notch filter. Independent component analysis (ICA;
FastICA, 20 components) was used to remove ocular and cardiac
artifacts. Epochs were extracted from \SI{-200}{\ms} to \SI{800}{\ms}
relative to stimulus onset, baseline-corrected using the
\SI{-200}{\ms} to \SI{0}{\ms} pre-stimulus interval, and rejected if
peak-to-peak amplitude exceeded \SI{100}{\μV}. On average,
$91.3 \pm 6.2$\% of trials were retained.
```

---

## Compilation

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex   # Run twice for cross-references
```

Or with latexmk:
```bash
latexmk -pdf main.tex
```
