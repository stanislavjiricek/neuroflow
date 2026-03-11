---
name: review-neuro
description: >
  Run a rigorous pre-submission peer review of a neuroscience manuscript. Use this skill
  whenever the user asks to review, critique, or give feedback on a neuroscience paper,
  draft manuscript, or scientific write-up — whether they say "review my paper", "check
  my manuscript before submission", "act as a referee for my paper", "give me feedback
  on this neuroscience paper", or simply upload/paste a neuroscience manuscript and ask
  for comments. Also trigger when the user mentions fMRI, EEG, connectivity analysis,
  computational neuroscience, brain dynamics, or related topics in
  the context of evaluating written work. Covers all neuroscience subfields including
  systems, cognitive, computational, clinical, and complex-network approaches.
---

# review-neuro — Pre-Submission Referee Report for Neuroscience

Perform a rigorous six-area pre-submission review of a neuroscience manuscript,
covering language, internal consistency, claim validity, statistics, methods
reproducibility, and contribution novelty.  Produce a single consolidated report.

Applicable to any neuroscience manuscript.

---

## How to invoke

The user can provide the manuscript in any of these ways:
- Paste the full text or abstract directly into the chat
- Upload the PDF or a `.tex` file
- Describe the paper and paste key sections (Abstract, Methods, Results, Discussion)

Optionally the user can specify a **target journal** (e.g. "review as if for eLife",
"use a NeuroImage referee persona").  If not specified, apply high general standards.

---

## Phase 0 — Setup

1. Read all manuscript content provided (uploaded files, pasted text, or both).
2. Extract: paper title, authors, journal target (if mentioned), and key methods.
3. Identify the manuscript type: empirical neuroimaging | EEG/iEEG | computational
   modelling | information-theoretic/causality methods | clinical | review/methods paper.
4. Note the target journal and load its persona from the table below:

| Abbrev | Editorial persona |
|---|---|
| NatNeurosci | Nature Neuroscience: demands clear conceptual advance, causal evidence, broad relevance |
| NatComms | Nature Communications: high technical standard, multidisciplinary, reproducibility |
| Neuron | Cell Press / Neuron: mechanistic insight or landmark computational contribution |
| eLife | eLife: open-science champion; data/code deposit expected; transparent reporting |
| JNeurosci | Journal of Neuroscience: rigorous methods, clear controls, reproducible |
| PNAS | PNAS: broad significance across disciplines |
| NeuroImage | NeuroImage: fMRI/EEG/MEG technical standards; COBIDAS compliance |
| HBM | Human Brain Mapping: connectivity statistical rigour; OpenNeuro data encouraged |
| CerebCortex | Cerebral Cortex: mechanistic neuroscience, solid anatomy, strong methods |
| ClinNeurophysiol | Clinical Neurophysiology: clinical relevance, validated biomarkers |
| Epilepsia | Epilepsia: epilepsy-specific methodology, ILAE terminology |
| Psychophysiology | Psychophysiology: psychophysiological methods rigour, effect sizes |
| NetworkNeuro | Network Neuroscience: graph-theory methodology, null models, open data |
| PLoSCB | PLoS Computational Biology: model correctness, biological plausibility, code required |
| FrontNeurosci | Frontiers in Neuroscience: solid methods, broad scope, open code encouraged |
| PhysRevE | Physical Review E: mathematical/physical rigour, analytic derivations |
| Chaos | Chaos (AIP): dynamical systems correctness, novelty of neural application |
| Entropy | Entropy (MDPI): information-theoretic framework correctness, open data |
| SciRep | Scientific Reports: technical correctness and reproducibility |

---

## Phase 1 — Six-Area Review

Work through all six areas in sequence.  For each, produce a clearly headed section of
structured findings.  Do not skip an area — write "No issues found" or "Not applicable"
if nothing to report.

---

### Area 1 — Language, Style & Terminology

Check and flag:
1. Spelling errors, grammatical mistakes, and punctuation errors (with location).
2. Abbreviations not defined on first use or used inconsistently.
3. Neuroscience terminology errors:
   - "BOLD activation" → prefer "BOLD signal change" or "haemodynamic response"
   - "proves / shows that the brain does X" → overclaim; use "is associated with"
   - "functional connectivity reflects direct connections" → overclaim
   - Conflating "synchrony", "coherence", "correlation", "functional connectivity"
   - Using "causality" when only Granger causality or transfer entropy was measured
     (these are *directed statistical dependencies*, not interventional causality)
   - "significant" without specifying statistically or clinically
4. Vague quantifiers ("many", "several") that should be specific numbers.
5. Species, strain, sex, age of subjects/animals not stated.
6. Tense inconsistencies (Methods: past tense; general statements: present tense).
7. For physics/maths components: notation inconsistencies (bold/italic, hat, subscripts).

---

### Area 2 — Internal Consistency & Cross-Reference Integrity

Check:
1. Every figure, table, equation, and supplementary item cited in text actually exists
   and is numbered correctly.
2. Numerical values in the Abstract match those in Results.
3. Statistical values (*p*, *t*, *F*, *r*, *z*, BF) in text match figures and tables.
4. Number of subjects / electrodes / nodes / ROIs consistent across Methods, Results,
   and figure legends.
5. For network papers: node count, edge count, and parcellation consistent throughout.
6. For modelling papers: parameter values in text match equations and any linked code.
7. Every analysis in Results has a corresponding Methods section.
8. Bibliography: duplicate entries, obviously wrong years or journals, missing DOIs.

---

### Area 3 — Claim Support, Causality Language & Connectivity Interpretation

**Key concern**: neuroscience papers frequently over-interpret correlational or
directed-statistical-dependence evidence as causal or mechanistic.

Flag:
1. Major claims in Abstract and Discussion with no direct evidentiary link (cite the
   offending sentence and state what evidence is missing).
2. **Causality creep**: correlational language replaced by interventional claims without
   a manipulation (optogenetics, DREADD, lesion, TMS, pharmacology):
   - "X drives Y", "X is required for Y", "X causes Y" — only valid with manipulation.
   - Transfer entropy / Granger causality / conditional MI = *directed statistical
     influence*, not mechanistic causation.
3. **FC over-interpretation**: undirected FC (Pearson correlation, coherence, PLV) ≠
   direct anatomical connection or causal pathway.
4. **Connectivity → behaviour**: correlational link between FC and behaviour stated as
   explanatory without mechanistic evidence.
5. **Network measure claims**: graph measures (clustering, path length, centrality,
   modularity) given specific functional meaning without null-model validation or
   citation to the methodological literature.
6. **Model generalisation**: computational model behaviour claimed to imply the same
   mechanism in biological tissue without empirical validation.
7. Over-generalisation across species, brain states, or populations not tested.
8. Contested claims in Introduction/Discussion missing key citations.

---

### Area 4 — Statistics, Network Inference & Multiple Comparisons

**General:**
1. Power analysis or sample-size justification — present? If not, flag.
2. Correct test choice: parametric on non-normal small samples? Repeated-measures
   correlation unaccounted for? Paired comparisons treated as independent?
3. Effect sizes alongside *p*-values (Cohen's *d*, η², *r*, ω²)?
4. Individual data points shown or available?
5. Mean ± SD vs ± SEM clearly distinguished?

**Multiple comparisons:**
6. Whole-brain neuroimaging: voxelwise FWE/FDR or permutation-based correction applied?
   Flag uncorrected maps.
7. Connectivity matrices (NxN edges): FDR or permutation over the full matrix?
8. Multiple frequency bands, ROIs, or time windows: correction explicit?

**Network / connectivity:**
9. Null models used to benchmark graph measures (random graph, degree-preserving
   rewiring, phase-randomised surrogates)?
10. Parcellation choice justified? Robustness to alternative atlases shown?
11. Dynamic FC: sliding-window length justified? Stationarity tested or acknowledged?
12. iEEG / MEG coherence: volume conduction / field spread accounted for?

**Information-theoretic / causality:**
13. TE / conditional MI: estimator (kernel, KSG, binning) specified and justified?
    Hyperparameters (embedding dimension, history length) reported and validated
    against surrogates?
14. Significance threshold set using appropriate surrogates (time-shifted,
    phase-randomised, permutation)?
15. Effect of filtering on causality measures discussed (known to induce spurious GC)?

**Computational modelling:**
16. Parameters physiologically constrained and values justified?
17. Fitting / optimisation procedure fully described?
18. Predictions validated against held-out empirical data?

---

### Area 5 — Methods Reproducibility, Reporting Standards & Open Science

Evaluate each applicable subsection as PASS / PARTIAL / FAIL / N/A with a brief comment.

**A. Human subjects**
- Ethics / IRB approval stated; informed consent stated.
- Demographics: age mean ± SD, sex, handedness where relevant.
- Clinical populations: DSM/ICD criteria, medication status, illness duration.
- Longitudinal studies: dropout rates and missing-data handling.

**B. Animal studies (ARRIVE 2.0)**
- Species, strain, sex, age, weight; housing and husbandry.
- Ethical approval number.
- Randomisation and blinding described; exclusion criteria pre-specified.

**C. fMRI (COBIDAS / OHBM)**
- Scanner: field strength, manufacturer, TR, TE, flip angle, voxel size, n volumes,
  slice acquisition order.
- Preprocessing: software + version, steps listed (motion correction, slice-timing,
  smoothing FWHM, band-pass, ICA-FIX / aCompCor).
- Motion: scrubbing thresholds stated; mean FD per group reported.
- Normalisation: MNI template version, registration method.
- Resting-state: global signal regression decision explicitly stated and justified.

**D. EEG / MEG**
- Electrode count, reference, sampling rate, hardware filter.
- Preprocessing: ICA or threshold artefact rejection; muscle/eye artefact handling.
- Source imaging: forward model (BEM/sphere), inverse method, regularisation.
- Simultaneous EEG-fMRI: BCG artefact removal method (OBS, AAS).

**E. Intracranial EEG (iEEG / SEEG / ECoG)**
- Electrode type, contact count, spatial sampling.
- MRI co-registration method.
- Spike sorting or LFP artefact rejection.
- Clinical placement stated not tailored to hypothesis.

**F. Computational modelling**
- All model equations stated or referenced; parameters in table with values and units.
- Initial conditions; sensitivity / robustness analysis.
- Simulation software: language, version, availability.
- Whole-brain models (TVB etc.): connectome source and parcellation.
- Fitting: optimiser, cost function, convergence criteria.

**G. Information-theoretic / causality measures**
- Estimator fully specified; surrogate generation described.
- Embedding / history-length selection procedure stated.

**H. Data & code availability**
- Data deposited: OpenNeuro, OSF, Zenodo, Dryad, EBRAINS, figshare, G-Node GIN?
- Code available: GitHub / OSF / Zenodo with citable DOI?
- Environment file (conda / pip / Docker) present?
- For models: parameters + code sufficient to reproduce key figures?

---

### Area 6 — Contribution, Novelty & Journal Fit (Adversarial Referee)

Write this section in the first person, as an actual referee report to the target
journal (use the persona from Phase 0, or "a generic high-standards referee" if none).

Address:
1. **Novelty**: Has this been shown before, in whole or part?  Name the two or three
   closest prior papers; state the incremental advance.
2. **Conceptual significance**: Does the paper address a major open question, or is it
   incremental in a saturated literature?
3. **Technical advance** (if methods paper): Is it demonstrably better than existing
   approaches on the right benchmarks?
4. **Impact**: Who will read and use this?  Is the audience wide enough for the target
   journal?
5. **Alternative interpretations**: The two strongest alternative explanations for the
   key result that the authors have not addressed.
6. **Missing analyses**: One or two specific additional analyses that would make the
   paper unambiguously publishable.
7. **Journal fit**: Explicit comment on whether scope and contribution level match the
   target journal.  If not, suggest a better outlet.
8. **Recommendation**: Accept / Major revision / Minor revision / Reject — one sentence.

---

## Phase 2 — Consolidated Report

After completing all six areas, compile the full report using this template:

```
# PRE-SUBMISSION REVIEW — NEUROSCIENCE
Date: [today's date]
Target journal: [JOURNAL or "Generic high standards"]
Paper: [title, authors if available]

---

## Executive Summary
[3–5 sentences: core contribution, main strengths, most critical issues]

## ⚠ Priority Issues (must address before submission)
[Numbered, deduplicated list of the most serious problems]

## 1 · Language & Style
[Area 1 findings]

## 2 · Internal Consistency
[Area 2 findings]

## 3 · Claim Support & Causality
[Area 3 findings]

## 4 · Statistics & Network Inference
[Area 4 findings]

## 5 · Methods Reproducibility & Open Science
[Area 5 checklist]

## 6 · Contribution & Novelty [{JOURNAL} referee]
[Area 6 first-person report]

---
*Generated by review-neuro skill*
```

Present the full report to the user.

**Immediately after presenting the report, save it automatically:**
1. Write the full report to `.neuroflow/paper-review/review-[date].md` (e.g. `review-2026-03-10.md`).
2. Update `.neuroflow/paper-review/flow.md` to list the new file.
3. Append a **single one-liner** to `.neuroflow/sessions/YYYY-MM-DD.md` — e.g.:
   `- [paper-review] Review of "[Paper title]" for [Journal] saved to .neuroflow/paper-review/review-[date].md`
   Do **not** paste the review content into the session log.

Then tell the user:

> Review saved to `.neuroflow/paper-review/review-[date].md`.
>
> Would you like to:
> - Expand any section in more detail
> - Focus on a specific area for revision guidance
> - Re-run the review for a different target journal

---

## Notes for Claude

- If only an abstract is available, note this prominently in the report and flag that
  several areas (especially 4 and 5) can only be partially assessed.
- Maintain a constructive but critical tone — the goal is to find all problems before
  the real referees do.
- Do not hallucinate specific citations; if a key reference appears to be missing, say
  so and describe the type of work that should be cited rather than inventing titles.
- Apply appropriate dual standards where relevant (e.g., both neuroscience reporting norms AND mathematical notation standards for computational/physics-adjacent manuscripts).

## Slash command

This skill is invoked as part of the `/neuroflow:paper-review` command. If used directly without that command, run the full review workflow as normal and mention at the end:

> 💡 You can also run `/neuroflow:paper-review` to start the full paper review workflow as a slash command next time.
