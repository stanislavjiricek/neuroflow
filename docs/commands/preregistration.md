---
title: /preregistration
---

# `/neuroflow:preregistration`

**Create and manage pre-registration documents.**

`/preregistration` helps you commit your study design, hypotheses, and analysis plan to a public registry before data collection begins — and manage any subsequent deviations from that plan.

---

## When to use it

- You want to pre-register your study on OSF or AsPredicted
- You want to check an existing pre-registration for completeness and internal consistency
- A deviation from the pre-registered plan occurred and needs to be logged
- You want to record the details of a submitted or accepted registered report

---

## What it does

Claude reads your project memory (`.neuroflow/ideation/` and `.neuroflow/experiment/`) for the research question, hypothesis, and paradigm details, then asks which mode applies:

1. **Draft pre-registration** — produce a complete pre-registration for OSF, AsPredicted, or a registered report journal
2. **Review pre-registration** — check an existing document for completeness and consistency
3. **Deviation log** — record and justify any post-registration change to the plan
4. **Link registered report** — record the DOI, URL, or registry ID of a submitted or accepted registered report
5. **Freeze** — hash-lock the final pre-registration so the local copy cannot drift from what was registered

---

## Draft pre-registration

Claude asks which registry and template you are targeting:

=== "OSF (standard)"

    Covers all required OSF preregistration fields:

    | Section | Content |
    |---|---|
    | **Title & authors** | Project title and team |
    | **Description** | Study overview |
    | **Hypotheses** | Directional, falsifiable predictions |
    | **Design** | Variables, conditions, randomisation, blinding |
    | **Participants** | Population, sample size, inclusion/exclusion, power calculation |
    | **Procedure** | Timeline, instruments, paradigm |
    | **Measures** | Operationalisation of each variable |
    | **Analysis plan** | Statistical tests, correction strategy, missing data handling |
    | **Exploratory analyses** | Clearly labelled non-confirmatory tests |
    | **Data sharing** | Availability and access plan |

=== "AsPredicted"

    Covers the six AsPredicted fields:

    1. Hypothesis and study question
    2. Dependent variable(s)
    3. Conditions
    4. Analyses
    5. Outliers and exclusions
    6. Sample size and rationale

=== "Registered report"

    Structured for stage 1 submission to a journal. Claude asks for the target journal's specific section requirements.

Every draft ends with a small machine-readable block (`yaml prereg-parameters`) that restates the plan: planned N, stopping rule, alpha, filters, epoch and baseline windows, ROIs, tests, exclusions, and the allocation seed if orders are counterbalanced. Later phases compare the analysis against it without parsing prose; the registered text stays authoritative.

**Output:** `prereg-[registry]-[date].md` saved to `.neuroflow/preregistration/`

---

## Review pre-registration

Claude reads your existing pre-registration document and checks:

- Is the hypothesis directional and falsifiable?
- Are all analysis steps fully specified?
- Is the sample size justified by a power calculation?
- Are exclusion and missing-data rules defined before data collection?
- Are exploratory analyses clearly distinguished from confirmatory ones?
- Is there any ambiguity that could allow selective reporting?

**Output:** `prereg-review-[date].md` saved to `.neuroflow/preregistration/`

---

## Deviation log

When something changes after registration, Claude records:

- What was pre-registered
- What actually happened
- Why the deviation occurred
- How it affects interpretation of results

**Output:** appended to `deviations.md` in `.neuroflow/preregistration/` (never overwritten)

---

## Freeze

Once the pre-registration is final — at the latest when it goes to the registry — Claude shows what would be frozen and freezes it only after you confirm in that turn. `freeze.py` then:

- records the SHA-256 of each frozen file, the registry, DOI and planned N in the frontmatter of `.neuroflow/preregistration/status.md` (`status: frozen`, `set_by: person`)
- puts a banner on the first line of each frozen file, visible to collaborators in any editor: `> FROZEN 2026-10-01 — sha256 3f5a… — do not edit; record changes in deviations.md`

`freeze.py verify` re-checks the hashes at any time (line endings and the banner do not count, so Windows and macOS copies agree). From then on the frozen files are never edited — every change goes to `deviations.md`. Unfreezing, for example to fix a typo before submission, is your decision only; it is logged in `deviations.md` with the old hashes. With the neuroflow mod you can also freeze, verify and unfreeze from the integrity tab of [`/dashboard`](dashboard.md): a key press and an explicit yes, which the model cannot give on your behalf. The registry copy remains the public record.

---

## Example session

```
/neuroflow:preregistration
```

```
Claude: I found your research question from /ideation:
        "Does white noise reduce P300 amplitude in a visual oddball task?"
        
        And paradigm details from /experiment.

        Which mode would you like?
        1. Draft pre-registration
        2. Review existing pre-registration
        3. Log a deviation
        4. Link a registered report
        5. Freeze the final pre-registration

You: 1

Claude: Which registry?
        1. OSF (standard)
        2. AsPredicted
        3. Registered report (journal submission)

You: 1 — OSF standard

Claude: Great. Let me start with the hypotheses section.
        The hypothesis I have from /ideation is:
        "White noise will reduce P300 amplitude compared to silence."
        Is this the directional prediction you want to register?
```

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/preregistration/flow.md`, `.neuroflow/ideation/flow.md`, `.neuroflow/experiment/flow.md` |
| Writes | `.neuroflow/preregistration/`, `.neuroflow/preregistration/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md` |

---

## Related commands

- [`/ideation`](ideation.md) — formalize your research question and hypothesis first
- [`/experiment`](experiment.md) — design the paradigm that goes into the methods section
- [`/data-analyze`](data-analyze.md) — run the pre-registered analysis plan after data collection
