---
name: lit-review
description: Run a structured literature review on a set of retrieved papers — synthesise findings, map contradictions, identify knowledge gaps, audit methodology, and draft a lit review section — using the 12 lit-review-protocols.
phase: ideation
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/fails/core.md
  - .neuroflow/fails/science.md
  - .neuroflow/fails/ux.md
  - .neuroflow/ideation/flow.md
writes:
  - .neuroflow/sessions/YYYY-MM-DD.md
  - .neuroflow/ideation/
  - .neuroflow/ideation/flow.md
---

# /lit-review

Read the `neuroflow:phase-lit-review` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/ideation/flow.md` before starting.

## What this command does

Runs a structured analysis of a literature corpus — papers already retrieved via `/ideation` (Explore literature mode), by the `scholar` agent, or provided directly by the user. The command delegates the actual analysis to the `neuroflow:lit-review-protocols` skill, which implements 12 named protocols for turning a pile of papers into a synthesis, a contradiction map, a knowledge-gap report, and a draft literature review section.

This command does **not** retrieve papers. Use `/ideation` (Explore literature mode) or the `scholar` agent to retrieve papers first.

---

## Inputs — ask before starting

Ask the user for:

1. **Where are the papers?** — file paths to PDFs or markdown summaries, a `.neuroflow/ideation/` folder path, a list of DOIs or PMIDs, or pasted abstracts
2. **Research topic** — the question or domain the review should be scoped to (or read from `project_config.md` if it exists)
3. **Which protocols to run** — all 12 (default), a named subset, or a single protocol by name

If `project_config.md` already has a research question, use it as the default scope and confirm with the user before proceeding.

---

## Protocols

Once inputs are gathered, invoke the `neuroflow:lit-review-protocols` skill and pass it the papers and the selected protocol list. Do not implement any protocol logic here — delegate entirely to the skill.

The 12 protocols, in recommended order:

| # | Protocol | Purpose |
|---|---|---|
| 1 | **The Intake Protocol** | List every paper by author + year + core claim; group into assumption clusters; flag contradictions |
| 2 | **The Contradiction Hunter** | Find every place two or more papers directly contradict each other; state each side, the data/method causing disagreement, and which side has stronger evidence |
| 3 | **The Knowledge Gap Detector** | Find questions all papers assume answered but never prove; avoided methodologies; missing populations, contexts, and variables |
| 4 | **The Timeline Builder** | Reconstruct intellectual history: dominant beliefs before 2015, what shifted them, current consensus and challengers |
| 5 | **The Methodology Auditor** | Extract study design, sample size, and limitations for each paper; identify dominant methodology and what it makes impossible to prove |
| 6 | **The Citation Network Map** | Identify papers cited by most others; find which findings everything builds on; name the "Achilles heel" paper |
| 7 | **The Lit Review Writer** | Write a literature review: opening (problem), body (3–4 thematic clusters), transition (unresolved), close (why this study is next) |
| 8 | **The Devil's Advocate** | Take the strongest claim and build the most credible case against it using counterevidence, methodological weaknesses, and untested assumptions |
| 9 | **The Theoretical Framework Extractor** | Identify every theoretical model, disciplinary influences, and missing theoretical lenses |
| 10 | **The Variable Map** | Extract all independent, dependent, and moderator variables; find which appear in 70%+ of studies, which are never replicated, and untested combinations |
| 11 | **The Plain Language Translator** | Take the 5 most complex findings and rewrite them for a smart journalist; identify the best headline |
| 12 | **The Future Research Agenda** | Write a 5-point future research agenda: unanswered questions, best methodology for each, and why it matters |

---

## Steps

### Step 1 — Gather inputs

Ask the three questions above. If the user provides a `.neuroflow/ideation/` folder, scan it for literature files (e.g. `literature-*.md`). If they paste abstracts, confirm the count before proceeding.

### Step 2 — Confirm protocol selection

If no protocols are specified, confirm: *"Run all 12 protocols? This produces a full synthesis. Or name the protocols you want."*

For a single protocol, just run that one and stop.

### Step 3 — Delegate to the skill

Invoke `neuroflow:lit-review-protocols` with:
- The corpus (papers, abstracts, or paths)
- The research topic
- The selected protocol list

Let the skill run each protocol in order and produce the outputs.

### Step 4 — Save outputs

After the skill completes, save the outputs:

- Full run → `lit-review-[date].md` in `.neuroflow/ideation/`
- Single protocol → `lit-review-[protocol-name]-[date].md` in `.neuroflow/ideation/`

Update `.neuroflow/ideation/flow.md` with the new file entry.

---

## At end

- Update `.neuroflow/ideation/flow.md`
- Append a one-liner to `.neuroflow/sessions/YYYY-MM-DD.md`, e.g.:
  `- [lit-review] Ran 12 protocols on [n] papers — topic: [topic]; saved to .neuroflow/ideation/lit-review-[date].md`
