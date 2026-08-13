---
name: phase-ideation
description: Phase guidance for the neuroflow /ideation command. Loaded automatically when /ideation is invoked to orient agent behavior, relevant skills, and workflow hints for the ideation phase.
---

# phase-ideation

The ideation phase is the entry point of a research project — sharpening a vague idea into a testable research question and mapping the existing literature rigorously.

## Approach

- Identify which entry point applies (brainstorm, literature explore, formalize, proposal, literature review) before doing anything else
- Resist generating a full proposal before the research question is clear — sequence matters
- Perform all literature searches **inline** by following `skills/phase-ideation/references/search-protocol.md` — do NOT spawn sub-agents
- Save `.md` metadata stubs for all results and ask the user which papers to download
- After the user selects papers (or skips), use the `literature-review` agent to run the full 12-protocol analysis
- The literature-review agent works from PDFs or `.md` stubs — full download is not required
- Keep outputs hypothesis-driven and concise; avoid scope creep at this stage
- If `project_config.md` already has a research question, confirm whether to refine or restart

## Relevant agents

- `literature-review` — runs 12 sequential analytical protocols on downloaded papers through the worker-critic loop; produces a compiled literature review saved to `.neuroflow/ideation/literature-review-[date].md`. The loop protocol is defined in `neuroflow:worker-critic` — the orchestrator is the current Claude instance and the critic role is played inline, not by separate agent files.

> **Note:** Literature searches are performed inline by the main agent following the search protocol — the `scholar` agent is NOT spawned as a sub-agent. Use the standalone `scholar` agent only for ad-hoc searches outside the `/ideation` workflow.

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules
- `neuroflow:pupil-labs-neon-realtime` — if the project involves Pupil Labs Neon eye-tracking hardware, use this skill for real-time data collection and device connection during ideation/piloting

## Zotero integration (optional)

If a Zotero MCP server is connected (any `mcp__*zotero*` tools available), the literature workflow becomes **library-first**: search the user's Zotero library before external sources, mark already-owned papers 📚 in results (excluded from download offers), offer to save newly selected papers into a project-named Zotero collection, and let the literature review pull the user's existing Zotero notes/annotations. If no Zotero MCP is present, `/ideation` asks once per project whether to set one up (answer stored as `zotero:` in `project_config.md`; setup guidance lives in `/setup`). Never require Zotero — the plain stub-based flow is always the fallback.

## Workflow hints

- The research question produced here anchors every downstream phase — write it precisely
- Save the final research question to `.neuroflow/ideation/research-question.md`
- Update `project_config.md` if the research question is defined or changed
- Downloaded papers live in `.neuroflow/ideation/papers/` — this folder is the input for the `literature-review` agent
- The compiled literature review (`literature-review-[date].md`) feeds directly into the `paper` phase; reference it there
- The search protocol reads `skills/phase-ideation/references/journal-defaults.md` to match the query to one of eight neuroscience areas and surface high-impact journals. If the user has custom journal preferences, they can create `.neuroflow/journal-preferences.md` from the template at `skills/phase-ideation/references/user-journal-preferences.md`.

## Slash command

`/neuroflow:ideation` — runs this workflow as a slash command.
