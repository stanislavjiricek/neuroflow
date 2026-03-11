---
name: neuroflow
description: Main entry point for a neuroflow project. If .neuroflow/ exists, shows current phase and status. If not, interviews the user and creates the .neuroflow/ folder structure.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/integrations.json
writes:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
  - .neuroflow/integrations.json
  - .claude/CLAUDE.md
---

# /neuroflow

## Greeting

Before doing anything else, greet the user with:

```
Hi, neuroflow here (v{version})
```

Replace `{version}` with the value from `.claude-plugin/plugin.json`. Then pick **one** of the following lines at random and print it directly after the greeting:

- *let's do some magic today*
- *let's go hack some stuff*
- *I heard HARKing is fun*

Print both lines together, then continue.

---

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

Also detect existing output folders to infer output paths per phase:

| Folder found | Used as output_path for |
|---|---|
| `scripts/` or `src/` | data-preprocess, data-analyze (code) |
| `results/` or `output/` | data-analyze (outputs) |
| `figures/` | data-analyze (figures) |
| `manuscript/` | paper-write |
| `paradigm/` | experiment |
| `tools/` | tool-build / tool-validate |
| `grant/` | grant-proposal |
| Nothing found | use defaults from neuroflow-core |

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

## Step 2b — Suggest phase sequence

Based on everything learned in Steps 1 and 2, generate a recommended ordered list of phases the user is likely to move through. Use the full pipeline as a reference:

```
ideation → preregistration → grant-proposal → experiment →
tool-build → tool-validate → data → data-preprocess →
data-analyze → paper-write → paper-review → write-report →
export → notes → finance
```

Select only the phases that apply to this project and order them logically. For example:

- A project already collecting data that targets a journal: `[data-preprocess, data-analyze, paper-write, paper-review, write-report, export]`
- A project starting from hypothesis with a tool to build: `[ideation, experiment, tool-build, tool-validate, data, data-preprocess, data-analyze, paper-write]`
- A grant-seeking early-stage project: `[ideation, preregistration, grant-proposal, experiment, data, data-analyze, paper-write]`

Print the suggested sequence clearly before creating `.neuroflow/`:

```
Based on what you described, here is the expected phase sequence for this project:

  → ideation (current)
  → preregistration
  → experiment
  → data-preprocess
  → data-analyze
  → paper-write
  → paper-review
  → export

You can always run /neuroflow:phase to see your position in this sequence or adjust it.
```

Save the list as `recommended_phases` in `project_config.md` (a simple comma-separated or YAML list). This list is read by `/phase` to render the phase map.

---

## Step 3 — Create .neuroflow/

Create this structure in the working directory:

```
.neuroflow/
├── project_config.md
├── flow.md
└── sessions/
└── reasoning/
    ├── flow.md
    └── general.json
```

**`project_config.md`** — write a short dense summary using what you learned. Include: project name, institution, active phase, research question (if given), modality, tools, `plugin_version` (from `plugin.json`), `recommended_phases` (the ordered list of phases suggested in Step 2b — see below), and an `## Output paths` table mapping each relevant phase to its detected or default output path. This file is read by every command and agent — keep it concise.

**`flow.md`** — write the initial index with only the folders that actually exist:

```
| File / Folder | Description | Last changed |
|---|---|---|
| project_config.md | Project overview and current phase. | YYYY-MM-DD |
| sessions/ | Daily session logs. | YYYY-MM-DD |
| reasoning/ | Structured per-phase decision logs (JSON: statement, source, reasoning). | YYYY-MM-DD |
```

**`sessions/`** — create a `.gitkeep` file. Remind the user to add `sessions/` to `.gitignore`.

**`reasoning/`** — create the folder with:
- `general.json` — an empty JSON array (`[]`) for project-level decisions
- `flow.md` — index of JSON files in this folder

> **Do not create `decisions.md`** — this is a legacy artifact superseded by `reasoning/general.json`. Use `reasoning/general.json` for all project-level decision logging.

---

## Step 4 — Update .claude/CLAUDE.md

Create or update `.claude/CLAUDE.md` in the **project root** (i.e. the user's current working directory, not `~/.claude/CLAUDE.md`). This local file travels with the repo and ensures every Claude session opened in this project folder automatically loads neuroflow context.

Append or update the following block:

```markdown
## neuroflow

This project uses the neuroflow workflow. Project memory is in `.neuroflow/`.

- Active phase: {phase}
- Config: `.neuroflow/project_config.md`
- Start any session by reading `project_config.md` and `flow.md` first.
```

If `~/.claude/CLAUDE.md` also exists, optionally add the block there too — but the **local** `.claude/CLAUDE.md` in the project root is required. Without it, Claude has no automatic project context when the folder is opened.

---

## Step 5 — Integration setup

Ask the user whether they want to connect the MCP integrations now:

> **Set up integrations?**
> neuroflow can connect to PubMed (literature search) and Miro (visual collaboration). Would you like to set them up now? (Y/n)
>
> - **Y / yes** — run the setup wizard (takes ~1 minute)
> - **n** — skip for now; you can run `/neuroflow:setup` at any time

**If the user says yes:** run the full `/setup` flow inline (follow every step in `commands/setup.md`). When done, return here and continue to Step 6.

**If the user says no or skip:** note it briefly — "Skipping integrations. You can run `/neuroflow:setup` at any time." — then continue to Step 6.

**If `.neuroflow/integrations.json` already exists with both credentials set:** skip this step entirely (do not prompt again).

---

## Step 6 — Confirm and suggest next step

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
