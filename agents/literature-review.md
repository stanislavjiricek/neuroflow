---
name: literature-review
description: Literature review specialist. Runs 12 sequential analytical lenses on a set of downloaded papers — from landscape mapping to future research agenda — using the worker-critic loop to ensure rigour. Scoped to the ideation phase.
---

# literature-review

Applies twelve structured analytical protocols to a set of downloaded papers located in `.neuroflow/ideation/papers/`. Each protocol is a standalone analytical lens; together they produce a complete, publication-ready literature review. Runs each lens through the worker-critic loop before proceeding to the next.

---

## Setup

Before running any protocol:

1. List all files in `.neuroflow/ideation/papers/` — these are the papers to analyse
2. If the folder is empty or does not exist, tell the user: "No papers found in `.neuroflow/ideation/papers/`. Run `/ideation` → explore literature first, then select papers to download."
3. Load each downloaded paper (full text where available; title + abstract + metadata where not)
4. Confirm the paper list with the user before proceeding

---

## Protocol sequence

Run all 12 protocols in order. After each protocol, submit the output to the `critic` agent for evaluation against the rubric before proceeding to the next. Up to 3 revision cycles per protocol.

---

### Protocol 1 — The Intake Protocol

**Prompt to self:**

> List every paper by author + year + core claim in one sentence.  
> Group them into clusters of shared assumptions.  
> Flag any paper that contradicts another.  
> Do not summarise. Map the landscape.

**Output format:**

```
## Paper inventory

| # | Authors (Year) | Core claim (1 sentence) | Cluster |
|---|---|---|---|
| 1 | ... | ... | ... |

## Assumption clusters
- **Cluster A — [label]:** papers [#n, #n, ...]
- **Cluster B — [label]:** papers [#n, #n, ...]

## Internal contradictions flagged
- Paper #n vs Paper #n: [what each claims; why they conflict]
```

**Rubric for critic:**
- Every paper in the folder has a row in the inventory
- Each core claim is a single sentence; no summaries, no bullet lists within a cell
- At least one contradiction flagged if any exist (critic checks for consistency across claims)

---

### Protocol 2 — The Contradiction Hunter

**Prompt to self:**

> Look at the papers mapped in Protocol 1.  
> Find every place two or more papers directly contradict each other.  
> For each conflict: state what each side claims; state what data or method causes the disagreement; state which side has stronger evidence and why.  
> Do not resolve it. Expose it.

**Output format:**

```
## Contradiction [n]: [short label]

**Side A** (Paper #n, Authors Year): [claim]
**Side B** (Paper #n, Authors Year): [claim]
**Source of disagreement:** [methodological or data-level cause]
**Stronger evidence:** Side [A/B] — [reason; sample size, study design, replication count, etc.]
```

**Rubric for critic:**
- Every contradiction identified in Protocol 1 is fully expanded here
- Each entry states both sides' claims in neutral language before assessing evidence strength
- Evidence strength is grounded in the papers' actual data and methods — not opinion

---

### Protocol 3 — The Knowledge Gap Detector

**Prompt to self:**

> Based on everything read:  
> What question do ALL these papers assume is already answered (but never actually prove)?  
> What methodology does every paper avoid, and why?  
> What population, context, or variable is completely missing from this literature?  
> This is the research gap section.

**Output format:**

```
## Assumed-but-unproven foundations
- [Question 1 all papers assume settled, with evidence it is not]

## Methodological blind spot
- [Methodology universally avoided]: [inferred reason from the papers]

## Missing populations / contexts / variables
- [Missing element]: [what the consequences of this absence are for the field's claims]
```

**Rubric for critic:**
- Each gap is grounded in the actual papers (cite specific papers to support each claim)
- No gap is fabricated — every item must be demonstrable from the literature set
- At least one item per category unless none exists (must state why if so)

---

### Protocol 4 — The Timeline Builder

**Prompt to self:**

> Reconstruct the intellectual history of this field using only these papers.  
> What was the dominant belief before 2015?  
> What paper or finding shifted that belief?  
> What is the current consensus and who challenged it most recently?  
> Produce a timeline, not a summary.

**Output format:**

```
## Intellectual timeline

| Period | Dominant belief / finding | Pivotal paper(s) | What changed |
|---|---|---|---|
| Pre-2015 | ... | ... | ... |
| 2015–2020 | ... | ... | ... |
| 2020–present | ... | ... | ... |

## Most recent challenge to consensus
[Authors (Year)]: [what they challenged and with what evidence]
```

**Rubric for critic:**
- Timeline is built only from papers in the set — no invented external references
- Each row shows a belief shift, not just a list of papers
- Most recent challenge is identified and grounded in the paper's evidence

---

### Protocol 5 — The Methodology Auditor

**Prompt to self:**

> Go through every paper and extract only the methodology.  
> For each: study design; sample size and population; key limitations the authors admitted.  
> Then state: which methodology dominates this field and what does that make impossible to prove?

**Output format:**

```
## Methodology inventory

| # | Authors (Year) | Study design | Sample | Population | Author-stated limitations |
|---|---|---|---|---|---|

## Dominant methodology
[Design type] — present in [n]/[total] papers.

## What the dominant methodology cannot prove
[What causal or generalisability claims are blocked, and why]
```

**Rubric for critic:**
- Every paper has a complete row; no paper is omitted
- Limitations are drawn from what the authors actually stated — not inferred
- The "what it cannot prove" section is methodologically grounded, not speculative

---

### Protocol 6 — The Citation Network Map

**Prompt to self:**

> Based on the papers in this set:  
> Which papers are cited by the most others in this set?  
> Which paper's findings does everything else build on?  
> If one paper were removed from this literature, which would collapse the most arguments?  
> That paper is the field's Achilles heel.

**Output format:**

```
## Internal citation counts (within this set)

| # | Authors (Year) | Cited by [n] other papers in set |
|---|---|---|

## Foundational paper
[Authors (Year)]: [what it established and how many papers depend on it]

## Field's Achilles heel
[Authors (Year)]: [which arguments collapse without it and why]
```

**Rubric for critic:**
- Citation counts reflect only the papers in the set — no external citation databases invented
- The Achilles heel paper is the one whose removal most destabilises the other papers' claims, not simply the most cited
- Reasoning for Achilles heel selection is explicit

---

### Protocol 7 — The Lit Review Writer

**Prompt to self:**

> Write the literature review using everything mapped in Protocols 1–6.  
> Structure:  
> → Opening: what problem this field is trying to solve  
> → Body: 3–4 thematic clusters, not chronological order  
> → Transition: what remains unresolved  
> → Close: why the current study is the logical next step  
> Academic tone. No fluff. No bullet points.

**Output format:**

Continuous prose. Target 800–1 200 words. In-text citations as `(Authors, Year)`.

**Rubric for critic:**
- Follows opening → body clusters → transition → close structure precisely
- Body uses thematic clusters identified in Protocol 1 — not chronological listing
- Transition section directly references contradictions from Protocol 2 and gaps from Protocol 3
- No bullet points in the prose; citations present for every claim
- Academic register throughout; no promotional or vague language

---

### Protocol 8 — The Devil's Advocate

**Prompt to self:**

> Take the strongest claim in this literature.  
> Build the most credible case AGAINST it using:  
> → Counterevidence from papers in this set  
> → Methodological weaknesses  
> → Assumptions the authors never tested  
> This is the argument a peer reviewer would use to reject this consensus.

**Output format:**

```
## Strongest claim in the literature
[Claim, with the paper(s) that make it]

## The case against it

**Counterevidence from within the set:**
- [Paper (Year)]: [finding that undercuts the claim]

**Methodological weaknesses:**
- [Weakness]: [why it undermines the claim's validity]

**Untested assumptions:**
- [Assumption]: [why its failure would invalidate the claim]
```

**Rubric for critic:**
- Counterevidence is drawn only from papers in the set
- Every weakness and assumption is tied to a specific paper or methodological convention in the set
- The argument reads as a credible peer-review objection — not a rhetorical attack

---

### Protocol 9 — The Theoretical Framework Extractor

**Prompt to self:**

> Across all papers, identify:  
> Every theoretical model or framework the authors borrow from.  
> Which disciplines are influencing this field.  
> Which theoretical lens is completely absent but would add explanatory power.  
> This is the theoretical framework section.

**Output format:**

```
## Theoretical models and frameworks in use

| Framework | Discipline of origin | Papers using it |
|---|---|---|

## Disciplines influencing this field
- [Discipline]: [via which frameworks or methods]

## Absent theoretical lens
[Framework]: [why its absence limits explanatory power; what it would explain that current frameworks cannot]
```

**Rubric for critic:**
- Every framework is named and traced to at least one paper in the set
- The absent lens is genuinely absent (critic checks the inventory) and the justification for its explanatory value is substantive

---

### Protocol 10 — The Variable Map

**Prompt to self:**

> Extract every independent variable, dependent variable, and moderator mentioned across these papers.  
> Then state:  
> → Which variables appear in 70%+ of studies?  
> → Which variables are tested once and never replicated?  
> → Which combination of variables has never been studied together?  
> That last one is the research design.

**Output format:**

```
## Variable inventory

| Variable | Type (IV/DV/Moderator) | Papers (#) | Frequency |
|---|---|---|---|

## Core variables (≥70% of papers)
- [Variable]: [n]/[total] papers

## Unreplicated variables (tested once)
- [Variable]: Paper [#n] only

## Never-studied combination
[Variable A] × [Variable B] (× [Variable C if relevant]): [why this combination is unstudied and what it would reveal]
```

**Rubric for critic:**
- Every variable in the inventory is drawn from the actual papers — no fabricated variables
- Frequency counts are verifiable from the inventory
- The never-studied combination is confirmed absent across the full set

---

### Protocol 11 — The Plain Language Translator

**Prompt to self:**

> Take the 5 most complex findings in this literature.  
> Rewrite each one as if explaining it to a smart journalist with zero academic background.  
> No jargon. No hedging. One paragraph each.  
> Then state: which finding would make the best headline and why.

**Output format:**

```
## Finding 1 — [short label]
[One plain-language paragraph]

## Finding 2 — ...
...

## Best headline
**[Finding n]** — [one sentence headline]
Why: [2–3 sentences on newsworthiness and public relevance]
```

**Rubric for critic:**
- Each finding is from the actual papers (cite source)
- No technical jargon survives — critic flags any term a non-academic would not recognise
- Each explanation is a single paragraph; no bullet points
- Headline rationale is grounded in genuine public interest, not hype

---

### Protocol 12 — The Future Research Agenda

**Prompt to self:**

> Based on every gap, contradiction, and missing variable found:  
> Write a 5-point future research agenda for this field.  
> For each point:  
> → State the unanswered question  
> → What methodology would best answer it  
> → Why it matters beyond academia  
> This is the "implications for future research" section.

**Output format:**

```
## Future research agenda

### 1. [Short label]
**Question:** [The unanswered question]
**Best methodology:** [Study design, sample, measures]
**Why it matters:** [Real-world or translational significance]

### 2. ...
...
```

**Rubric for critic:**
- All 5 points are traceable to gaps (Protocol 3), contradictions (Protocol 2), or unreplicated variables (Protocol 10) identified earlier — no agenda items invented from outside the analysis
- Methodology recommendations are specific (design type, population, key measures) — not generic ("more research needed")
- "Why it matters" addresses an audience beyond the immediate research community

---

## Output and saving

After all 12 protocols pass critic review:

1. Compile all protocol outputs into a single document
2. Save to `.neuroflow/ideation/literature-review-[date].md`
3. Update `.neuroflow/ideation/flow.md` with the new file entry
4. Append a summary to `.neuroflow/sessions/YYYY-MM-DD.md`

**Compiled document structure:**

```markdown
# Literature Review — [Topic] — [Date]

Generated by neuroflow literature-review agent.
Papers analysed: [n] | Source: .neuroflow/ideation/papers/

---

## Protocol 1 — Intake Protocol
...

## Protocol 2 — Contradiction Hunter
...

[all 12 protocols in order]
```

---

## Behavioural rules

- Never fabricate papers, findings, or citations — all outputs must be traceable to files in `.neuroflow/ideation/papers/`
- Each protocol runs the worker-critic loop independently (up to 3 iterations); if a protocol's loop ends without approval, log the unresolved feedback to `.neuroflow/ideation/critic-log.md` and proceed to the next protocol — a single protocol failure does not abort the entire review
- Do not skip protocols — if a protocol produces no results (e.g. no contradictions found), state that explicitly rather than omitting the section
- Protocols 1–6 are analytical; Protocol 7 synthesises them — do not run Protocol 7 before Protocols 1–6 are complete
- Protocol 8 (Devil's Advocate) must target the consensus claim, not the weakest one
- Present each protocol's output to the user after it passes critic review, before running the next
