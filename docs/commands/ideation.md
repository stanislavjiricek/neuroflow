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

    Search PubMed and bioRxiv simultaneously using the [scholar agent](../concepts/agents.md).

    !!! note "PubMed credential required"
        Before searching, Claude checks whether `PUBMED_EMAIL` is configured.
        If not, it offers to run `/setup` or proceed with bioRxiv only.

    **What Claude does:**
    - Runs your topic on both PubMed and bioRxiv
    - Tries synonym and broader/narrower queries if results are thin
    - Returns a deduplicated list with ⚠️ preprint and 🔒 paywall markers
    - Offers follow-up: download, save as markdown, or synthesize

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

---

## Integration reminders

**PubMed / bioRxiv** — checked before any literature search. If `PUBMED_EMAIL` is missing, Claude offers to configure it before proceeding.

**Miro** — if you mention Miro or ask to visualize a mind map, Claude checks `MIRO_ACCESS_TOKEN` and offers to configure it if missing.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/ideation/flow.md`, `.neuroflow/integrations.json` |
| Writes | `.neuroflow/ideation/`, `.neuroflow/ideation/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md` |

---

## Related commands

- [`/grant-proposal`](grant-proposal.md) — write a formal grant application after ideation
- [`/experiment`](experiment.md) — design the paradigm once the research question is clear
- [`/data-analyze`](data-analyze.md) — run analysis with results tied back to your hypothesis
