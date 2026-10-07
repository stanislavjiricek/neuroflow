---
title: /paper
---

# `/neuroflow:paper`

**Draft and internally review every section of your manuscript — nothing is saved without critic approval.**

`/paper` is the unified manuscript command. It replaces two separate steps (draft, then review) with a single brutal loop: the `paper-writer` agent drafts each section, the `paper-critic` agent applies the full eight-area peer-review methodology, and the loop iterates up to 3 times per section. Only approved sections reach disk.

---

## When to use it

- After `/data-analyze` — results and figures are ready
- You want to produce a manuscript that has been through rigorous internal review before it reaches a real journal
- You want drafting and critique in one integrated workflow with automatic critic approval gates

---

## What it does

Claude reads your project memory and asks:

1. **Target journal?**
2. **Format?** LaTeX or Markdown/Word
3. **Which section(s)?** — or full paper
4. **Review focus?** — full eight-area critique on every section, or specific areas

For each section, the `paper-writer` agent first returns an outline. You approve it (or change it) before any prose is written. The agents run as subagents and never ask you anything themselves: every question comes from the main conversation.

The writer cites only papers in your project library (`.neuroflow/ideation/papers/` or your reference-manager export). A claim that needs a paper the library lacks gets a `[CITE: …]` placeholder and a question to you; it is never filled from memory.

---

## The write→critique loop

Every section goes through this loop before it is saved:

```
paper-writer → draft v1
paper-critic → [STATUS: APPROVED] or [STATUS: REJECTED] + actionable feedback

if APPROVED → section saved to manuscript/
if REJECTED → paper-writer revises → draft v2
              paper-critic → verdict

if APPROVED → section saved
if REJECTED → paper-writer revises → draft v3
              paper-critic → verdict

if APPROVED → section saved
if REJECTED (3rd) → loop halts; unresolved critique logged to .neuroflow/paper/critic-log.md
                    user decides whether to accept the draft or stop
```

Maximum 3 iterations per section. Nothing is written to `manuscript/` without `[STATUS: APPROVED]` or explicit user acceptance. Rounds 2 and 3 continue the same writer and critic agents, so they keep what they already read and the critic remembers its own earlier feedback.

---

## Modes

| Mode | What it does |
|---|---|
| default | The drafting loop above |
| `--submit` | Submission package: cover letter, availability statements, CRediT, suggested reviewers, **AI-use statement**, acknowledgements line, pre-submission checks (citations, statistics, figures) and a ✅/❌ checklist |
| `--revise` | Reviewer rebuttal under the prime rule: minimal changes, only what a reviewer asked; an audit script checks that every change traces to a comment |
| `--coauthor <file.docx>` | Works through a coauthor's Word comments and tracked changes one row at a time; the coauthor's file is never edited |
| `--abstract` | Conference abstract with one critic pass |
| `--xray <file>` | Sentence-by-sentence check: an annotated copy with red (countable defects) and orange (judgement) findings; reports only. With the neuroflow mod, `--xray view` opens the findings as a pane to accept or reject, and `--xray check <file>` runs only the statistics and citation scripts |
| `--auto on\|off\|status\|sync` | A living paper skeleton in `.neuroflow/paper/`: facts with sources, preregistered hypotheses quoted word for word, one Results slot per planned test, reporting gaps — no prose results. With the neuroflow mod, `--auto status` opens a pane with the gaps and the sources changed since the last sync |

---

## Checks that run as scripts

| Script | What it reports |
|---|---|
| `cite_check.py` | "DOI resolves" or "does not resolve"; retraction, withdrawal, expression-of-concern and correction notices in Crossref ("no retraction notice found in Crossref as of <date>"); cited DOIs missing from the project library |
| `statcheck.py` | Whether each reported p matches its t, F, r, χ² or z and degrees of freedom; corrected p-values are skipped |
| `revise_audit.py` | Changes in the revised manuscript that no reviewer comment quotes, and quoted changes that are not in the manuscript |
| `docx_comments.py` | A .docx's comments and tracked changes as a work table |

They live in the `phase-paper` skill (`scripts/`), need only Python 3.10+, and never claim more than they test: a DOI that resolves can still be cited for something the paper does not say.

---

## AI use and style editing

The `humanizer` skill is a style edit (filler, rhythm, register) that runs only when you ask for it. It is never used to hide AI involvement. `--submit` drafts an AI-use statement from the session and critic logs; you confirm it before it goes into the package.

---

## Critic standards

The `paper-critic` agent applies the full `neuroflow:review-neuro` eight-area methodology to every draft:

| Area | What is checked |
|---|---|
| Language & Terminology | Spelling, grammar, neuroscience terminology errors, causality language |
| Internal Consistency | Figure/table references, value consistency across sections |
| Claim Support & Causality | Overclaims, causality creep, FC over-interpretation |
| Statistics | Effect sizes, multiple-comparison correction, null models, estimator specification |
| Methods Reproducibility | COBIDAS/ARRIVE compliance, artefact thresholds, data/code availability |
| Contribution & Novelty | Novelty claims, prior work comparison, journal fit |
| Literature Gap | Missing citations vs local paper library and the manuscript's own references |
| Figure Review | Figure citations, panel completeness, axes/units/error bars, statistical annotations |

Figure Review findings are advisory: they never block a verdict, and you see them in the critique summary after each section — fix a figure in its plotting code through the [`/data-analyze`](data-analyze.md) figure check. A figure that contradicts the text or the statistics is a blocking Internal Consistency or Statistics item instead.

A section is approved only if it would survive peer review at a top-tier neuroscience journal. The bar is not "acceptable draft" — it is "ready for submission".

---

## Drafting order

For a full paper, sections are drafted in this order:

| Order | Section | Source material |
|---|---|---|
| 1 | **Methods** | `.neuroflow/experiment/`, `.neuroflow/data-preprocess/`, `.neuroflow/data-analyze/` |
| 2 | **Results** | `.neuroflow/data-analyze/` (analysis outputs, figures) |
| 3 | **Introduction** | `.neuroflow/ideation/` (research question, literature) |
| 4 | **Discussion** | All prior sections plus interpretation |
| 5 | **Abstract** | Always last — summarises after all other sections are approved |

---

## Output

Approved sections are saved to `manuscript/` (or the path set in `.neuroflow/paper/flow.md`). Loop state is tracked in `.neuroflow/paper/critic-log.md`.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/ideation/flow.md`, `.neuroflow/ideation/papers/`, `.neuroflow/data-analyze/flow.md`, `.neuroflow/preregistration/flow.md`, `.neuroflow/paper/flow.md`, `.neuroflow/sessions/` (`--submit`) |
| Writes | `.neuroflow/paper/` (critic log, coauthor rounds, X-ray files, skeleton, DOI cache), `.neuroflow/paper/flow.md`, `.neuroflow/reasoning/paper.jsonl`, `.neuroflow/project_config.md` (`target_journal`, `paper_auto`), `.neuroflow/timeline.md`, `.neuroflow/sessions/YYYY-MM-DD.md`, `manuscript/` (approved drafts, `submission/`, `revision/`, `abstracts/`) |

---

## Related commands

- [`/data-analyze`](data-analyze.md) — generate the results that go into the paper
- [`/review`](review.md) — peer review a colleague's paper using the same eight-area methodology
- [`/poster`](poster.md) — the conference poster for the same results
- [`/output`](output.md) — archive data and code before `--submit` claims availability
