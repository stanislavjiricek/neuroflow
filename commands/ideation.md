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

Use the `scholar` agent to search PubMed and bioRxiv for relevant papers. Use the user's topic as the starting query, then try synonyms and broader/narrower terms if first results are thin.

Save the output as `literature-[topic]-[date].md` in `.neuroflow/ideation/`.

### Proposal

Produce a structured project proposal document covering: research question, background (from literature), hypothesis, planned methods, population, modality, timeline (rough). Save as `proposal-[date].md` in `.neuroflow/ideation/`.

---

## At end

- Update `.neuroflow/ideation/flow.md` with any new files created
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
