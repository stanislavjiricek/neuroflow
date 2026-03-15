---
name: phase-paper
description: Phase guidance for the neuroflow /paper command. Loaded automatically when /paper is invoked to orient agent behavior, relevant skills, and workflow for the unified paper phase — covering manuscript drafting and rigorous internal peer review in a single write→critique loop.
---

# phase-paper

The paper phase produces a reviewed and approved neuroscience manuscript. Every section draft is subjected to a brutal `paper-writer` → `paper-critic` loop before it is saved. Nothing reaches disk without critic approval or an explicit user decision to accept an unresolved draft.

## Approach

- Read upstream phase flows (ideation, data-analyze, experiment) before drafting — pull facts from memory, not from recall
- Confirm target journal before writing any section; it determines structure, length, style, and the critic's review persona
- Draft section by section in logical order; write the abstract last
- Distinguish what the results show (Results) from what they mean (Discussion) — flag if they become conflated
- Every section draft is routed through the `paper-critic` agent using the full eight-area `neuroflow:review-neuro` methodology before saving
- Nothing is saved to `output_path` without a `[STATUS: APPROVED]` verdict or explicit user acceptance of an unresolved draft

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules
- `neuroflow:worker-critic` — defines the multi-agent revision loop protocol (max 3 iterations per section)
- `neuroflow:review-neuro` — the eight-area review methodology used by the `paper-critic` agent on every draft
- `neuroflow:notebooklm` — use when the user wants a podcast, slide deck, or infographic generated from manuscript sections

## Two-agent write→critique loop

The loop runs section by section, strictly following the `neuroflow:worker-critic` protocol:

1. **paper-writer** receives the task, upstream memory, journal target, and rubric — drafts the section
2. **paper-critic** receives the draft and rubric — applies the full six-area `review-neuro` methodology — returns `[STATUS: APPROVED]` or `[STATUS: REJECTED]` with specific actionable feedback
3. On `REJECTED`: **paper-writer** receives the draft and the critic's feedback — revises, addressing each bullet specifically
4. Loop repeats until `APPROVED` or three iterations are exhausted

On the third rejection the loop halts. The orchestrator presents draft v3 and the unresolved critique to the user, appends the critique to `.neuroflow/paper/critic-log.md`, and asks whether to continue with the next section.

## Critic standards

The `paper-critic` agent applies the FULL eight-area `neuroflow:review-neuro` methodology to every draft — including partial section drafts. The eight areas are:

1. **Language, Style & Terminology** — spelling, grammar, notation, neuroscience terminology errors, causality language
2. **Internal Consistency & Cross-Reference Integrity** — figure/table references, value consistency across sections
3. **Claim Support, Causality Language & Connectivity Interpretation** — overclaims, causality creep, FC over-interpretation
4. **Statistics, Network Inference & Multiple Comparisons** — effect sizes, correction procedures, null models, estimator specification
5. **Methods Reproducibility, Reporting Standards & Open Science** — COBIDAS/ARRIVE compliance, data/code availability
6. **Contribution, Novelty & Journal Fit** — novelty assessment, prior work comparison, journal fit, referee recommendation
7. **Literature Gap** — whether key prior work is cited; uses Zotero or `.neuroflow/ideation/papers/` as reference database
8. **Figure Review** — colormaps, font sizes, caption completeness, axis labels, figure–text consistency

A section is approved only if it would survive peer review at a top-tier neuroscience journal. The bar is not "acceptable draft" — it is "ready for submission".

## Journal recommendation

If the user has not set a target journal and requests recommendations:

1. Read `project_config.md` for modality, research question, and tools.
2. Read `.neuroflow/ideation/` if it exists for topic keywords and collected literature.
3. Use the `scholar` agent to search PubMed and bioRxiv for recent papers (past 3 years) in the same area. A journal is considered recurring if it appears in at least 3 of the top 20 results.
4. Rank 3–5 candidate journals using these criteria (in order of priority):
   - **Scope alignment** — does the journal publish this modality and methodology?
   - **Paper type fit** — empirical, methods, review, brief communication?
   - **Open access** — required, preferred, or irrelevant for this project?
   - **Typical length** — does the journal's word-count range suit the planned manuscript?
   - **Prestige vs. speed** — balance impact factor with typical time-to-decision
5. Present the shortlist in priority order. For each journal: name, publisher, one-sentence scope, why it fits this project, notable constraints (page limits, OA fees, data sharing policy).
6. Ask the user to pick or skip. If they pick, write `target_journal: <name>` to `project_config.md` — this is the authoritative location. Also write it to `.neuroflow/paper/flow.md` only if that file already exists — do not create the folder or file.

## Output paths

| What | Where |
|---|---|
| Approved section drafts, final manuscript | `output_path` (default: `manuscript/`) — outside `.neuroflow/` |
| Phase memory, plans, critic logs | `.neuroflow/paper/` |
| Critic loop state per section | `.neuroflow/paper/critic-log.md` |
| Scope and framing decisions | `.neuroflow/reasoning/paper.json` |

Log any framing or scope decisions that differ from the original research question in `.neuroflow/reasoning/paper.json` — ask before writing.

## Slash command

`/neuroflow:paper` — runs this workflow as a slash command.
