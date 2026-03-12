---
name: phase-lit-review
description: Phase guidance for the neuroflow /lit-review command. Loaded automatically when /lit-review is invoked to orient agent behavior, relevant skills, and workflow hints for structured post-retrieval literature corpus analysis.
---

# phase-lit-review

The lit-review phase takes a set of already-retrieved papers and applies structured analytical protocols to synthesise findings, surface contradictions, map knowledge gaps, and draft a literature review section. It sits between paper retrieval (done by `/ideation` or the `scholar` agent) and writing (done by `/paper-write`).

## Approach

- Do not retrieve papers in this phase — that is `/ideation`'s job
- Always ask the user where the papers are before starting any protocol
- Confirm the research topic (from `project_config.md` or user input) before running
- Default to running all 12 protocols unless the user specifies otherwise
- Delegate all protocol execution to `neuroflow:lit-review-protocols` — do not implement protocol logic here
- Run protocols in order (1 → 12) unless the user requests a specific subset or single protocol

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules
- `neuroflow:lit-review-protocols` — the 12 analytical protocols; delegate to this skill for all analysis

## Workflow hints

- The Intake Protocol (1) is always required before any other protocol — it builds the index all other protocols reference
- The Lit Review Writer (7) produces the most directly usable output for manuscript writing; run it last
- For quick synthesis, recommend protocols 1, 2, 3, and 7 as the minimum useful set
- Save outputs to `.neuroflow/ideation/` so they are available to `/paper-write` and `/grant-proposal` without any extra steps
- If the user has many papers (20+), suggest running the Methodology Auditor (5) and Citation Network Map (6) first to reduce the corpus before running the full suite

## Output conventions

| Protocol run | Output file |
|---|---|
| All 12 | `lit-review-[date].md` |
| Single protocol | `lit-review-[protocol-name]-[date].md` |
| Custom subset | `lit-review-custom-[date].md` |

All outputs go to `.neuroflow/ideation/`.

## Slash command

`/neuroflow:lit-review` — runs this workflow as a slash command.
