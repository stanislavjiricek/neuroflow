---
name: ideation
description: The very beginning of a research project — brainstorm a research question, explore literature inline (no sub-agents), formalize an existing idea into a project definition, or produce a project proposal document.
phase: ideation
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/ideation/flow.md
  - .neuroflow/integrations.json
  - skills/phase-ideation/SKILL.md
  - skills/phase-ideation/references/search-protocol.md
writes:
  - .neuroflow/ideation/
  - .neuroflow/ideation/papers/
  - .neuroflow/ideation/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /ideation

Read the `neuroflow:phase-ideation` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/ideation/flow.md` before starting.

## What this command does

Handles the very beginning of a research project. Four possible entry points — ask the user which applies:

1. **Brainstorm** — the user has a vague idea and wants to think through research questions
2. **Explore literature** — the user wants to search what is already known before committing to a question
3. **Formalize** — the user has an idea and wants to sharpen it into a concrete, testable research question
4. **Proposal** — the user wants to produce a written project proposal document
5. **Literature review** — papers have been retrieved (via the inline search protocol, or manually placed in `.neuroflow/ideation/papers/`) and the user wants to run the full 12-protocol analysis

If `project_config.md` already has a research question, confirm whether they want to build on it or start fresh.

---

## Steps

### Brainstorm / Formalize

Ask the user to describe their idea in any form — a phenomenon they want to study, a method they want to apply, a gap they noticed. Then:

1. Help them narrow it down to a testable research question
2. Identify the key variables (independent, dependent, confounds)
3. Identify the population and modality
4. State the hypothesis in one clear sentence

Save the result as `research-question.md` in `.neuroflow/ideation/`.

### Explore literature

Perform the literature search **directly — do NOT spawn a sub-agent**. Read and follow `skills/phase-ideation/references/search-protocol.md` step by step:

1. Run the MCP health check (Step 0 of the protocol)
2. Execute PubMed and bioRxiv searches in parallel, with CrossRef/Semantic Scholar/arXiv fallbacks as needed
3. Deduplicate results and emit the coverage summary table
4. Present the results list in the output format defined in the protocol
5. Save a `.md` metadata stub for every result to `.neuroflow/ideation/papers/` automatically
6. Ask the user which papers to download for full-text analysis (`1,3,5`, `all`, or `skip`)
7. If the user selects papers, follow the download procedure in the protocol (batches of 2, with resume detection)
8. After downloads complete (or are skipped), offer follow-up actions: literature-review, save, or summarize

All search logic, output formats, stub templates, resume detection, and download procedures are defined in the search protocol reference — follow them exactly.

### Literature review

After papers have been retrieved and downloaded, run the full 12-protocol literature review using the `literature-review` agent:

1. Confirm the contents of `.neuroflow/ideation/papers/` with the user
2. Invoke the `literature-review` agent — it will run all 12 analytical protocols through the worker-critic loop automatically
3. The agent saves the compiled review to `.neuroflow/ideation/literature-review-[date].md`

The 12 protocols the `literature-review` agent runs:

1. **Intake Protocol** — map every paper by author + year + core claim; cluster by shared assumptions; flag contradictions
2. **Contradiction Hunter** — expose every head-to-head conflict between papers with evidence assessment
3. **Knowledge Gap Detector** — identify what all papers assume but never prove; missing methodologies; missing populations
4. **Timeline Builder** — reconstruct the intellectual history of the field from these papers alone
5. **Methodology Auditor** — extract study designs, sample sizes, and limitations; name what the dominant method cannot prove
6. **Citation Network Map** — identify which paper everything else builds on and which is the field's Achilles heel
7. **Lit Review Writer** — produce the prose literature review (opening → thematic body → transition → close)
8. **Devil's Advocate** — build the strongest case against the dominant consensus using the papers themselves
9. **Theoretical Framework Extractor** — map all theoretical models in use; name the missing lens
10. **Variable Map** — inventory every IV/DV/moderator; surface the never-studied variable combination
11. **Plain Language Translator** — rewrite the 5 most complex findings for a non-academic audience; identify the best headline
12. **Future Research Agenda** — write a 5-point agenda grounded in gaps, contradictions, and unreplicated variables

### Proposal

Produce a structured project proposal document covering: research question, background (from literature), hypothesis, planned methods, population, modality, timeline (rough). Save as `proposal-[date].md` in `.neuroflow/ideation/`.

---

## At end

- Update `.neuroflow/ideation/flow.md` with any new files created (including files in `papers/` and the compiled literature review)
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- If a research question was defined or updated, update `project_config.md`

---

## Integration reminders

Apply these checks at the points indicated above and whenever the user explicitly requests an integration:

**PubMed / bioRxiv** — available out of the box. No setup required.

**Miro** — if the user mentions Miro, asks to visualise a mind map, or wants to export ideas to a board:
1. Read `.neuroflow/integrations.json` and check whether `MIRO_ACCESS_TOKEN` is set.
2. If not configured, show:

> ⚠️ **Miro not configured.**
> To use Miro you need a personal access token stored in `MIRO_ACCESS_TOKEN`.
>
> Would you like to set it up now?
> - **Y** — run `/neuroflow:setup` to configure the Miro token, then continue
> - **n** — skip Miro; I'll describe what would be created instead
