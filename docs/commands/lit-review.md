---
title: /lit-review
---

# `/neuroflow:lit-review`

**Structured post-retrieval literature analysis using 12 named protocols.**

`/lit-review` takes a set of papers you have already retrieved and applies a suite of analytical protocols to synthesise findings, surface contradictions, map knowledge gaps, audit methodology, and draft a literature review section. It runs after `/ideation` (Explore literature mode) or the `scholar` agent — it does not retrieve papers itself.

---

## When to use it

- After retrieving papers with `/ideation` or the `scholar` agent
- When you need to synthesise a literature corpus rather than just read it
- Before writing a background section in `/paper-write` or `/grant-proposal`
- When you want structured critique of a field's assumptions and contradictions

---

## What it does

Claude gathers the corpus and delegates analysis to the `neuroflow:lit-review-protocols` skill, which implements 12 named protocols:

| # | Protocol | What it produces |
|---|---|---|
| 1 | **The Intake Protocol** | Master index: author + year + core claim; assumption clusters; contradiction flags |
| 2 | **The Contradiction Hunter** | Full contradiction map: sides, causes, which has stronger evidence |
| 3 | **The Knowledge Gap Detector** | Assumed-but-never-proven questions; avoided methodologies; missing populations |
| 4 | **The Timeline Builder** | Intellectual history: prior consensus, what shifted it, current state and challengers |
| 5 | **The Methodology Auditor** | Study design, N, and limitations per paper; dominant methodology and its epistemic ceiling |
| 6 | **The Citation Network Map** | Most-cited papers; foundational findings; the Achilles heel paper |
| 7 | **The Lit Review Writer** | Draft literature review: opening, 3–4 thematic clusters, transition, close |
| 8 | **The Devil's Advocate** | Case against the dominant claim: counterevidence, weaknesses, untested assumptions |
| 9 | **The Theoretical Framework Extractor** | All theoretical models, disciplinary influences, and missing lenses |
| 10 | **The Variable Map** | All IVs/DVs/moderators; dominant, never-replicated, and untested combinations |
| 11 | **The Plain Language Translator** | 5 complex findings rewritten for a journalist; best headline |
| 12 | **The Future Research Agenda** | 5-point agenda: question, best methodology, why it matters |

---

## Example session

```
/neuroflow:lit-review
```

```
Claude: Where are the papers?

You: .neuroflow/ideation/literature-alpha-oscillations-2025-03-01.md

Claude: Research topic?

You: Alpha oscillation suppression in working memory tasks

Claude: Run all 12 protocols or a specific subset?

You: Run 1, 2, 3, and 7

Claude: [Intake Protocol]

        ## Intake

        ### Paper Index
        - [Cohen & Maris, 2010] — Alpha suppression reflects active inhibition of
          task-irrelevant cortical regions during working memory retention
        - [Klimesch et al., 2007] — Alpha synchronisation, not just suppression,
          reflects top-down attentional gating...

        ### Assumption Clusters
        **Cluster: Alpha as inhibition**
        - Shared assumption: alpha power decrease = neural activation in that region
        - Papers: Cohen & Maris (2010), Jensen & Mazaheri (2010), Foxe & Snyder (2011)
        - Contradictions: Y ⚠

        ⚠ Jensen & Mazaheri (2010) vs Palva & Palva (2011) — inhibition vs routing model

        [Contradiction Hunter]

        ## Contradiction Map

        ### Contradiction 1: Alpha as inhibition vs alpha as routing
        - **Side A:** Jensen & Mazaheri (2010) — "Alpha reflects active inhibition..."
        - **Side B:** Palva & Palva (2011) — "Alpha organises routing of information..."
        - **What causes the disagreement:** Different tasks (pure suppression vs
          cross-frequency coupling paradigm), different analysis (power vs phase)
        - **Stronger evidence:** Side B — pre-registered follow-up with higher N (N=45 vs N=18)

        [continues through Protocol 3 and Protocol 7...]
```

---

## Protocol subsets

| Goal | Run protocols |
|---|---|
| Quick synthesis | 1, 2, 3, 7 |
| Methodology review | 1, 5, 6 |
| Manuscript background section | 1, 4, 7, 12 |
| Grant proposal background | 1, 3, 7, 12 |
| Full analysis | 1–12 |

---

## Output

| Protocol run | Saved as |
|---|---|
| All 12 | `.neuroflow/ideation/lit-review-[date].md` |
| Single protocol | `.neuroflow/ideation/lit-review-[protocol-name]-[date].md` |
| Custom subset | `.neuroflow/ideation/lit-review-custom-[date].md` |

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/ideation/flow.md`, paper corpus |
| Writes | `.neuroflow/ideation/`, `.neuroflow/ideation/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md` |

---

## Related commands

- [`/ideation`](ideation.md) — retrieve papers via PubMed/bioRxiv before running this command
- [`/paper-write`](paper-write.md) — use the Protocol 7 output as your background section scaffold
- [`/grant-proposal`](grant-proposal.md) — use Protocol 3 and 12 outputs to build the significance and innovation sections
- [`/paper-review`](paper-review.md) — review a manuscript after writing it
