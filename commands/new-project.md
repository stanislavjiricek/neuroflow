---
description: Start a new neuroflow project. Walks the user through a short interview and writes a .neuroflow/config.json config into their current working directory.
---
# /new-project

Guide the user through a short structured interview to understand their project context. At the end., write a `.neuroflow/config.json` file into their current working directory.

## Step 0 — Scan the current directory

Before asking anything, use Glob and Read to inspect what's already in the working directory:

1. Check if `.neuroflow/config.json` already exists — if it does, read it and tell the user what was found, then ask if they want to update it or start fresh. If they want to update, pre-fill all answers from the existing file and only ask about fields they want to change.

2. Scan the top-level directory structure. Look for signals that indicate project stage:

| What you find | Inferred signal |
|---|---|
| `sub-*/`, `dataset_description.json`, `participants.tsv` | BIDS dataset — likely "have data" |
| `*.py`, `*.m`, `*.R` analysis scripts | Processing underway — "have data" or "have results" |
| `derivatives/`, `results/`, `figures/` | Analysis done — likely "have results" |
| `*.tex`, `*.docx`, `manuscript/` | Draft exists — "have a draft" |
| `paradigm/`, `*.psyexp`, PsychoPy scripts | Paradigm design stage |
| Empty or only README | Fresh start — "idea / hypothesis" |

3. Summarise what you found in one short sentence before asking the first question. For example:

> "I can see a BIDS dataset with 12 subjects and some analysis scripts in `analysis/`. Looks like you're in the data analysis phase — does that sound right?"

Use this to skip or pre-answer questions where the repo already makes the answer obvious. Don't ask what you already know.

## Step 1 — Starting point

Ask the user a single open question first:

> "What are you working on? Give me a sentence or two — it can be a research project, a tool you're building, an analysis you're running, or anything else."

From their answer, infer the best-fit category:

- **hypothesis** — Research question exists, no data yet, planning phase
- **data** — Data collected or being collected, analysis in progress
- **results** — Analysis done, moving toward writing
- **draft** — Manuscript exists, needs writing or review
- **tool** — Building technical infrastructure: experiment software, real-time systems, data pipelines, acquisition tools, paradigm code, LSL integrations, etc. No research question driving it — the output is working code.

Do not show this list to the user. Infer the category silently and proceed. If genuinely ambiguous, ask one clarifying question.

Store the inferred category as `"stage"` in the config.

## Step 2 — Core project info

Ask these questions conversationally (not as a form — one or two at a time, natural back-and-forth):

- What is the project name?
- What is your lab / institution?
- What neuroscience modality or modalities are you working with? (EEG, fMRI, iEEG, eye tracking, ECG, other)
- What programming language and analysis tools do you use? (e.g. Python + MNE, MATLAB, R)

## Step 3 — Stage-specific questions

Based on their answer to Step 1, ask the relevant follow-up questions:

**If "Idea / hypothesis":**

- Do you have a target population in mind?
- Do you have a target journal or publication venue in mind?
- Do you have ethics approval yet, or is that pending?

**If "Have data":**

- Is the data already preprocessed or does it still need preprocessing?
- Is it organized in BIDS format?
- What is the main analysis goal? (ERP, time-frequency, connectivity, decoding, GLM, other)

**If "Have results":**

- Do you have a target journal?
- What citation style does that journal use? (APA, Vancouver, other)
- Do you have figures ready or do they still need to be generated?

**If "Have a draft":**

- What is the target journal?
- What is the main concern — scientific logic, writing quality, statistics, or all of the above?
- Is the draft in LaTeX or Word/Google Docs?

**If "Tool":**

- What kind of tool? (e.g. real-time experiment, data acquisition pipeline, LSL integration, paradigm, BCI system, preprocessing pipeline, other)
- What hardware or software does it interface with? (e.g. EEG amplifier, eye tracker, PsychoPy, BrainFlow, LSL, other)
- What programming language?
- Is this standalone or does it need to integrate with an existing recording/analysis setup?

## Step 3b — Open-ended catch-all

Before writing the file, ask:

> "Is there anything else you'd like to add — constraints, collaborators, deadlines, specific requirements, or anything else that might be useful context?"

If they add something, include it in the config under a sensible key. If they say no, proceed.

## Step 4 — Write .neuroflow/config.json

Write `.neuroflow/config.json` with only the fields you actually have data for. Do not write empty strings, nulls, or placeholder values — if you don't know it, leave the key out entirely.

**Rules:**
- Always include `"stage"` (one of: `"hypothesis"`, `"data"`, `"results"`, `"draft"`, `"tool"`)
- Use whatever field names make sense for what was collected — there is no fixed schema
- If the user stated a hypothesis or research question, save it verbatim under `"hypothesis"`
- If the user described their tool in detail, save the description under `"description"`
- Prefer human-readable values over codes (e.g. `"MNE-Python"` not `"mne"`)

Example for a hypothesis-stage project:

```json
{
  "stage": "hypothesis",
  "project_name": "Attentional Blink EEG",
  "institution": "Charles University",
  "modalities": ["EEG"],
  "hypothesis": "The attentional blink will be reflected in reduced P3 amplitude for T2 targets presented within 200–500ms of T1.",
  "population": "Healthy adults, 18–35",
  "journal_target": "NeuroImage",
  "programming_language": "Python",
  "analysis_tools": ["MNE-Python", "scipy"]
}
```

Example for a tool project:

```json
{
  "stage": "tool",
  "project_name": "RT EEG Feedback System",
  "description": "Real-time alpha power feedback loop using BrainFlow and LSL, displayed via PsychoPy.",
  "hardware": ["OpenBCI Cyton", "LSL"],
  "programming_language": "Python",
  "integrates_with": "existing EEG recording setup"
}
```

After writing the file, tell the user:

> "Created `.neuroflow/config.json` in your project folder. Every neuroflow skill and command will read this automatically when you run them. You can edit it any time."

Then briefly suggest the logical next step based on their stage:

- **hypothesis** → suggest starting with literature review or paradigm design
- **data** → suggest running preprocessing or analysis
- **results** → suggest drafting the manuscript
- **draft** → suggest `neuroflow:review-neuro`
- **tool** → suggest starting with paradigm design, LSL integration, or marker writing depending on what they described
