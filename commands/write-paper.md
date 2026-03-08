---
description: Generate a scientific manuscript draft in LaTeX format from analysis results, figures, and study information. Produces a complete paper with all sections formatted for the target journal.
argument-hint: [target-journal]
allowed-tools: [Read, Write, Glob]
---

# /write-paper — Generate Scientific Manuscript

You are generating a complete scientific paper draft in LaTeX format.

**Target journal**: $ARGUMENTS

## Your Task

Produce a full LaTeX manuscript incorporating the study's methods, results, and discussion.

## Step 1: Gather Source Material

Read all available files in the project:
1. `hypotheses.md` — research question and hypotheses
2. `project_brief.md` — study design and recording info
3. `analysis/results/` — any CSV files with statistical results
4. `figures/` — available figure files
5. `config/team.json` — team, modality, journal target
6. Any `participants.tsv` for demographic info

If information is missing, ask the user to provide it.

## Step 2: Determine Journal Format

If target journal is specified in arguments or `team.json`, apply the correct format:
- **NeuroImage / Elsevier**: word limit ~8000, elsarticle class, numbered refs
- **JNeurosci**: Significance Statement required, APA citations
- **eLife**: Methods at end, author-year citations, no word limit
- **Nature family**: strict word limits, numbered refs, Extended Data
- **PLOS ONE**: no limit, open access, Vancouver

Otherwise: use standard article format.

## Step 3: Generate LaTeX Manuscript

Create `manuscript/main.tex` with:

### Abstract (250 words)
Write a structured abstract with:
- Background (1-2 sentences): what is known
- Objective (1 sentence): what this study examines
- Methods (2-3 sentences): key design, N, modality, analysis
- Results (2-3 sentences): main findings with key statistics
- Conclusion (1-2 sentences): implications

### Introduction
1. Open with the broad phenomenon (1 paragraph)
2. Review key prior findings (2-3 paragraphs citing literature)
3. Identify the gap this study addresses
4. State aims and hypotheses explicitly

### Methods
Use the `project_brief.md` and `config/team.json` to write:
- **Participants**: demographics, ethics, exclusion criteria
- **Experimental Paradigm**: detailed description
- **Recording**: system, sampling rate, reference, impedance
- **Preprocessing**: all steps with exact parameters
- **Analysis**: feature extraction, statistical tests

### Results
For each hypothesis:
1. State the test performed
2. Report result with full statistics: t(df) = X, p = .XXX, d = X.XX
3. Include figure reference: (see Figure 1)
4. One sentence interpretation

### Discussion
1. Summary paragraph (main findings vs. hypotheses)
2. One paragraph per major finding: contextualize with prior work
3. Unexpected results / null results addressed
4. Limitations
5. Future directions
6. Conclusion

### Generate Also:
- `manuscript/references.bib` — BibTeX file (placeholder entries with DOIs to fill in)
- `manuscript/Makefile` — for easy PDF compilation
- `manuscript/figures/` — directory for figure files

## Step 4: Report

List all files created. Provide compilation instructions:
```bash
cd manuscript && make
# or: pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

Suggest: `/review-paper` for quality check before submission.
