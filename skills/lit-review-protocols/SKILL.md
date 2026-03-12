---
name: lit-review-protocols
description: >
  Apply structured analytical protocols to a literature corpus retrieved after a paper search.
  Use this skill whenever /lit-review is invoked, or whenever the user asks to synthesise,
  critique, map, or write up a set of papers. Implements 12 named protocols: Intake, Contradiction
  Hunter, Knowledge Gap Detector, Timeline Builder, Methodology Auditor, Citation Network Map,
  Lit Review Writer, Devil's Advocate, Theoretical Framework Extractor, Variable Map, Plain
  Language Translator, and Future Research Agenda.
---

# lit-review-protocols

This skill implements 12 analytical protocols for structured post-retrieval literature analysis. It is invoked by the `/lit-review` command after papers have been gathered. Each protocol is a self-contained analytical procedure. Run them in order unless instructed otherwise.

---

## Before running any protocol

Read the corpus provided by the command. Build an internal index:
- Author + year + title for each paper
- Source (PubMed, bioRxiv, user-provided)
- Whether the full text or only an abstract is available

Flag any paper where only an abstract is available — note this limitation when running protocols that require methodology or data details.

---

## Protocol 1 — The Intake Protocol

**Purpose:** Build the master index of the corpus. All other protocols reference this.

**Steps:**
1. List every paper in the corpus as: `[Author(s), Year] — [Core claim in one sentence]`
2. Group papers into clusters of shared assumptions (e.g. "papers assuming attention modulates ERP amplitude", "papers assuming resting-state FC is stable across days")
3. Within each cluster, identify papers that contradict each other — mark them with `⚠ CONTRADICTION`
4. Produce a summary table: cluster name | number of papers | key assumption | contradiction present (Y/N)

**Output format:**
```
## Intake

### Paper Index
- [Author, Year] — [Core claim]
...

### Assumption Clusters
**Cluster: [name]**
- Shared assumption: [statement]
- Papers: [list]
- Contradictions: [Y/N — brief note]

### Contradiction flags
⚠ [Author A, Year] vs [Author B, Year] — [one-line description]
```

---

## Protocol 2 — The Contradiction Hunter

**Purpose:** Surface every direct contradiction between two or more papers.

**Steps:**
1. For each `⚠ CONTRADICTION` flag from Protocol 1, produce a full entry:
   - State Side A's claim and the paper making it
   - State Side B's claim and the paper making it
   - Identify the data or methodological difference that explains the disagreement (sample size, task design, population, analysis method, etc.)
   - Judge which side has stronger evidence — state why (larger N, pre-registered, more replications, better controls, etc.)
2. If no contradictions exist, state that explicitly — do not invent them.

**Output format:**
```
## Contradiction Map

### Contradiction 1: [topic]
- **Side A:** [Author, Year] — "[claim]"
- **Side B:** [Author, Year] — "[claim]"
- **What causes the disagreement:** [explanation]
- **Stronger evidence:** Side [A/B] — [reason]
```

---

## Protocol 3 — The Knowledge Gap Detector

**Purpose:** Find what the field assumes but has never proven, and what it has systematically avoided studying.

**Steps:**
1. Identify questions that all papers treat as settled but none actually test (assumed-but-not-proven)
2. Identify methodological approaches consistently absent from the corpus (avoided methodologies)
3. Identify populations, contexts, or variables that no paper in the corpus addresses (missing territory)

**Output format:**
```
## Knowledge Gaps

### Assumed but never proven
- [Statement of assumption] — assumed by [papers], never directly tested

### Avoided methodologies
- [Methodology] — absent from the corpus; possible reason: [speculation]

### Missing populations / contexts / variables
- [Missing element] — no paper in the corpus addresses this
```

---

## Protocol 4 — The Timeline Builder

**Purpose:** Reconstruct the intellectual history of the field.

**Steps:**
1. Order papers by year
2. Identify the dominant belief or consensus before 2015 (or the earliest date in the corpus if all papers are recent)
3. Identify the paper(s) or finding(s) that shifted that belief — name the mechanism of the shift (new method, replication failure, technology, etc.)
4. State the current consensus (what most papers agree on)
5. Name the papers challenging that consensus and what they claim instead

**Output format:**
```
## Timeline

### Before [year]: Dominant belief
[statement of prior consensus]

### What shifted it
[Author, Year] — [finding or method that changed the field] — [mechanism of shift]

### Current consensus
[statement]

### Current challengers
- [Author, Year] — "[challenger claim]"
```

---

## Protocol 5 — The Methodology Auditor

**Purpose:** Audit the methodological landscape of the corpus.

**Steps:**
1. For each paper, extract: study design (RCT, observational, case study, etc.), sample size (N), population, key limitation stated by authors
2. Produce a summary table
3. Identify the dominant methodology (used by the plurality of papers)
4. State what the dominant methodology structurally makes impossible to prove (its epistemic ceiling)

**Output format:**
```
## Methodology Audit

| Paper | Design | N | Population | Key limitation |
|---|---|---|---|---|
| [Author, Year] | [design] | [N] | [pop] | [limitation] |

### Dominant methodology
[description]

### What it cannot prove
[statement of epistemic ceiling]
```

---

## Protocol 6 — The Citation Network Map

**Purpose:** Identify the foundational papers and the most fragile dependency in the network.

**Steps:**
1. Identify which papers in the corpus are cited by the most other papers in the corpus (core nodes)
2. Identify which findings are treated as established premises that everything else builds on
3. Name the "Achilles heel" paper — the single paper whose replication failure would most undermine the field's current conclusions; explain why

**Note:** If full citation data is not available, infer from the corpus: which papers does every author mention? Which findings are introduced without citation (treated as obvious)?

**Output format:**
```
## Citation Network

### Most-cited papers in corpus
1. [Author, Year] — cited by [N] papers in corpus
2. ...

### Foundational findings (everything builds on these)
- [Finding] — established by [Author, Year], assumed by [papers]

### Achilles heel
[Author, Year] — [reason this paper is the most fragile dependency]
```

---

## Protocol 7 — The Lit Review Writer

**Purpose:** Produce a draft literature review section suitable for a manuscript or grant proposal.

**Steps:**
1. Write an opening paragraph: state the problem or phenomenon, why it matters, what is already known
2. Write 3–4 thematic body paragraphs: each paragraph covers one assumption cluster from Protocol 1; within each, cite supporting papers, then acknowledge contradictions
3. Write a transition paragraph: identify the most important unresolved question the corpus leaves open
4. Write a closing paragraph: explain why the current study (from `project_config.md`, or described by the user) is the logical next step

Use academic prose. Cite papers as (Author, Year). Do not use bullet points in the body — write in flowing paragraphs.

**Output format:**
```
## Literature Review

[Opening paragraph]

[Body paragraph 1 — cluster 1]

[Body paragraph 2 — cluster 2]

[Body paragraph 3 — cluster 3]

[Body paragraph 4 — cluster 4, if applicable]

[Transition paragraph — unresolved question]

[Closing paragraph — why this study is next]
```

---

## Protocol 8 — The Devil's Advocate

**Purpose:** Steel-man the strongest challenge to the field's dominant claim.

**Steps:**
1. Identify the strongest claim in the corpus — the one most papers accept and that underpins most conclusions
2. Build the most credible case *against* that claim using only evidence in the corpus:
   - Counterevidence from dissenting papers
   - Methodological weaknesses in the papers supporting the claim
   - Untested assumptions the claim depends on
3. Rate the challenge: weak (the dominant claim survives), moderate (the claim needs qualification), or strong (the claim may be wrong)

**Output format:**
```
## Devil's Advocate

### Dominant claim under scrutiny
"[claim]" — supported by [papers]

### The case against it

**Counterevidence:**
- [Author, Year] — [finding that undermines the claim]

**Methodological weaknesses in supporting papers:**
- [weakness] — affects [papers]

**Untested assumptions the claim depends on:**
- [assumption]

### Challenge rating
[Weak / Moderate / Strong] — [one-sentence justification]
```

---

## Protocol 9 — The Theoretical Framework Extractor

**Purpose:** Map the theoretical architecture underlying the corpus.

**Steps:**
1. Identify every theoretical model explicitly or implicitly used across the corpus (e.g. predictive coding, dual-process theory, embodied cognition, connectionism)
2. Identify the disciplinary influences shaping those models (cognitive neuroscience, computational psychiatry, systems neuroscience, etc.)
3. Identify theoretical lenses that are entirely absent but could reframe the findings if applied

**Output format:**
```
## Theoretical Frameworks

### Models present in corpus
| Model | Papers using it | Core assumption |
|---|---|---|
| [model] | [papers] | [assumption] |

### Disciplinary influences
- [Discipline] — shapes [aspect of the field]

### Missing theoretical lenses
- [Lens] — absent; if applied, it would reframe [finding] as [alternative interpretation]
```

---

## Protocol 10 — The Variable Map

**Purpose:** Extract and analyse the variable landscape of the corpus.

**Steps:**
1. Extract all independent variables (IVs), dependent variables (DVs), and moderators/mediators from each paper
2. Build a frequency table: how many papers include each variable
3. Flag variables present in 70% or more of papers (dominant variables — this threshold is a heuristic for "appears in the large majority"; adjust if the corpus is very small or very large)
4. Flag variables present in only one paper (never replicated)
5. Identify combinations of variables that have never been tested together in the corpus

**Output format:**
```
## Variable Map

### Variable frequency table
| Variable | Type (IV/DV/Mod) | Papers using it | % of corpus |
|---|---|---|---|

### Dominant variables (≥70% of papers)
- [variable] — [N] papers

### Never-replicated variables (single paper only)
- [variable] — only [Author, Year]

### Untested variable combinations
- [IV] × [DV] — no paper in corpus tests this combination
```

---

## Protocol 11 — The Plain Language Translator

**Purpose:** Make the 5 most complex findings accessible to a non-specialist audience.

**Steps:**
1. Identify the 5 most technically complex or counterintuitive findings in the corpus
2. For each, write a plain-language version (2–3 sentences) that a smart journalist with no neuroscience background could understand — no jargon, no abbreviations, active voice
3. After all 5, identify the single best headline for a science journalist covering this field

**Output format:**
```
## Plain Language

### Finding 1
**Original:** "[technical claim from paper]" — [Author, Year]
**Plain:** [2–3 sentence accessible version]

### Finding 2
...

### Best headline
"[Headline]"
```

---

## Protocol 12 — The Future Research Agenda

**Purpose:** Write a concrete 5-point research agenda based on what the corpus leaves unresolved.

**Steps:**
1. Identify the 5 most important unanswered questions in the corpus — draw from Protocol 3 (knowledge gaps) and Protocol 2 (contradictions)
2. For each question, specify:
   - The question
   - The best study design to answer it (be specific: RCT vs longitudinal vs cross-sectional, N required, key controls)
   - Why answering it matters (scientific and/or clinical implication)

**Output format:**
```
## Future Research Agenda

### Priority 1: [Question]
- **Best methodology:** [specific design — sample size, key controls, analysis approach]
- **Why it matters:** [scientific and/or clinical implication]

### Priority 2: [Question]
...
```

---

## Running rules

- Always run Protocol 1 (Intake) before any other protocol — all other protocols reference it
- If only an abstract is available for a paper, note this at the top of each affected protocol output
- Do not fabricate citations or findings — only use what is in the provided corpus
- If a protocol produces no output (e.g. no contradictions found), state that explicitly; do not invent content to fill the section
- For Protocol 7 (Lit Review Writer), write in academic prose — no bullet points in the body text
