---
name: phase-paper-write
description: Phase guidance for the neuroflow /paper-write command. Loaded automatically when /paper-write is invoked to orient agent behavior, relevant skills, and workflow hints for the paper-write phase.
---

# phase-paper-write

The paper-write phase generates a manuscript draft from analysis results, figures, and project memory accumulated across all prior phases.

## Approach

- Read upstream phase flows (ideation, data-analyze, experiment) before drafting — pull facts from memory, not from recall
- Confirm the target journal before writing; it determines structure, length, and style
- Draft section by section in logical order; write the abstract last
- Distinguish what the results show from what they mean — keep interpretation in Discussion

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Journal recommendation

If the user has not set a target journal and requests recommendations:

1. Read `project_config.md` for modality, research question, and tools.
2. Read `.neuroflow/ideation/` if it exists for topic keywords and collected literature.
3. Use the `neuroflow:scholar` agent to search PubMed and bioRxiv for recent papers (past 3 years) in the same area. A journal is considered recurring if it appears in at least 3 of the top 20 results.
4. Rank 3–5 candidate journals using these criteria (in order of priority):
   - **Scope alignment** — does the journal publish this modality and methodology?
   - **Paper type fit** — empirical, methods, review, brief communication?
   - **Open access** — required, preferred, or irrelevant for this project?
   - **Typical length** — does the journal's word-count range suit the planned manuscript?
   - **Prestige vs. speed** — balance impact factor with typical time-to-decision
5. Present the shortlist in priority order. For each journal: name, publisher, one-sentence scope, why it fits this project, notable constraints (page limits, OA fees, data sharing policy).
6. Ask the user to pick or skip. If they pick, write `target_journal: <name>` to `project_config.md`. Also write it to `.neuroflow/paper-write/flow.md` only if that file already exists — do not create the folder or file.

## Workflow hints

- The manuscript draft goes to `output_path` (`manuscript/`), not inside `.neuroflow/`
- Save `manuscript-plan.md` to `.neuroflow/paper-write/` with journal target, section outline, and author list
- Log any framing or scope decisions that differ from the original research question in `.neuroflow/reasoning/paper-write.json`

## Slash command

`/neuroflow:paper-write` — runs this workflow as a slash command.
