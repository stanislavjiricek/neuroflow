---
name: neuroflow
description: Main entry point for a neuroflow project. If .neuroflow/ exists, shows current phase and status. If not, interviews the user and creates the .neuroflow/ folder structure.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - ~/.neuroflow/flowie/profile.md        # optional — only if flowie is set up globally
  - ~/.neuroflow/flowie/sync.json         # optional — only if flowie is set up globally
  - ~/.neuroflow/flowie/integrations.json # optional — only if flowie is set up globally
  - ~/.neuroflow/user.yaml                # personal layer: flowie_handle, preferences, consents
  - ~/.claude/CLAUDE.md                   # only to find a stale neuroflow block (Step 0)
writes:
  - .neuroflow/                           # scaffold: neuroflow-core scripts/scaffold.py
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/objectives.md
  - .neuroflow/timeline.md
  - .neuroflow/sessions/YYYY-MM-DD.md
  - .claude/CLAUDE.md
  - .gitattributes
  - .gitignore
  - ~/.neuroflow/user.yaml                # personal answers (consent, mode, name, writing style)
  - .claude/settings.json                 # optional, only after the person agrees (Step 5b)
lifecycle: light
produces:
  - .neuroflow/project_config.md
next:
  - ideation
  - phase
  - setup
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

Replace `{version}` with the `version` from the **installed plugin's** manifest: `<neuroflow-core base dir>/../../.claude-plugin/plugin.json` (Claude Code shows the base directory when the `neuroflow:neuroflow-core` skill loads). Never read a `.claude-plugin/plugin.json` relative to the working directory — user projects have none. If the version cannot be read, print the line without `v{version}  ·  `. Then pick **one** of the following lines at random and print it directly after the logo block:

- *let's do some magic today*
- *let's go hack some stuff*
- *I heard HARKing is fun*

Print the logo, version, tagline, and the selected one-liner together as one block, then continue.

---

## Step 0 — Check for existing project

Look for an existing project with the walk-up rule (`neuroflow:neuroflow-core` → **Finding the project**): `.neuroflow/project_config.md` in the working directory or a parent folder, up to the git repository root, never at or above the home directory. If one is found in a parent folder, that folder is the project — say so and work there; never scaffold a second `.neuroflow/` inside it.

**If `.neuroflow/project_config.md` exists and `active_phase` is `setup`:**
The setup was started but not completed. Print:
```
It looks like neuroflow setup was started but not finished. Let's complete it now.
```
Skip Step 0d (the folder already exists) and continue directly to Step 1 to run the interview.

**If `.neuroflow/project_config.md` exists and `active_phase` is anything other than `setup`:**
1. Read `project_config.md` — facts from its frontmatter (`neuroflow:neuroflow-core` → **project_config.md — the config contract**). If it uses a legacy dialect (no `nf_schema` frontmatter), say so in one line and offer `/neuroflow:migrate`.
2. Read `flow.md`
3. Print a brief status: current phase(s), research question (if set), last session date (from `sessions/` folder)
4. Run the journal check (Step 0b) and the integration check (Step 0c)
5. **Global instruction check:** if `~/.claude/CLAUDE.md` contains a `## neuroflow` block, show that block exactly and ask with `AskUserQuestion` (**Remove it** / **Keep it**) whether to remove it — an older neuroflow version wrote it there, and it pushes one project's phase into every session on this machine. On yes, delete only that block (from `## neuroflow` to the next level-1 or level-2 heading, or the end of the file) and keep everything else. Never edit that file without the yes.
6. Ask what to do next with `AskUserQuestion`: **Continue with {active_phase}** (first), **Switch phase** (runs `/neuroflow:phase`), **Something else**
7. Stop — do not run the interview

---

## Step 0b — Journal check

Run this check whenever Step 0 finds an existing project. Skip entirely when **both** of the following are true: (1) the current active phase is not `paper`, and (2) `paper` does not appear in `recommended_phases`. If either condition is false, run the check.

**Trigger condition:** `paper` is the active phase, or appears in `recommended_phases`.

1. Look for `target_journal` in the `project_config.md` frontmatter.
2. If not found there, check `.neuroflow/paper/flow.md` for a line that starts with `target_journal:`.
3. **If a journal is already set:** print it as part of the status line — e.g. `Target journal: NeuroImage` — and continue. No further action needed.
4. **If no journal is set:**
   - Print: `No target journal has been set for your manuscript.`
   - Ask with `AskUserQuestion`: **Recommend journals** / **Not now**
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

6. Ask with `AskUserQuestion`: the top three journals as options plus **Decide later**; "Other" lets the person type a name.

7. If the user picks a journal (by option or name):
   - Set `target_journal: <journal name>` in the `project_config.md` frontmatter
   - If `.neuroflow/paper/` exists, also write `target_journal: <journal name>` to `.neuroflow/paper/flow.md`; do not create the folder or file if they do not exist yet
   - Confirm: `Target journal set to <journal name>.`

8. If the user says skip: note it and continue without writing.

**If no project is found here or above (Step 0):**
Run Step 0d immediately, then continue to Step 1.

---

## Step 0c — Integration check

Run this check whenever Step 0 finds an existing project. Check three integrations silently and report their status as a single compact line:

**Flowie check:**
Check whether `~/.neuroflow/flowie/profile.md` exists.
- Found: print `Flowie: active`
- Not found: print `Flowie: not set up (run /flowie to start)`

**Hive check:**
Check whether `~/.neuroflow/hives/` contains at least one cached repo, or `hive_repo:` is set in `project_config.md`.
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

**Run this step as soon as Step 0 confirms there is no project here or above — before the interview, before any questions.**

Run the scaffold script that ships with the `neuroflow:neuroflow-core` skill (Claude Code shows its base directory when the skill loads):

```bash
python <neuroflow-core base dir>/scripts/scaffold.py --root .
```

Use `python3` where `python` is not on the PATH. The script is idempotent and never overwrites an existing file. It creates:

- `.neuroflow/project_config.md` with the contract frontmatter (`nf_schema: 1`, `project_name`, `active_phase: setup`, `plugin_version`), `.neuroflow/flow.md`, `sessions/`, `tasks/` (one file per task — `/tasks` owns the format), the `wiki/` skeleton (`index.md`, `log.md`, `schema.md`, `raw/`, `pages/{concepts,entities,sources,synthesis,methods}/`), `reasoning/flow.md` and an empty `reasoning/general.jsonl`
- the merge-safety lines in `.gitattributes` and the local-tier lines in `.gitignore` (`neuroflow:neuroflow-core` → **Merge safety**, **Sharing tiers**)
- the static neuroflow block in `.claude/CLAUDE.md` (`neuroflow:neuroflow-core` → **Project instruction block**) — never in `~/.claude/CLAUDE.md`, and no `.github/copilot-instructions.md` or `AGENTS.md` mirrors

| Exit code | What to do |
|---|---|
| `0` | Print its one-line summary and continue to Step 1. |
| `1` | Scaffold done, but it found a legacy `project_config.md` or an older block in `.claude/CLAUDE.md` — say so in one line, offer `/neuroflow:migrate` after setup, and continue. |
| `2` | Refused (home directory, a folder inside another project, a config written by a newer neuroflow) — show its message and stop. Never work around a refusal. |

**If Python is unavailable**, create the same files by hand, skipping any that exist:

- `.neuroflow/project_config.md`:
  ```
  ---
  nf_schema: 1
  project_name: (setup in progress)
  active_phase: setup
  plugin_version: {version of the installed plugin, if known}
  ---

  # Project config
  ```
- `.neuroflow/flow.md` — the index table with rows for `project_config.md`, `sessions/`, `reasoning/`, `tasks/` and `wiki/` (today's date)
- `.neuroflow/sessions/.gitkeep`, `.neuroflow/tasks/.gitkeep`, the `wiki/` skeleton above (empty files and `.gitkeep`s)
- `.neuroflow/reasoning/general.jsonl` (empty) and `.neuroflow/reasoning/flow.md` with one row for `general.jsonl`
- the missing `.gitattributes` and `.gitignore` lines, appended — never replacing what is there
- `.claude/CLAUDE.md` with the static block (appended if the file exists without one)

Do not wait for user input. Do not ask for confirmation — the person ran `/neuroflow` to set up. Continue immediately to Step 1.

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

Before asking any interview questions, ask the user this as the **first question**, with `AskUserQuestion`:

> **Do you have a flowie or hive profile I can read to pre-fill the setup?**
>
> - **Flowie** — your personal research identity (stored in a private GitHub repo named `flowie`)
> - **Hive** — your team's shared research profile (stored in a team GitHub org repo)
> - **Both**
> - **Neither** — start the interview from scratch

**If the user picks Neither:** skip to Step 2 (full interview, unchanged).

**Otherwise:** follow the relevant sub-section(s) below. After reading all available profiles, go to the **Confirmation summary** sub-section instead of running Step 2.

---

### Flowie profile

**Check locally first:** if `~/.neuroflow/flowie/profile.md` already exists, **pull the latest changes first** (`git -C ~/.neuroflow/flowie pull --ff-only 2>/dev/null || true`) and then read both `profile.md` and `integrations.json` (if present) directly. Do this before asking any interview questions or touching integrations — go straight to the field mapping table below.

**If no local profile:** check `~/.neuroflow/user.yaml` (Unix) or `%USERPROFILE%\.neuroflow\user.yaml` (Windows) for a `flowie_handle` field. If found, use that handle as the default and ask: *"I found your GitHub username `{handle}` in your global neuroflow config. Use this for flowie? (Y/n)"* — skip to the fetch logic below if confirmed. Otherwise ask: *"What is your GitHub username?"*

Since flowie repositories are always private, use the following fetch order:

1. **Check `gh auth status` (one command).** If it succeeds, run `gh api /repos/{username}/flowie/contents/profile.md --jq '.content' | base64 -d` to fetch `profile.md`. Also fetch `integrations.json` with `gh api /repos/{username}/flowie/contents/integrations.json --jq '.content' | base64 -d 2>/dev/null` (ignore if missing). If `profile.md` succeeds, proceed to the field mapping table.
2. **If `gh` is unavailable or not authenticated**, immediately try a shallow clone: `git clone --depth 1 https://github.com/{username}/flowie.git /tmp/.flowie-fetch-{username}`, then read `profile.md` and `integrations.json` (if it exists) from the cloned directory. Clean up the temp directory after reading. If this succeeds, proceed to the field mapping table.
3. **Only if both of the above fail**, ask the user for a GitHub Personal Access Token (PAT) with `repo` scope. Use it in the Authorization header to call `GET https://api.github.com/repos/{username}/flowie/contents/profile.md`. Decode the base64 `content` field. Also attempt `GET .../integrations.json` in the same request batch (ignore 404).
4. **If none of the above works**: fall back to the full interview (Step 2).

Do not attempt additional `gh` commands (config file paths, env var checks, etc.) between steps 1 and 2. One `gh auth status` check is sufficient — if it fails, move directly to the git clone attempt.

**After reading the flowie repo:** if flowie was fetched remotely (not already cloned locally), clone it into `~/.neuroflow/flowie/` so it's available globally. Copy `integrations.json` into `~/.neuroflow/flowie/integrations.json`. This makes flowie's integrations available across all projects so Step 5 does not need to repeat the setup.

If the profile is found, extract the following fields and map them to interview answers:

| Profile field | Maps to |
|---|---|
| `name` | Researcher name — personal: stored as `name` in `~/.neuroflow/user.yaml`, never in `project_config.md` |
| `research_domain` | Context for "What are you working on?" |
| Methodological preferences (tools, paradigms) | Neuroscience modality and programming tools |
| Writing style | Personal: stored as `writing_style` in `~/.neuroflow/user.yaml` |

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

**Check locally first:** if `~/.neuroflow/hives/` contains a cache for this org/repo, read the index files from there directly.

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
| Consent question (issue drafts) | Skip if `auto_issue_reporting` is already in `~/.neuroflow/user.yaml` |
| Personality mode question | Skip if `default_mode` is already in `~/.neuroflow/user.yaml` |

Then continue directly to Step 2b.

---

## Step 2 — Interview

Ask conversationally — one or two questions at a time:

1. What are you working on? (one or two sentences)
2. Project name and institution?
3. Neuroscience modality or modalities? — ask with `AskUserQuestion` (multi-select), offering the likeliest modalities from the Step 1 scan (e.g. EEG, fMRI, MEG / iEEG, eye tracking); "Other" covers ECG and the rest
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

**Objectives and timeline (always, from the answers above — do not ask extra questions for this):**

- Distill the interview into `.neuroflow/objectives.md` — one numbered sentence per aim/objective (typically 2–5). Read it back to the user in one line for confirmation ("Your objectives, as I understood them: …"). This file is the cross-phase cornerstone every command reads at session start.
- If any deadline, milestone, or date was mentioned anywhere in the interview (conference, funder call, thesis date, data-collection window, ethics expiry), write it to `.neuroflow/timeline.md` as `| YYYY-MM-DD | what | phase it gates |`. If none were mentioned, create the file with just the header row — `/ethics`, `/meeting`, and `/paper` append to it later. `/phase` renders upcoming entries.

Then the consent question — only if `auto_issue_reporting` is not yet set in `~/.neuroflow/user.yaml` (consent is personal and covers all your projects). Ask with `AskUserQuestion` (**Yes, offer drafts** / **No**):

> neuroflow is in active development. When something seems off, it can draft a short GitHub issue for the developers — plugin version, phase and a one-line description, no personal data — and offer to open it in your browser. Nothing is opened or sent without your yes each time.
>
> **Should neuroflow offer issue drafts when it notices a problem?**

Record the answer as `auto_issue_reporting: yes` or `auto_issue_reporting: no` in `~/.neuroflow/user.yaml` — merge it in, keep every other line, create the file if missing. Never write it into `project_config.md`. No clear answer means `no`.

Then the personality mode question — only if `default_mode` is not yet set in `~/.neuroflow/user.yaml`. Ask with `AskUserQuestion`:

> **How would you like me to work with you?**
> - 🧐 **Teacher** — I’ll explain each step, check my assumptions, and wait for your go-ahead before changing anything.
> - ⚡ **Executor** — I’ll just do it. Less talk, more action. I’ll self-critique my work.
> - 🔍 **Critic** — I’ll interrogate your assumptions and surface hard questions before we proceed.
> - **Decide later**

| Answer | Write |
|---|---|
| Teacher / Executor / Critic | `default_mode: teacher` / `executor` / `critic` in `~/.neuroflow/user.yaml` — your personal default across projects |
| Decide later | nothing |

A team that wants one mode for everyone may set `default_mode` in the `project_config.md` frontmatter instead; a personal value overrides it (`neuroflow:neuroflow-core` → **Personality modes**). Any single message can switch with `mode: <name>`.

---

## Step 2b — Suggest phase sequence

Based on everything learned in Steps 1 and 2, generate a recommended ordered list of phases the user is likely to move through. The canonical phase list and order is the **Phase taxonomy** section in `neuroflow:neuroflow-core` (includes the `brain-*` modelling track, `poster`, `review`, and `output`); reference pipeline:

```
ideation → preregistration → grant-proposal → finance → experiment →
tool-build → tool-validate → data → data-preprocess → data-analyze →
brain-build → brain-optimize → brain-run → paper → review → poster →
write-report → output   (+ notes — anytime)
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
  → output

You can always run /neuroflow:phase to see your position in this sequence or adjust it.
```

Save the list as `recommended_phases` in the `project_config.md` frontmatter — canonical phase ids in order, e.g. `recommended_phases: [ideation, experiment, data, data-analyze, paper]`. This list is read by `/phase` to render the phase map.

---

## Step 3 — Update .neuroflow/ with full content

The `.neuroflow/` folder was already created in Step 0d. Now update it with the full content from the interview.

**`project_config.md`** — replace the scaffold placeholder, keeping the contract (`neuroflow:neuroflow-core` → **project_config.md — the config contract**):

- **Frontmatter:** `nf_schema: 1`, `project_name`, `active_phase` (a canonical phase id), `recommended_phases` (Step 2b), `target_journal` if known, `hive_repo` if connected, `plugin_version` (the installed plugin's version), and — if the user linked a flowie profile in Step 1b — `flowie_profiles` with one entry (`handle: {username}`, `repo: {username}/flowie`). Ask: *"Who else is working on this project? (name, email — one per line, or press Enter to skip)"* — add each person to `collaborators` (`name`, `email`, `handle` if known). Write only what the person gives you; never guess an email or handle. `/meeting` uses this list for calendar invites.
- **Body:** institution, research question (if given), modality, tools, and an `## Output paths` table mapping each relevant phase to its detected or default output path.
- **Never here:** consent, researcher name, writing style or a personal mode — those live in `~/.neuroflow/user.yaml` (Step 2).

This file is read by every command and agent — keep it concise.

**Collaborator note:** Remind the user that flowie lives at `~/.neuroflow/flowie/` (global, per-user) — it is never inside the project repo, so no `.gitignore` entry is needed. Each collaborator sets up their own flowie independently.

**`flow.md`** — update the index to reflect only the folders that actually exist (the structure is the same as what Step 0d wrote; update the `Last changed` dates).

> **Do not create `decisions.md`** — this is a legacy artifact superseded by `reasoning/general.jsonl`. Use `reasoning/general.jsonl` for all project-level decision logging (`neuroflow:neuroflow-core` → **Reasoning log**).

---

## Step 4 — Check the project instruction block

The scaffold (Step 0d) wrote the static neuroflow block into `.claude/CLAUDE.md` in the project root — the file Claude Code loads when the folder is opened. The block names no phase and points at `project_config.md`, so the interview changes nothing in it (`neuroflow:neuroflow-core` → **Project instruction block**). Only verify that it is there; if the file had other content, the block was appended after it.

The block lives in the project's `.claude/CLAUDE.md` only:

- never in `~/.claude/CLAUDE.md` — a block there leaks this project's state into every session on the machine (if you find one, offer its removal as in Step 0, step 5)
- never mirrored into `.github/copilot-instructions.md` or `AGENTS.md` — neuroflow is a Claude Code plugin

---

## Step 5 — Integration setup

Ask the user with `AskUserQuestion` whether they want to connect the MCP integrations now:

> **Set up integrations?**
> neuroflow can connect to Miro (visual collaboration) and custom LLM providers.
>
> - **Set up now** — run the setup wizard (takes ~1 minute)
> - **Skip** — you can run `/neuroflow:setup` at any time

**If the user picks Set up now:** run the full `/setup` flow inline (follow every step in `commands/setup.md`). When done, return here and continue to Step 5b.

**If the user picks Skip:** note it briefly — "Skipping integrations. You can run `/neuroflow:setup` at any time." — then continue to Step 5b.

**If `~/.neuroflow/integrations.json` (global credentials) already exists with the relevant keys set:** skip this step entirely — integrations are managed globally on this device. (A per-project `.neuroflow/integrations.json` override also counts. `~/.neuroflow/flowie/integrations.json` holds non-secret settings only and is not a credentials store.)

**Google Workspace (gws) option:**
Also offer gws CLI setup as part of the integration wizard:

> **Google Workspace (gws)** — connects Claude to your Google Drive and Gmail for paper pipeline and grant workflows  
> - Install: `npm install -g @googleworkspace/cli` (or `brew install googleworkspace-cli` on macOS)  
> - Auth setup: `gws auth setup`, then `gws auth login --scopes drive,calendar,gmail`  
> - Claude extension: `npx skills add https://github.com/googleworkspace/cli`  
> - Skip for now? You can set this up at any time with `/neuroflow:setup`

If the user skips gws: write `gws_setup: skipped` to `~/.neuroflow/user.yaml`.

---

## Step 5b — Bookkeeping permissions (optional, offered once)

neuroflow writes session logs, decision logs and `flow.md` indexes often, and each write can raise a permission prompt. Offer — once, during setup — to allow exactly those writes. Show the rules, then ask with `AskUserQuestion` (**Add these rules** / **Skip**):

```json
{
  "permissions": {
    "allow": [
      "Edit(.neuroflow/sessions/**)",
      "Edit(.neuroflow/reasoning/**)",
      "Edit(.neuroflow/**/flow.md)"
    ]
  }
}
```

On yes, merge them into the project's `.claude/settings.json` — keep every existing setting and rule, create the file if missing. `Edit(...)` rules cover every file-writing tool. `.claude/settings.json` is shared with collaborators; a person who wants the rules only for themselves puts them in `.claude/settings.local.json` instead. Never add a blanket `.neuroflow/**` rule, a rule for `.neuroflow/integrations.json` or anything under `~/.neuroflow/`, or any `Bash` rule.

---

## Step 6 — Confirm, checklist and next step

Tell the user what was created, then print the post-setup checklist — `[x]` done, `[ ]` still open:

```
Setup checklist
  [x] .neuroflow/ project memory (scaffold)
  [x] .gitignore keeps sessions/, review/ and credentials out of git
  [x] .gitattributes merges append-only logs without conflicts
  [ ] objectives.md: 2–5 numbered aims
  [ ] timeline.md: deadlines and milestones
  [ ] Integrations (/neuroflow:setup)
  [ ] Personal settings in ~/.neuroflow/user.yaml (issue drafts, mode)
```

Tick each line from what actually exists now; skip lines that do not apply. Then suggest the logical next command based on their phase and close with `Next: /neuroflow:<name>`:

| Phase | Suggested next step |
|---|---|
| hypothesis / ideation | `/neuroflow:ideation` |
| experiment | `/neuroflow:experiment` |
| tool | `/neuroflow:tool-build` |
| data | `/neuroflow:data` |
| analysis | `/neuroflow:data-analyze` |
| writing | `/neuroflow:paper` |
| peer review | `/neuroflow:review` |
