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

Perform a rigorous eight-area pre-submission review of a neuroscience manuscript using
eight parallel specialist agents. Areas: language, internal consistency, claim validity,
statistics, methods reproducibility, contribution novelty, literature gap, and figure
review. Produces a single consolidated report with scope annotation.

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
| FrontCompNeuro | Frontiers in Computational Neuroscience: modelling rigour, biological plausibility |
| PhysRevE | Physical Review E: mathematical/physical rigour, analytic derivations |
| Chaos | Chaos (AIP): dynamical systems correctness, novelty of neural application |
| Entropy | Entropy (MDPI): information-theoretic framework correctness, open data |
| SciRep | Scientific Reports: technical correctness and reproducibility |
| Brain | Brain (Oxford): clinical neuroscience, translational relevance, mechanistic insight |
| NeurobiolDis | Neurobiology of Disease: disease model rigour, translational relevance |
| BrainCogn | Brain and Cognition: cognitive neuroscience, solid experimental design |

---

## Phase 0b — Pre-scan literature

Before launching the review agents, attempt to load reference literature for use in Area 7 (Literature Gap).

**Try Zotero MCP first:**
Use `tool_search` to check for available Zotero MCP tools (look for tools matching `zotero`). If six or more Zotero tools are found:
1. Run a semantic search in Zotero for the paper's topic keywords
2. Retrieve the top 10–20 matches (title, authors, year, abstract, tags)
3. Store this as the "Zotero hit list" for Agent 7

**If Zotero MCP tools are unavailable or return zero results:**
Silently fall back — do not mention Zotero to the user. Instead:
1. Check if `.neuroflow/ideation/papers/` exists in the working directory
2. If yes: list all `.md` metadata files there; read title, authors, year, abstract from each
3. Store this as the "local papers hit list" for Agent 7
4. If the folder does not exist or is empty: Agent 7 will work from manuscript references only

Do not block the review on literature availability. Proceed to Phase 1 regardless.

---

## Phase 1 — Eight-area parallel review

Spawn eight specialist agents in parallel. Each agent works independently on the same manuscript. Do not wait for one agent to finish before starting the next — launch all eight simultaneously and collect outputs.

Each agent produces one clearly headed section of structured findings. "No issues found" or "Not applicable" is a valid output for any item.

---

### Agent 1 — Language, Style & Terminology

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

### Agent 2 — Internal Consistency & Cross-Reference Integrity

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

### Agent 3 — Claim Support, Causality Language & Connectivity Interpretation

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

### Agent 4 — Statistics, Network Inference & Multiple Comparisons

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

### Agent 5 — Methods Reproducibility, Reporting Standards & Open Science

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

### Agent 6 — Contribution, Novelty & Journal Fit (Adversarial Referee)

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

### Agent 7 — Literature Gap

Identify missing or overlooked prior work that should be cited or engaged with.

**Data sources (in priority order):**
1. Use the "Zotero hit list" from Phase 0b if available (Zotero MCP was connected)
2. Otherwise use the "local papers hit list" from Phase 0b (`.neuroflow/ideation/papers/*.md`)
3. Otherwise work from the manuscript's own reference list and general knowledge

**Check for:**
1. Key foundational papers for the method(s) used that are not cited.
2. Recent (last 2 years) high-impact work in the same area that the authors appear
   unaware of — especially papers that directly anticipate or contradict key claims.
3. Papers that established or challenged the theoretical framework the authors rely on.
4. Seminal negative results or replication failures relevant to the main claim.
5. Competing methods papers that should be benchmarked against or at least discussed.
6. Cross-disciplinary work (physics, machine learning, clinical) that is clearly
   relevant but absent.

**Output format:**
For each gap, write:
```
Gap: [brief description of what is missing]
Why it matters: [one sentence — how its absence weakens the paper]
Example work: [if from Zotero/local library: cite entry; otherwise: describe the type of work without fabricating titles]
```

Do not fabricate specific paper titles, DOIs, or authors. If referencing a type of work that exists but is not in the available library, say so clearly ("A body of work on X exists; representative examples should be cited — see [general area description]").

---

### Agent 8 — Figure Review

Evaluate all figures present in the manuscript (uploaded images, PDF pages, or described figures).

**For each figure:**
1. **Colormap check**: Is the colormap perceptually uniform and accessible to colour-blind readers? Flag jet/rainbow colormaps on scalar data — recommend viridis, cividis, or plasma. Flag diverging data mapped with a sequential colormap.
2. **Font size**: Are axis labels, tick labels, and legends legible at journal print size (typically 85–174 mm column width)? Flag anything below 7pt effective size.
3. **Caption completeness**: Does the caption describe all panels, define all abbreviations used in the figure, state n (sample size or observation count), and define error bars (SD / SEM / CI)?
4. **Figure–text consistency**: Does the caption and/or main text describe every panel? Are panel labels (A, B, C...) present and referenced in the text?
5. **Data representation**: Are individual data points shown alongside summary statistics where N < 30? Are error bars clearly defined?
6. **Axis labels**: Are all axes labelled with units? Are scale bars included for microscopy/anatomy images?
7. **Statistical annotations**: Are significance markers (*, **, ns) defined in the legend or caption?
8. **Overall clarity**: Is the figure interpretable without reading the methods in full?

If figure files are not directly accessible (text-only manuscript), assess from figure captions and text references and note accordingly.

---

## Phase 2 — Consolidate and archive

1. Collect all eight agent outputs.
2. Compile the full consolidated report (see template below).
3. **Zotero archival**: If the Zotero MCP was available in Phase 0b, attempt to save the review report as a note attached to the most relevant Zotero item. Skip silently if MCP is unavailable or the operation fails.

### Report template

```
# PRE-SUBMISSION REVIEW — NEUROSCIENCE
Date: [today's date]
Manuscript: [title, authors if available]
Target journal: [JOURNAL or "Generic high standards"]
Review scope: [Full 8-area review | Abstract-only (areas 4, 5, 8 partially assessed) | {other limitation}]
Literature source: [Zotero ({n} items) | Local library: .neuroflow/ideation/papers/ ({n} files) | Manuscript references only]

---

## Executive Summary
[3–5 sentences: core contribution, main strengths, most critical issues]

## ⚠ Priority Issues (must address before submission)
[Numbered, deduplicated list of the most serious problems across all eight areas]

## 1 · Language & Style
[Agent 1 findings]

## 2 · Internal Consistency
[Agent 2 findings]

## 3 · Claim Support & Causality
[Agent 3 findings]

## 4 · Statistics & Network Inference
[Agent 4 findings]

## 5 · Methods Reproducibility & Open Science
[Agent 5 checklist]

## 6 · Contribution & Novelty [{JOURNAL} referee]
[Agent 6 first-person report]

## 7 · Literature Gap
[Agent 7 findings]

## 8 · Figure Review
[Agent 8 findings]

---
*Generated by review-neuro skill (8-agent parallel review)*
```

Present the full report to the user.

**Immediately after presenting the report, save it automatically:**
1. Write the full report to `reviews/review-[title-slug]-[date].md` in the project directory. Create the `reviews/` folder if it does not exist.
2. Append a **single one-liner** to `.neuroflow/sessions/YYYY-MM-DD.md` — e.g.:
   `- [review] Referee report for "[Paper title]" ([Journal]) saved to reviews/review-[title-slug]-[date].md`
   Do **not** paste the review content into the session log.

Then tell the user:

> Review saved to `reviews/review-[title-slug]-[date].md`.
>
> Would you like to:
> - Expand any section in more detail
> - Focus on a specific area for revision guidance
> - Re-run the review for a different target journal

---

## Notes for Claude

- If only an abstract is available, note this prominently in the report header (`Review scope:`) and flag that areas 4, 5, and 8 can only be partially assessed.
- Collect all eight agent outputs before writing the consolidated report — do not present partial results mid-review.
- Maintain a constructive but critical tone — the goal is to find all problems before the real referees do.
- Do not hallucinate specific citations; if a key reference appears to be missing, say so and describe the type of work that should be cited rather than inventing titles.
- Apply appropriate dual standards where relevant (e.g., both neuroscience reporting norms AND mathematical notation standards for computational/physics-adjacent manuscripts).

## Slash command

This skill is invoked as part of the `/neuroflow:review` command. If used directly without that command, run the full review workflow as normal and mention at the end:

> 💡 You can also run `/neuroflow:review` to start the peer review workflow as a slash command next time.
