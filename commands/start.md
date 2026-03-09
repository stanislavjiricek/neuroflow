---
name: start
description: Main entry point for a neuroflow project. If .neuroflow/ exists, shows current phase and status. If not, interviews the user and creates the .neuroflow/ folder structure.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
writes:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
  - .claude/CLAUDE.md
---

# /start

## Step 0 — Check for existing project

Check whether `.neuroflow/` exists in the current working directory.

**If `.neuroflow/project_config.md` exists:**
1. Read `project_config.md`
2. Read `flow.md`
3. Print a brief status: current phase(s), research question (if set), last session date (from `sessions/` folder)
4. Ask if the user wants to continue, switch phase, or do something specific
5. Stop — do not run the interview

**If `.neuroflow/` does not exist:**
Continue to Step 1.

---

## Step 1 — Scan the repo

Before asking anything, use Glob and Read to inspect the working directory. Look for signals:

| What you find | Inferred signal |
|---|---|
| `sub-*/`, `dataset_description.json`, `participants.tsv` | BIDS dataset — data phase |
| `*.py`, `*.m`, `*.R` analysis scripts | Processing underway |
| `derivatives/`, `results/`, `figures/` | Analysis done |
| `*.tex`, `*.docx`, `manuscript/` | Writing phase |
| `paradigm/`, `*.psyexp`, PsychoPy scripts | Experiment phase |
| Empty or only README | Fresh start |

Summarise what you found in one sentence before the first question. Use it to skip or pre-answer obvious questions.

---

## Step 2 — Interview

Ask conversationally — one or two questions at a time:

1. What are you working on? (one or two sentences)
2. Project name and institution?
3. Neuroscience modality or modalities? (EEG, fMRI, iEEG, eye tracking, ECG, other)
4. Programming language and tools? (Python + MNE, MATLAB, R, etc.)

Then ask phase-specific questions based on what they described:

**Hypothesis / ideation:**
- Can you state the research question in one sentence?
- Do you have ethics approval or is that pending?

**Data / analysis:**
- Is the data already preprocessed?
- Is it in BIDS format?
- What is the main analysis goal?

**Writing:**
- What is the target journal?
- Draft in LaTeX or Word?

**Tool:**
- What kind of tool? (experiment software, data pipeline, real-time system, paradigm, other)
- What hardware or software does it interface with?

Finally: "Is there anything else useful to add — collaborators, deadlines, constraints?"

---

## Step 3 — Create .neuroflow/

Create this structure in the working directory:

```
.neuroflow/
├── project_config.md
├── flow.md
├── decisions.md
├── sessions/
└── references/
    └── flow.md
```

**`project_config.md`** — write a short dense summary using what you learned. Include: project name, institution, active phase, research question (if given), modality, tools. This file is read by every command and agent — keep it concise.

**`flow.md`** — write the initial index with only the folders that actually exist:

```
| File / Folder | Description | Last changed |
|---|---|---|
| project_config.md | Project overview and current phase. | YYYY-MM-DD |
| decisions.md | Key decisions log. | YYYY-MM-DD |
| sessions/ | Daily session logs. | YYYY-MM-DD |
| references/ | Papers, URLs, and data paths used in this project. | YYYY-MM-DD |
```

**`decisions.md`** — create empty with just a header.

**`references/flow.md`** — create empty with just a header.

**`sessions/`** — create a `.gitkeep` file. Remind the user to add `sessions/` to `.gitignore`.

---

## Step 4 — Update .claude/CLAUDE.md

Append or update a short neuroflow block in `.claude/CLAUDE.md`:

```markdown
## neuroflow

This project uses the neuroflow workflow. Project memory is in `.neuroflow/`.

- Active phase: {phase}
- Config: `.neuroflow/project_config.md`
- Start any session by reading `project_config.md` and `flow.md` first.
```

---

## Step 5 — Confirm and suggest next step

Tell the user what was created. Then suggest the logical next command based on their phase:

| Phase | Suggested next step |
|---|---|
| hypothesis / ideation | `/neuroflow:ideation` |
| experiment | `/neuroflow:experiment` |
| tool | `/neuroflow:tool-build` |
| data | `/neuroflow:data` |
| analysis | `/neuroflow:data-analyze` |
| writing | `/neuroflow:paper-write` |
| review | `/neuroflow:paper-review` |
