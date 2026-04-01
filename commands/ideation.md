---
name: ideation
description: The very beginning of a research project — brainstorm a research question, explore literature via the scholar agent, formalize an existing idea into a project definition, or produce a project proposal document.
phase: ideation
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/ideation/flow.md
  - .neuroflow/integrations.json
  - skills/phase-ideation/SKILL.md
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
5. **Literature review** — papers have been retrieved (automatically downloaded by `scholar`, or manually placed in `.neuroflow/ideation/papers/`) and the user wants to run the full 12-protocol analysis

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

**Before searching**, check integration credentials:

1. Read `.neuroflow/integrations.json` if it exists.
2. Check whether `PUBMED_EMAIL` is set (either in the file or as an env var).
3. If `PUBMED_EMAIL` is **not** configured, show this reminder before proceeding:

> ⚠️ **PubMed not configured.**
> The PubMed MCP server requires a `PUBMED_EMAIL` to query the NCBI API. Without it, PubMed searches will fail.
>
> Would you like to set it up now?
> - **Y** — run `/neuroflow:setup` to configure credentials, then continue the literature search
> - **n** — skip; I'll attempt bioRxiv only (no email required)

If the user chooses Y: run the PubMed section of the setup wizard — specifically Step 2 (prompt for email) and Step 4 (save to integrations.json) from `commands/setup.md` — then continue here.
If the user skips: proceed using bioRxiv only, and note PubMed results will be unavailable.

Run searches directly: call `search_pubmed`, then `search_biorxiv`, then `search_crossref` sequentially — do NOT spawn the `scholar` subagent. Use the user's topic as the starting query, then try synonyms and broader/narrower terms if first results are thin.

After collecting results, download papers via Bash `curl` in batches of 3. Try open-access URLs first (Frontiers, PLoS, eNeuro, PMC), then Sci-Hub as fallback (fetch page → extract PDF URL → download).

After all downloads complete, run `/compact` to clear context before continuing.

Save the search result list as `literature-[topic]-[date].md` in `.neuroflow/ideation/`.

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

**PubMed / bioRxiv** — checked before any literature search (see "Explore literature" step above).

**Miro** — if the user mentions Miro, asks to visualise a mind map, or wants to export ideas to a board:
1. Read `.neuroflow/integrations.json` and check whether `MIRO_ACCESS_TOKEN` is set.
2. If not configured, show:

> ⚠️ **Miro not configured.**
> To use Miro you need a personal access token stored in `MIRO_ACCESS_TOKEN`.
>
> Would you like to set it up now?
> - **Y** — run `/neuroflow:setup` to configure the Miro token, then continue
> - **n** — skip Miro; I'll describe what would be created instead
