---
title: /ideation
---

# `/neuroflow:ideation`

**The very beginning of a research project.**

`/ideation` helps you brainstorm a research question, explore the literature, formalize an existing idea into a project definition, or produce a project proposal document. It's the natural next step after `/neuroflow` for a new project.

---

## When to use it

- You have a vague idea and need to think through research questions
- You want to search what is already known before committing to a question
- You have an idea and want to sharpen it into a concrete, testable research question
- You want to produce a written project proposal
- You have a set of papers and want a structured, critic-checked literature review

---

## Entry points

When you run `/neuroflow:ideation`, Claude asks which mode applies:

=== "1. Brainstorm"

    You have a vague idea. Claude helps you narrow it down to a testable research question.

    **What Claude does:**
    - Asks you to describe your idea in any form
    - Helps identify key variables (independent, dependent, confounds)
    - Identifies population and modality
    - Formulates a clear hypothesis statement

    **Output:** `research-question.md` saved to `.neuroflow/ideation/`

    **Example:**
    ```
    You: I'm interested in how background noise affects EEG-based attention measures.

    Claude: Let me help you narrow this down. What kind of attention are you 
            measuring — sustained, selective, or divided?

    You: Selective attention — I want to look at P300 amplitude differences.

    Claude: Good. Here's a draft research question:

            "Does white noise background (65 dB) reduce P300 amplitude during 
             a visual oddball task compared to silence in healthy adults?"

            Key variables:
            - Independent: noise condition (noise vs. silence)
            - Dependent: P300 amplitude and latency
            - Confounds: hearing threshold, fatigue, time of day
    ```

=== "2. Explore literature"

    Search PubMed and bioRxiv simultaneously using the inline [search protocol](../skills/phase-ideation/references/search-protocol.md) (no sub-agent spawned), with CrossRef, Semantic Scholar and arXiv as fallbacks.

    !!! note "No credentials required"
        PubMed and bioRxiv search works out of the box — no setup needed.

    **What Claude does:**
    - Runs your topic on both PubMed and bioRxiv, then CrossRef / Semantic Scholar / arXiv when bioRxiv coverage is thin
    - Tries synonym and broader/narrower queries if results are thin
    - Returns a deduplicated list with ⚠️ preprint and 🔒 paywall markers
    - Saves a metadata stub per paper; each DOI is labelled with the check actually done (for example "from the PubMed record" or "resolves on 2026-10-07"), never "verified"
    - Downloads only the papers you pick, and only open-access copies (preprint servers, open repository copies, publisher open access) — never Sci-Hub. For the rest it tells you which PDFs to get through your library and where to save them
    - Offers follow-up: literature review, save as markdown, synthesize, or watch the query

    !!! tip "Keep following a topic"
        Choose **watch** to pin a query in `.neuroflow/ideation/watch.md`. Claude recommends a free PubMed alert ("Create alert") and bioRxiv / medRxiv subject alerts; when a pinned query has not been checked for a week, `/ideation` offers to re-run it and shows only the new papers — they join your paper set only if you pick them.

    !!! note "Zotero (optional)"
        With a Zotero MCP server connected, Claude searches your library first and skips papers you already have. It writes to Zotero (collections, notes, tags) only when you confirm each write.

    **Output:** `literature-[topic]-[date].md` saved to `.neuroflow/ideation/`

    **Example output:**
    ```
    PubMed results (5 papers)
    ─────────────────────────
    **N2 and P300 in auditory attention** (2023) — Smith et al.
    *NeuroImage* | DOI: 10.1016/j.neuroimage.2023.001
    Shows P300 amplitude reduces with cognitive load in selective attention tasks.

    bioRxiv results (2 papers)
    ──────────────────────────
    **Noise effects on ERP** (2024) — Jones et al.
    *bioRxiv* | DOI: 10.1101/2024.001
    ⚠️ PREPRINT

    Summary: The literature consistently shows P300 attenuation under high 
    cognitive load. White noise as a stressor is understudied — gap identified.
    ```

=== "3. Formalize"

    You have an idea. Claude sharpens it into a precise, testable research question.

    Similar to Brainstorm but focused: Claude takes your existing idea and pressure-tests it for clarity, testability, and novelty.

=== "4. Proposal"

    Produce a structured project proposal document.

    **Sections:**
    - Research question
    - Background (from your literature)
    - Hypothesis
    - Planned methods
    - Population and modality
    - Rough timeline

    **Output:** `proposal-[date].md` saved to `.neuroflow/ideation/`

=== "5. Literature review"

    Run 12 analytical protocols — intake, contradictions, gaps, timeline, methods, citation network, review prose, devil's advocate, theory, variables, plain language, research agenda — on the papers in `.neuroflow/ideation/papers/` (PDFs or metadata stubs).

    **What Claude does:**
    - Confirms the paper list with you, then runs the `literature-review` agent
    - The agent checks every protocol with a critic pass (its rubric, countable items first) — a self-check, labelled as such — and saves each protocol as a checkpoint, so an interrupted review resumes where it stopped
    - Shows a status table (approved or halted per protocol); on request, a separate critic agent re-checks a protocol against the paper files

    **Output:** `literature-review-[date].md` in `.neuroflow/ideation/`, with per-protocol checkpoints in `literature-review-[date]/`

---

## Integration reminders

**PubMed / bioRxiv** — no credentials required, works out of the box.

**Miro** — if you mention Miro or ask to visualize a mind map, Claude checks `MIRO_ACCESS_TOKEN` and offers to configure it if missing.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/ideation/flow.md`, `.neuroflow/ideation/watch.md`, `.neuroflow/integrations.json`, `~/.neuroflow/user.yaml` |
| Writes | `.neuroflow/ideation/` (including `papers/`, `watch.md`, `literature-review-[date].md`), `.neuroflow/ideation/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md`, `~/.neuroflow/user.yaml` (your Zotero answer) |

---

## Related commands

- [`/grant-proposal`](grant-proposal.md) — write a formal grant application after ideation
- [`/experiment`](experiment.md) — design the paradigm once the research question is clear
- [`/data-analyze`](data-analyze.md) — run analysis with results tied back to your hypothesis
