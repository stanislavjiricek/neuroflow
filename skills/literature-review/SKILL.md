---
name: literature-review
description: Use when conducting neuroscience literature reviews, searching PubMed or bioRxiv, building reference lists, identifying research gaps, summarizing prior findings, or preparing a Background/Introduction section for a neuroscience paper. Triggers on "find papers about", "literature review", "what is known about", "search PubMed", "systematic review", "prior studies on", or requests to map the state of a field.
version: 1.0.0
---

# Literature Review for Neuroscience Research

## Purpose

Conduct efficient, rigorous literature searches and synthesize findings into structured summaries that inform study design, hypothesis formulation, and paper writing.

## When This Skill Applies

- Searching for prior work on a neuroscience topic
- Identifying methodological approaches used in a field
- Finding contradictions, replications, or gaps in the literature
- Preparing the Background / Introduction section of a paper
- Building a BibTeX reference list

## Search Strategy

### 1. Define Search Terms

Use a layered approach:
- **Core concept**: the primary phenomenon (e.g., "N200", "working memory", "alpha oscillations")
- **Modality**: "EEG", "fMRI", "MEG", "eye tracking"
- **Population**: "healthy adults", "schizophrenia", "children"
- **Method**: "permutation test", "ICA", "decoding", "MVPA"

**Boolean template:**
```
("N200" OR "N2") AND ("EEG" OR "ERP") AND ("response inhibition" OR "conflict monitoring")
```

### 2. Database Priority

| Database | Best for |
|---|---|
| **PubMed** | Clinical, cognitive neuroscience, peer-reviewed |
| **bioRxiv** | Latest preprints, cutting-edge methods |
| **Google Scholar** | Broad coverage, citation counts |
| **NeuroSynth** | fMRI meta-analysis, coordinate-based |
| **OpenNeuro** | Publicly available datasets |

Use the `search_articles` (PubMed) and `search_preprints` (bioRxiv) tools when available.

### 3. Inclusion/Exclusion Criteria

Define before searching:
- **Inclusion**: Human subjects, peer-reviewed (or preprint with code), modality match
- **Exclusion**: Animal studies (unless directly translational), no neural measure, no statistics

### 4. Synthesis Structure

For each relevant paper, extract:
- **Population**: N, age, sex ratio, clinical status
- **Paradigm**: task type, condition structure, key manipulation
- **Modality & preprocessing**: recording system, key preprocessing steps
- **Main finding**: DV, direction, effect size if reported
- **Limitations**: noted by authors or apparent

### 5. Gap Analysis

After synthesis, identify:
1. **Replicated findings**: consensus in the field
2. **Contradictions**: conflicting results, possible moderators
3. **Missing populations**: understudied groups
4. **Methodological gaps**: outdated methods, lack of open data
5. **Your study's niche**: how it fills a specific gap

### 6. Output Format

```
## Literature Summary: [Topic]

### Consensus findings
- ...

### Contradictions / open questions
- ...

### Methodological approaches observed
- ...

### Identified gaps (your study addresses)
- ...

### Key references (BibTeX format)
@article{...}
```

## Citation Formatting

Produce BibTeX entries ready for LaTeX import. Always include:
- `author`, `title`, `journal`, `year`, `volume`, `pages`, `doi`
- Use the MNE / Neuroimage / JNeurosci journal abbreviations where applicable
