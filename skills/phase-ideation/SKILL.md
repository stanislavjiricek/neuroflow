---
name: phase-ideation
description: Phase guidance for the neuroflow /ideation command. Loaded automatically when /ideation is invoked to orient agent behavior, relevant skills, and workflow hints for the ideation phase.
---

# phase-ideation

The ideation phase is the entry point of a research project — sharpening a vague idea into a testable research question and mapping the existing literature rigorously.

## Approach

- Identify which entry point applies (brainstorm, literature explore, formalize, proposal, literature review) before doing anything else
- Resist generating a full proposal before the research question is clear — sequence matters
- Use the `scholar` agent for any literature search; do not search manually
- The `scholar` agent runs searches **sequentially**: PubMed → bioRxiv → fallbacks (CrossRef → Semantic Scholar → arXiv) one at a time. Never fires sources simultaneously — this prevents API freezes on custom providers.
- The `scholar` agent downloads papers in **batches of 2** — completes each batch before starting the next
- The `scholar` agent always attempts to download papers automatically to `.neuroflow/ideation/papers/` — do not wait for the user to request downloads
- After papers are downloaded, use the `literature-review` agent to run the full 12-protocol analysis
- Keep outputs hypothesis-driven and concise; avoid scope creep at this stage
- If `project_config.md` already has a research question, confirm whether to refine or restart

## Relevant agents

- `scholar` — searches PubMed and bioRxiv; automatically downloads open-access papers to `.neuroflow/ideation/papers/`
- `literature-review` — runs 12 sequential analytical protocols on downloaded papers through the worker-critic loop; produces a compiled literature review saved to `.neuroflow/ideation/literature-review-[date].md`
- `critic` — evaluates each protocol output in the literature-review loop
- `orchestrator` — manages the worker-critic loop when invoked

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules
- `neuroflow:pupil-labs-neon-realtime` — if the project involves Pupil Labs Neon eye-tracking hardware, use this skill for real-time data collection and device connection during ideation/piloting

## Workflow hints

- The research question produced here anchors every downstream phase — write it precisely
- Save the final research question to `.neuroflow/ideation/research-question.md`
- Update `project_config.md` if the research question is defined or changed
- Downloaded papers live in `.neuroflow/ideation/papers/` — this folder is the input for the `literature-review` agent
- The compiled literature review (`literature-review-[date].md`) feeds directly into the `paper` phase; reference it there
- When using the `scholar` agent for a literature search, it reads `skills/phase-ideation/references/journal-defaults.md` to match the query to one of eight neuroscience areas and surface high-impact journals. If the user has custom journal preferences, they can create `.neuroflow/journal-preferences.md` from the template at `skills/phase-ideation/references/user-journal-preferences.md`.

## Slash command

`/neuroflow:ideation` — runs this workflow as a slash command.
