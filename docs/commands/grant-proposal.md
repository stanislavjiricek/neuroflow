---
title: /grant-proposal
---

# `/neuroflow:grant-proposal`

**Write a full grant application.**

`/grant-proposal` helps you draft a grant application from scratch or based on an existing project proposal from `/ideation`. It adapts to the requirements of any funding body — NIH, ERC, national schemes, or institutional grants.

---

## When to use it

- You need to write a funding application for your study
- You want to formalize your research idea into a grant-ready document
- You have an existing proposal from `/ideation` and want to expand it into a full application

---

## What it does

Claude reads your project memory (`.neuroflow/ideation/`) and then asks:

1. **Which funding body / scheme?** (e.g. NIH R01, ERC Starting Grant, GAČR, institutional)
2. **Page/word limit and required sections?**
3. **Existing proposal or research question to build from?**

It then produces the grant document section by section, adapted to the target funder's requirements.

---

## Standard sections

| Section | Description |
|---|---|
| **Specific aims** | What you will do and why it matters — typically 1 page |
| **Significance** | The scientific problem and why solving it matters |
| **Innovation** | What is new or different about your approach |
| **Approach** | Methods, timeline, expected outcomes, limitations and alternatives |
| **Budget** | Personnel, equipment, consumables — Claude asks you for the numbers |
| **Timeline** | Milestones mapped to the funding period |

!!! tip "Funder-specific adaptation"
    neuroflow adapts section names, word limits, and structure to match your target funder. Just tell Claude which scheme you're applying to.

---

## Example session

```
/neuroflow:grant-proposal
```

```
Claude: I found your research question from /ideation:
        "Does white noise reduce P300 amplitude in a visual oddball task?"

        Which funding body / scheme are you applying to?

You: GAČR (Czech Science Foundation) — standard project, 3 years

Claude: GAČR standard project. Budget limit is approximately 5M CZK over 3 years.
        Required sections: Project summary, State of the art, Objectives, 
        Methodology, Feasibility, Budget justification, Timeline.

        Let me start with the Project summary...
```

---

## Output

The completed grant document is saved as `grant-[funder]-[date].md` in `.neuroflow/grant-proposal/`.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/ideation/flow.md`, `.neuroflow/grant-proposal/flow.md` |
| Writes | `.neuroflow/grant-proposal/`, `.neuroflow/grant-proposal/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md` |

---

## Related commands

- [`/ideation`](ideation.md) — formalize your research question first
- [`/experiment`](experiment.md) — design the paradigm that goes into the methods section
- [`/write-report`](write-report.md) — generate a progress report for funders
