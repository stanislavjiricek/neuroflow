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

Before doing anything else, display the ASCII welcome logo:

```
   ____  ___  __  ___________  / __/ /___ _      __
  / __ \/ _ \/ / / / ___/ __ \/ /_/ / __ \ | /| / /
 / / / /  __/ /_/ / /  / /_/ / __/ / /_/ / |/ |/ /
/_/ /_/\___/\__,_/_/   \____/_/ /_/\____/|__/|__/

  v{version}  ·  agentic neuroscience research, from hypothesis to publication
```

Replace `{version}` with the value from `.claude-plugin/plugin.json`. Then pick **one** of the following lines at random and print it directly after the logo block:

- *let's do some magic today*
- *let's go hack some stuff*
- *I heard HARKing is fun*

Print the logo, version, tagline, and the selected one-liner together as one block, then continue.

---

## Step 0 — Check for existing project

Check whether `.neuroflow/` exists in the current working directory.

**If `.neuroflow/project_config.md` exists:**
1. Read `project_config.md`
2. Read `flow.md`
3. Print a brief status: current phase(s), research question (if set), last session date (from `sessions/` folder)
4. Ask if the user wants to continue, switch phase, or do something specific
5. Run the journal check (Step 0b) before stopping
6. Stop — do not run the interview

---

## Step 0b — Journal check

Run this check whenever Step 0 finds an existing project. Skip entirely when **both** of the following are true: (1) the current active phase is not `paper-write` or `paper-review`, and (2) neither `paper-write` nor `paper-review` appears in `recommended_phases`. If either condition is false, run the check.

**Trigger condition:** `paper-write` or `paper-review` is the active phase, or appears in `recommended_phases`.

1. Look for a `target_journal:` field in `project_config.md`.
2. If not found there, check `.neuroflow/paper-write/flow.md` for a line that starts with `target_journal:`.
3. **If a journal is already set:** print it as part of the status line — e.g. `Target journal: NeuroImage` — and continue. No further action needed.
4. **If no journal is set:**
   - Print: `No target journal has been set for your manuscript.`
   - Ask: `Would you like a journal recommendation? (Y/n)`
   - **If yes:** run the journal recommendation workflow below.
   - **If no:** note it briefly — `"You can set the target journal when you run /neuroflow:paper-write."` — and continue.

### Journal recommendation workflow

When the user asks for a recommendation:

1. Read the following from `project_config.md`: modality, research question, tools, and any keywords.
2. If `.neuroflow/ideation/` exists, read it for topic keywords and literature already collected.
3. Use the `neuroflow:scholar` agent (PubMed + bioRxiv) to search for recent papers in the same area. Note which journals those papers appear in most frequently.
4. Apply the following ranking criteria to generate a shortlist of 3–5 candidate journals:

   | Criterion | What to check |
   |---|---|
   | Scope alignment | Does the journal publish papers on this modality and methodology? |
   | Paper type | Does the journal accept the expected paper type (methods, empirical, review)? |
   | Open access | If the user mentioned OA requirements, filter accordingly |
   | Typical length | Does the journal's word-count range fit the expected manuscript size? |
   | Prestige vs. speed | Balance impact factor with typical time-to-decision for the field |

5. Present the shortlist in priority order. For each journal include:
   - Journal name and publisher
   - One-sentence scope summary
   - Why it fits this project specifically
   - Any notable constraints (page limits, OA fees, data sharing policy)

6. Ask: `Which journal should I set as the target? (Enter number or type a name, or "skip" to decide later)`

7. If the user picks a journal (by number or name):
   - Write `target_journal: <journal name>` to `project_config.md`
   - If `.neuroflow/paper-write/` exists, also write `target_journal: <journal name>` to `.neuroflow/paper-write/flow.md`; do not create the folder or file if they do not exist yet
   - Confirm: `Target journal set to <journal name>.`

8. If the user says skip: note it and continue without writing.

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

Then ask the following consent question (always, regardless of phase):

> neuroflow is in active development. If you run into a bug or something feels off, it can automatically file an anonymous issue on GitHub to help improve the plugin — no personal data, just the plugin version, phase, and a brief description of what went wrong.
>
> **Do you allow neuroflow to automatically report issues to the developers? (y/n)**

Record the answer as `auto_issue_reporting: yes` or `auto_issue_reporting: no` in `project_config.md`. If the user does not answer clearly, default to `no`.

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

**`project_config.md`** — write a short dense summary using what you learned. Include: project name, institution, active phase, research question (if given), modality, tools, `plugin_version` (from `plugin.json`), `auto_issue_reporting` (from the consent question in Step 2 — `yes` or `no`), `recommended_phases` (the ordered list of phases suggested in Step 2b — see below), and an `## Output paths` table mapping each relevant phase to its detected or default output path. This file is read by every command and agent — keep it concise.

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
