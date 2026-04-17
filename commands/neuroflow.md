---
name: neuroflow
description: Main entry point for a neuroflow project. If .neuroflow/ exists, shows current phase and status. If not, interviews the user and creates the .neuroflow/ folder structure.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/integrations.json
  - .neuroflow/flowie/profile.md        # optional — only if flowie profile exists or user provides one
  - .neuroflow/flowie/sync.json         # optional — only if flowie profile exists
  - .neuroflow/flowie/integrations.json # optional — only if flowie is set up; read before Step 5
writes:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
  - .neuroflow/integrations.json
  - .claude/CLAUDE.md
  - .github/copilot-instructions.md
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

**If `.neuroflow/project_config.md` exists and `active_phase` is `setup`:**
The setup was started but not completed. Print:
```
It looks like neuroflow setup was started but not finished. Let's complete it now.
```
Skip Step 0d (the folder already exists) and continue directly to Step 1 to run the interview.

**If `.neuroflow/project_config.md` exists and `active_phase` is anything other than `setup`:**
1. Read `project_config.md`
2. Read `flow.md`
3. Print a brief status: current phase(s), research question (if set), last session date (from `sessions/` folder)
4. Ask if the user wants to continue, switch phase, or do something specific
5. Run the journal check (Step 0b) before stopping
5b. Run the integration check (Step 0c) before stopping
6. Stop — do not run the interview

---

## Step 0b — Journal check

Run this check whenever Step 0 finds an existing project. Skip entirely when **both** of the following are true: (1) the current active phase is not `paper`, and (2) `paper` does not appear in `recommended_phases`. If either condition is false, run the check.

**Trigger condition:** `paper` is the active phase, or appears in `recommended_phases`.

1. Look for a `target_journal:` field in `project_config.md`.
2. If not found there, check `.neuroflow/paper/flow.md` for a line that starts with `target_journal:`.
3. **If a journal is already set:** print it as part of the status line — e.g. `Target journal: NeuroImage` — and continue. No further action needed.
4. **If no journal is set:**
   - Print: `No target journal has been set for your manuscript.`
   - Ask: `Would you like a journal recommendation? (Y/n)`
   - **If yes:** run the journal recommendation workflow below.
   - **If no:** note it briefly — `"You can set the target journal when you run /neuroflow:paper."` — and continue.

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
   - If `.neuroflow/paper/` exists, also write `target_journal: <journal name>` to `.neuroflow/paper/flow.md`; do not create the folder or file if they do not exist yet
   - Confirm: `Target journal set to <journal name>.`

8. If the user says skip: note it and continue without writing.

**If `.neuroflow/` does not exist:**
Run Step 0d immediately, then continue to Step 1.

---

## Step 0c — Integration check

Run this check whenever Step 0 finds an existing project. Check three integrations silently and report their status as a single compact line:

**Flowie check:**
Look for a `flowie/` entry in `.neuroflow/flow.md`.
- Found: print `Flowie: active`
- Not found: print `Flowie: not set up (run /flowie to start)`

**Hive check:**
Look for a `hive/` entry in `.neuroflow/flow.md`, or a `hive_repo:` field in `project_config.md`.
- Found: print `Hive: connected to [team name if available]`
- Not found: print `Hive: not connected`

**Google Workspace (gws) check:**
Run `gws --version 2>/dev/null`.
- If it returns a version string: print `Google Workspace (gws): ready`
- If the command fails or returns nothing: print `Google Workspace (gws): not installed — run /setup for setup instructions`

Combine all three into one line, e.g.:
```
Integrations — Flowie: active | Hive: not connected | gws: ready
```

Do not prompt the user to set anything up here. This is informational only.

---

## Step 0d — Scaffold .neuroflow/ immediately

**Run this step as soon as Step 0 confirms `.neuroflow/` does not exist — before the interview, before any questions.**

Create the following structure in the current working directory:

```
.neuroflow/
├── project_config.md
├── flow.md
├── sessions/
│   └── .gitkeep
├── tasks/
│   ├── inbox/
│   ├── ready/
│   ├── active/
│   ├── review/
│   ├── meeting/
│   ├── done/
│   └── archive/
├── wiki/
│   ├── index.md
│   ├── log.md
│   ├── schema.md
│   ├── raw/
│   └── pages/
│       ├── concepts/
│       ├── entities/
│       ├── sources/
│       ├── synthesis/
│       └── methods/
└── reasoning/
    ├── flow.md
    └── general.json
```

**`project_config.md`** — write a minimal placeholder:

```
# Project config

project_name: (setup in progress)
active_phase: setup
plugin_version: {version from plugin.json}
auto_issue_reporting: no
```

**`flow.md`** — write the initial index:

```
| File / Folder | Description | Last changed |
|---|---|---|
| project_config.md | Project overview and current phase. | YYYY-MM-DD |
| sessions/ | Daily session logs. | YYYY-MM-DD |
| reasoning/ | Structured per-phase decision logs (JSON: statement, source, reasoning). | YYYY-MM-DD |
```

**`sessions/`** — create a `.gitkeep` file. Remind the user to add `sessions/` to `.gitignore`.

**`tasks/`** — create each column folder (`inbox/`, `ready/`, `active/`, `review/`, `meeting/`, `done/`, `archive/`) with a `.gitkeep` file. This is the shared project-level Kanban board — git-tracked and visible to all collaborators. Update `.neuroflow/flow.md` to include a `tasks/` row.

**`wiki/`** — create the scaffold for the project-level shared wiki (`index.md`, `log.md`, `schema.md` as empty placeholders, `raw/`, `pages/concepts/`, `pages/entities/`, `pages/sources/`, `pages/synthesis/`, `pages/methods/`). The wiki is initialized properly on first `/wiki` run. Update `.neuroflow/flow.md` to include a `wiki/` row.

**`reasoning/`** — create the folder with:
- `general.json` — an empty JSON array (`[]`)
- `flow.md` — minimal index with this content:

```
| File / Folder | Description | Last changed |
|---|---|---|
| general.json | Project-level decision log. | YYYY-MM-DD |
```

**`.claude/CLAUDE.md` and `.github/copilot-instructions.md`** — create or update both files in the project root with the neuroflow block (use `setup` as the active phase placeholder; this will be updated to the real phase in Step 4):

```markdown
## neuroflow

This project uses the neuroflow workflow. Project memory is in `.neuroflow/`.

- Active phase: setup
- Config: `.neuroflow/project_config.md`
- Start any session by reading `project_config.md` and `flow.md` first.
```

Do not wait for user input. Do not ask for confirmation. Create all files silently and continue immediately to Step 1.

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
| `manuscript/` | paper |
| `paradigm/` | experiment |
| `tools/` | tool-build / tool-validate |
| `grant/` | grant-proposal |
| Nothing found | use defaults from neuroflow-core |

Summarise what you found in one sentence before the first question. Use it to skip or pre-answer obvious questions.

---

## Step 1b — Check for existing profiles

Before asking any interview questions, ask the user this as the **first question**:

> **Do you have a flowie or hive profile I can read to pre-fill the setup?** (Y/n)
>
> - **Flowie** — your personal research identity (stored in a private GitHub repo named `flowie`)
> - **Hive** — your team's shared research profile (stored in a team GitHub org repo)
> - **Neither / not sure** — press Enter to start the interview from scratch

**If the user says no or presses Enter:** skip to Step 2 (full interview, unchanged).

**If the user says yes:** ask which type(s) of profile they have — Flowie, Hive, or both — then follow the relevant sub-section(s) below. After reading all available profiles, go to the **Confirmation summary** sub-section instead of running Step 2.

---

### Flowie profile

**Check locally first:** if `.neuroflow/flowie/profile.md` already exists in the current working directory, **pull the latest changes first** (`git -C .neuroflow/flowie pull --ff-only 2>/dev/null || true`) and then read both `profile.md` and `integrations.json` (if present) directly. Do this before asking any interview questions or touching integrations — go straight to the field mapping table below.

**If no local profile:** ask: *"What is your GitHub username?"*

Since flowie repositories are always private, use the following fetch order:

1. **Check `gh auth status` (one command).** If it succeeds, run `gh api /repos/{username}/flowie/contents/profile.md --jq '.content' | base64 -d` to fetch `profile.md`. Also fetch `integrations.json` with `gh api /repos/{username}/flowie/contents/integrations.json --jq '.content' | base64 -d 2>/dev/null` (ignore if missing). If `profile.md` succeeds, proceed to the field mapping table.
2. **If `gh` is unavailable or not authenticated**, immediately try a shallow clone: `git clone --depth 1 https://github.com/{username}/flowie.git /tmp/.flowie-fetch-{username}`, then read `profile.md` and `integrations.json` (if it exists) from the cloned directory. Clean up the temp directory after reading. If this succeeds, proceed to the field mapping table.
3. **Only if both of the above fail**, ask the user for a GitHub Personal Access Token (PAT) with `repo` scope. Use it in the Authorization header to call `GET https://api.github.com/repos/{username}/flowie/contents/profile.md`. Decode the base64 `content` field. Also attempt `GET .../integrations.json` in the same request batch (ignore 404).
4. **If none of the above works**: fall back to the full interview (Step 2).

Do not attempt additional `gh` commands (config file paths, env var checks, etc.) between steps 1 and 2. One `gh auth status` check is sufficient — if it fails, move directly to the git clone attempt.

**After reading the flowie repo:** copy `integrations.json` (if fetched remotely) into `.neuroflow/flowie/integrations.json`. This makes flowie's integrations available locally so Step 5 does not need to repeat the setup.

If the profile is found, extract the following fields and map them to interview answers:

| Profile field | Maps to |
|---|---|
| `name` | Researcher / PI name — stored in `project_config.md` |
| `research_domain` | Context for "What are you working on?" |
| Methodological preferences (tools, paradigms) | Neuroscience modality and programming tools |
| Writing style | Stored as `writing_style` in `project_config.md` |

If the profile cannot be fetched, report the cause clearly:

```
Could not read flowie profile from github.com/{username}/flowie.
Possible causes: authentication failure, network error, or repository does not exist yet.
Falling back to the full interview.
```

Then continue to Step 2.

---

### Hive profile

Ask: *"What is your team's Hive repo? (e.g. my-lab/hive-research)"*

**Check locally first:** if `.neuroflow/hive/` already exists, read the index files from there directly.

**If no local hive data:** fetch the Hive index using the same authentication approach as for flowie above (`gh` CLI preferred, PAT as fallback). Try the following locations in order:

1. Root `README.md`: `GET https://api.github.com/repos/{org}/{repo}/contents/README.md`
2. `directions.md` at the repo root: `GET https://api.github.com/repos/{org}/{repo}/contents/directions.md`

Use whichever file is found first. Decode the base64 `content` field and extract any shared research directions, modalities, and tools. Use these as additional context when pre-filling the interview answers.

If the Hive repo cannot be read (authentication failure, network error, repo not found), report it and continue with whatever profile data is already available.

---

### Confirmation summary

Once one or more profiles have been read, **do not run the full Step 2 interview**. Instead, display a pre-filled summary of every field that could be inferred. Label the source(s) clearly:

```
Based on your flowie profile [and team hive profile], here is what I've inferred for this project:

  Researcher:      {name from flowie, or "—"}
  Research area:   {research_domain from flowie, or team direction from hive, or "—"}
  Modality:        {inferred from methodological preferences, or "—"}
  Tools:           {inferred from methodological preferences, or "—"}
  Writing style:   {from flowie profile, or "—"}

Does this look right? Confirm with Y, type a correction for any field, or add anything that's missing.
```

Wait for the user to respond. Accept corrections inline (e.g. *"Modality is MEG, not EEG"*) and update the pre-filled values accordingly.

After the user confirms, ask **only** the Step 2 questions that could not be pre-filled from the profile:

| Step 2 question | When to skip |
|---|---|
| What are you working on? | Skip if `research_domain` was confirmed |
| Project name and institution? | **Always ask** — this is the project name, not the researcher's name |
| Neuroscience modality? | Skip if modality was confirmed |
| Programming language and tools? | Skip if tools were confirmed |
| Phase-specific questions (ethics, BIDS, target journal, etc.) | Always ask — profile does not contain project-specific phase data |
| "Anything else to add?" | Always ask |
| Consent question (auto issue reporting) | Always ask |
| Personality mode question | Always ask |

Then continue directly to Step 2b.

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

Then ask the personality mode question:

> **How would you like me to work on this project?**
> 1. 🧐 **Teacher** — I’ll explain each step, check my assumptions, and wait for your go-ahead before changing anything.
> 2. ⚡ **Executor** — I’ll just do it. Less talk, more action. I’ll self-critique my work.
> 3. 🔍 **Critic** — I’ll interrogate your assumptions and surface hard questions before we proceed.
>
> (Enter 1, 2, or 3, or press Enter to skip and decide later)

Map the answer to a mode:
| Answer | `default_mode` value |
|---|---|
| 1 | `teacher` |
| 2 | `executor` |
| 3 | `critic` |
| Skip / Enter | — omit the key from `project_config.md` |

Record the answer as `default_mode: teacher` / `default_mode: executor` / `default_mode: critic` in `project_config.md`. If the user skips, do not write the key.

---

## Step 2b — Suggest phase sequence

Based on everything learned in Steps 1 and 2, generate a recommended ordered list of phases the user is likely to move through. Use the full pipeline as a reference:

```
ideation → preregistration → grant-proposal → experiment →
tool-build → tool-validate → data → data-preprocess →
data-analyze → paper → write-report →
notes → finance
```

Select only the phases that apply to this project and order them logically. For example:

- A project already collecting data that targets a journal: `[data-preprocess, data-analyze, paper, write-report]`
- A project starting from hypothesis with a tool to build: `[ideation, experiment, tool-build, tool-validate, data, data-preprocess, data-analyze, paper]`
- A grant-seeking early-stage project: `[ideation, preregistration, grant-proposal, experiment, data, data-analyze, paper]`

Print the suggested sequence clearly:

```
Based on what you described, here is the expected phase sequence for this project:

  → ideation (current)
  → preregistration
  → experiment
  → data-preprocess
  → data-analyze
  → paper
  → export

You can always run /neuroflow:phase to see your position in this sequence or adjust it.
```

Save the list as `recommended_phases` in `project_config.md` (a simple comma-separated or YAML list). This list is read by `/phase` to render the phase map.

---

## Step 3 — Update .neuroflow/ with full content

The `.neuroflow/` folder was already created in Step 0d. Now update it with the full content from the interview.

**`project_config.md`** — overwrite the placeholder with a short dense summary using what you learned. Include: project name, institution, active phase, research question (if given), modality, tools, `plugin_version` (from `plugin.json`), `auto_issue_reporting` (from the consent question in Step 2 — `yes` or `no`), `recommended_phases` (the ordered list of phases suggested in Step 2b), an `## Output paths` table mapping each relevant phase to its detected or default output path, (if the user linked a flowie project during Step 1b) `flowie_project: {name}`, and a `collaborators:` list. Ask: *"Who else is working on this project? (name, email — one per line, or press Enter to skip)"* — add each person as `- name: {name}\n  email: {email}\n  handle: {github-handle or omit}`. This list is used by `/meeting` to pull attendee emails for calendar invites. This file is read by every command and agent — keep it concise.

**`.neuroflow/flowie/` gitignore:** After writing all files, check whether `.neuroflow/flowie/` is already excluded in the project's `.gitignore`. If not, print:

```
⚠️  Multi-collaborator tip: .neuroflow/flowie/ is your personal research profile —
    it should NOT be committed to a shared repo.

    Add this to your project's .gitignore:
      .neuroflow/flowie/

    Each collaborator will have their own private flowie profile.
    Shared project tasks live in .neuroflow/tasks/ (already git-tracked).
```

**`flow.md`** — update the index to reflect only the folders that actually exist (the structure is the same as what Step 0d wrote; update the `Last changed` dates).

> **Do not create `decisions.md`** — this is a legacy artifact superseded by `reasoning/general.json`. Use `reasoning/general.json` for all project-level decision logging.

---

## Step 4 — Update .claude/CLAUDE.md and .github/copilot-instructions.md

Both files were already created with a placeholder phase (`setup`) in Step 0d. Now update them with the real active phase determined from the interview.

Update **both** of the following files in the **project root** (i.e. the user's current working directory):

- `.claude/CLAUDE.md` — loaded automatically by Claude Code / Claude.ai when the folder is opened
- `.github/copilot-instructions.md` — loaded automatically by GitHub Copilot (VS Code extension, Copilot CLI, and GitHub Copilot Chat) when working in the project

**Both files must contain identical content.** Update the neuroflow block in each to replace `Active phase: setup` with the real active phase:

```markdown
## neuroflow

This project uses the neuroflow workflow. Project memory is in `.neuroflow/`.

- Active phase: {phase}
- Config: `.neuroflow/project_config.md`
- Start any session by reading `project_config.md` and `flow.md` first.
```

If `.github/copilot-instructions.md` already contains other project instructions, append the neuroflow block at the end (do not overwrite the whole file). If it already contains a neuroflow block, update the block in place. Identify the neuroflow block by the header line `## neuroflow` — the block runs from that header to the next `##`-level header (or end of file).

If `~/.claude/CLAUDE.md` also exists, optionally add the block there too — but the **local** `.claude/CLAUDE.md` in the project root is required. Without it, Claude has no automatic project context when the folder is opened.

---

## Step 5 — Integration setup

Ask the user whether they want to connect the MCP integrations now:

> **Set up integrations?**
> neuroflow can connect to Miro (visual collaboration) and custom LLM providers. Would you like to set them up now? (Y/n)
>
> - **Y / yes** — run the setup wizard (takes ~1 minute)
> - **n** — skip for now; you can run `/neuroflow:setup` at any time

**If the user says yes:** run the full `/setup` flow inline (follow every step in `commands/setup.md`). When done, return here and continue to Step 6.

**If the user says no or skip:** note it briefly — "Skipping integrations. You can run `/neuroflow:setup` at any time." — then continue to Step 6.

**If `.neuroflow/integrations.json` already exists with credentials set:** skip this step entirely (do not prompt again).

**If `.neuroflow/flowie/integrations.json` exists:** skip this step entirely — integrations are managed through your flowie profile. Do not create a separate `.neuroflow/integrations.json`.

**Google Workspace (gws) option:**
Also offer gws CLI setup as part of the integration wizard:

> **Google Workspace (gws)** — connects Claude to your Google Drive and Gmail for paper pipeline and grant workflows  
> - Install: `npm install -g @googleworkspace/cli` (or `brew install googleworkspace-cli` on macOS)  
> - Auth setup: `gws auth setup`, then `gws auth login --scopes drive,calendar,gmail`  
> - Claude extension: `npx skills add https://github.com/googleworkspace/cli`  
> - Skip for now? You can set this up at any time with `/neuroflow:setup`

If the user skips gws **and flowie is not active**: write `gws_setup: skipped` to `.neuroflow/integrations.json` (create the file if it doesn’t exist yet). If flowie is active, skip this write — integrations are owned by the flowie profile.

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
| writing | `/neuroflow:paper` |
| peer review | `/neuroflow:review` |
