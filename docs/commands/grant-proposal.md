---
title: /grant-proposal
---

# `/neuroflow:grant-proposal`

**Write a competitive, funder-ready grant application — from research question to full draft.**

`/grant-proposal` is the neuroflow command for writing complete grant applications. It automatically discovers your ideation outputs, fetches funder call documents from URLs, adapts its structure to the target funder, and drafts every section with word-count tracking and review-criteria alignment.

---

## When to use it

- You need to write a funding application for your neuroscience study
- You want to turn an ideation output into a full grant application
- You have a funder call URL or PDF and want Claude to parse the requirements
- You need to draft specific sections (Specific Aims, Approach, Budget) with expert guidance
- You want your draft checked against the funder's actual review criteria

---

## What it does — step by step

### Step 0: Discovers your research idea automatically

Before asking you anything, Claude checks `.neuroflow/ideation/` for existing research question documents. If it finds them:

```
I found your ideation output. Here's what I'll build the grant from:
• Research question: Does white noise reduce P300 amplitude in a visual oddball paradigm?
• Modality: EEG (64-channel, 1000 Hz)
• Population: Healthy adults, 18–35
• Preliminary data: Pilot N=8, effect size d=0.61 (SE=0.18)
• Key references: Polich (2007), Näätänen et al. (2018)

Is this the right idea to build the grant around?
```

If no ideation files exist, Claude asks you for the research question and offers to read a funder call URL.

### Step 1: Fetches and parses the funder call

Provide a URL to the funding call, or paste the call text. Claude extracts:

- Scheme name, budget ceiling, duration
- Page/word limits per section
- Required sections and order
- Review criteria
- Eligibility constraints
- Deadline
- Submission portal

Then confirms everything with you before drafting a single word.

### Step 2: Builds a proposal outline

Claude produces a structured outline adapted to the funder's requirements — with page budgets next to each section — and asks for your approval before proceeding.

### Step 3: Drafts section by section

Claude drafts one section at a time, showing:
- Which review criteria the section addresses
- Word/page count vs. the limit
- A menu of options after each section: revise / expand / next / save / checklist

### Step 4: Quality check

Before saving, Claude runs a quality checklist:
- Every aim is measurable
- Power analysis is present
- Limitations and alternatives are addressed
- All sections are within word/page limits
- Review criteria are explicitly addressed in the text

### Step 5: Saves to memory

The completed draft is saved as `grant-[funder]-[date].md` in `.neuroflow/grant-proposal/`. Funder, scheme, and deadline are logged to `project_config.md` with your confirmation.

---

## Supported funders

| Funder | Scheme | Typical budget | Duration |
|---|---|---|---|
| NIH | R01 | $500K DC/yr | 5 years |
| NIH | R21 | $275K total | 2 years |
| ERC | Starting Grant | €1.5M | 5 years |
| ERC | Consolidator Grant | €2M | 5 years |
| ERC | Advanced Grant | €2.5M | 5 years |
| Wellcome Trust | Discovery Award | £3–5M | 5 years |
| MRC | Programme Grant | £2–4M | 5 years |
| GAČR | Standard Project | ~5M CZK/yr | 3 years |
| DFG | Research Grants | €250K–1M | 3 years |
| Horizon Europe | EIC Pathfinder | €3M | 4 years |

!!! tip "Any funder works"
    If your funder is not in the table above, Claude will ask you for the requirements directly, or read a URL or PDF you provide.

---

## Neuroscience-specific expertise

`/grant-proposal` understands neuroscience methodology. When drafting the Approach section it asks for and includes:

| Modality | Detail included |
|---|---|
| EEG / ERP | Cap system, sampling rate, bandpass, epoch, ICA, software |
| fMRI / BOLD | TR, field strength, HRF, motion scrubbing, cluster correction |
| iEEG / SEEG | Electrode type, HFO analysis, reference scheme |
| Eye-tracking | Tracker model, fixation algorithm, AOI definition |
| ECG / HRV | R-peak detection, SDNN/RMSSD, artifact correction |
| Behaviour | Timing precision, counterbalancing, trial counts |

A **formal power analysis** is always included — using your pilot data or published effect sizes.

---

## Example session

```
/neuroflow:grant-proposal
```

```
Claude: I found your ideation output. Here's what I'll build the grant from:
        • Research question: Does white noise reduce P300 amplitude in a visual oddball task?
        • Modality: EEG (64-channel, BrainProducts actiCHamp)
        • Population: Healthy adults 18–35, N=40
        • Preliminary data: Pilot N=8, d=0.61
        • Key refs: Polich (2007), Näätänen et al. (2018)

        Is this the right idea to build the grant around?

You: Yes. Applying to GAČR Standard Project.

Claude: Do you have a URL to the current GAČR call for proposals?

You: https://gacr.cz/en/calls/2025-standard/

Claude: [reads URL]
        GAČR Standard Project 2025:
        • Budget: up to 5M CZK/year, 3 years
        • Sections: Project summary (600w CZ+EN), State of the art, Objectives,
          Methodology, Feasibility, Budget justification, Timeline
        • Review criteria: Scientific originality, Feasibility, Team qualifications, Budget
        • Deadline: October 15, 2025
        • Submission: GRIS portal

        Confirmed — shall I build the outline?

You: Yes

Claude: [produces outline with page budgets]

        Ready to draft Section 1: Project Summary (600 words)?

You: Go

Claude: [drafts Project Summary]

        Word count: 587 / 600  ✅

        Options: revise | expand [topic] | next | save | checklist
```

---

## Output files

| File | Location | Description |
|---|---|---|
| Grant draft | `.neuroflow/grant-proposal/grant-[funder]-[date].md` | Full application |
| Section drafts | `.neuroflow/grant-proposal/draft-[funder]-[date]-[section].md` | Per-section files during drafting |
| Flow index | `.neuroflow/grant-proposal/flow.md` | Funder, scheme, deadline, section status |
| Session log | `.neuroflow/sessions/YYYY-MM-DD.md` | Appended automatically |

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/ideation/flow.md`, `.neuroflow/grant-proposal/flow.md` |
| Writes | `.neuroflow/grant-proposal/`, `.neuroflow/grant-proposal/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md` |

---

## Related commands

- [`/ideation`](ideation.md) — define your research question first if you don't have one
- [`/experiment`](experiment.md) — design the paradigm that feeds into the Approach section
- [`/preregistration`](preregistration.md) — register your analysis plan; reference it in the grant
- [`/write-report`](write-report.md) — generate progress reports for funders after funding is secured
- [`/finance`](finance.md) — manage the awarded budget after the grant is funded
