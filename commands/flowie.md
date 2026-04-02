---
name: flowie
description: Personal research OS — link a private GitHub repository to store your research profile, cross-project Kanban task board, and project registry with phase tracking. Supports profile creation, task management, project registry, GitHub sync, phase auto-tracking, and credential export.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/flowie/profile.md
  - .neuroflow/flowie/ideas.md
  - .neuroflow/flowie/sync.json
  - .neuroflow/flowie/tasks/config.json
  - .neuroflow/flowie/projects/projects.json
  - .neuroflow/flowie/wellbeing/config.json
  - .neuroflow/flowie/wellbeing/*.json
writes:
  - .neuroflow/flowie/profile.md
  - .neuroflow/flowie/ideas.md
  - .neuroflow/flowie/sync.json
  - .neuroflow/flowie/tasks/**
  - .neuroflow/flowie/projects/projects.json
  - .neuroflow/flowie/projects/*.md
  - .neuroflow/flowie/notes/
  - .neuroflow/flowie/wellbeing/config.json
  - .neuroflow/flowie/wellbeing/*.json
  - .neuroflow/project_config.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /flowie

Personal research OS for neuroflow. Links the current project to a private GitHub repository — the user's `flowie` repo — which stores three layers of research infrastructure:

1. **Identity layer** — `profile.md`, `ideas.md`: research stances, writing style, methodological preferences, cross-project hypotheses
2. **Kanban task board** — `tasks/`: column-per-folder, task-per-.md-file, ASCII board view
3. **Project registry** — `projects/`: `projects.json` machine index + one `{name}.md` per project with phase timeline

The `flowie` directory at `.neuroflow/flowie/` **is the git repo itself** — cloned from GitHub. GitHub is canonical. Pull before every read, push after every write.

Read the `neuroflow:phase-flowie` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` and `flow.md` before starting.

Flowie is fully optional. Nothing breaks if it is not set up.

---

## Git operations pattern

All git operations use the `-C` flag to target the flowie repo directory. All push operations fail silently to avoid blocking the user on network issues.

```bash
# Pull before any read:
git -C .neuroflow/flowie pull --rebase origin main || true

# After any write:
git -C .neuroflow/flowie add -A && git -C .neuroflow/flowie commit -m "..." && git -C .neuroflow/flowie push || true
```

Never use a staging/remote-sync subdirectory. The flowie directory is the repo.

---

## Step 0 — Check for .neuroflow/

If `.neuroflow/` does not exist, stop and tell the user to run `/neuroflow` first.

---

## Step 1 — Read project state

Read `.neuroflow/project_config.md` and `.neuroflow/flow.md`.

Check whether `.neuroflow/flowie/` exists:

- **If it does not exist** — this is first run. Go to Step 2.
- **If it exists** — pull latest from GitHub (`git -C .neuroflow/flowie pull --rebase origin main || true`), then read `sync.json` to confirm the linked GitHub repo and last sync time. Go to Step 3 (mode menu).

---

## Step 2 — First run: ask whether to set up flowie

Print:

```
flowie — personal research OS

Your flowie profile is a private GitHub repository that stores your research infrastructure:
  • research identity (stances, writing style, methodological preferences)
  • Kanban task board across all projects
  • project registry with phase timelines
  • ongoing ideas and hypotheses across projects

Claude reads this to personalize assistance and track where each project stands.

Set up or connect a flowie profile now? [Y/n]
```

If the user declines, stop. Do not create `.neuroflow/flowie/` or write anything.

If the user agrees, continue to Step 2a.

---

## Step 2a — GitHub authentication

Explain the GitHub requirements:

```
To use flowie, you need a GitHub account and one of:

  Option A — GitHub CLI (recommended if installed):
    Run: gh auth login
    Then come back and re-run /flowie.

  Option B — Personal Access Token (PAT):
    1. Go to: https://github.com/settings/tokens
    2. Create a new token with the "repo" scope.
    3. Store it somewhere safe — you will need it below.

Which option are you using? [A / B]
```

If Option A: check whether `gh auth status` succeeds. If it fails, ask the user to run `gh auth login` first and stop.

If Option B: ask for the PAT (stored only in memory, never written to disk). Store the token in a variable for use in subsequent git operations during this session.

Ask for the user's GitHub username (needed to construct the repo URL).

---

## Step 2b — Check for existing flowie repo

Using `gh` CLI or the GitHub API (with the PAT), check whether a private repository named `flowie` exists on the user's account.

If it exists:
```
Found an existing flowie repository on your GitHub account.
Connect to it? [Y/n]
```

If confirmed, set the repo URL and continue to Step 2c (clone path).

If it does not exist:
```
No flowie repository found on your GitHub account.
Create a new private repository named "flowie"? [Y/n]
```

If confirmed, create the repository:
- Using `gh repo create flowie --private` (if `gh` CLI is available)
- Or via the GitHub API: `POST /user/repos` with `{ "name": "flowie", "private": true }`

Confirm creation succeeded, then continue to Step 2c (init path).

---

## Step 2c — Initialise local flowie directory

**If connecting to an existing repo** (Step 2b found one):

```bash
git clone --depth 1 https://github.com/{username}/flowie .neuroflow/flowie
```

After cloning, scaffold any missing files/folders from the spec below without overwriting existing content.

**If creating a new repo** (Step 2b created one):

Create `.neuroflow/flowie/` and scaffold the full structure:

```
.neuroflow/flowie/
  .flow                          ← root index (neuroflow convention)
  profile.md                     ← research identity template
  ideas.md                       ← cross-project hypotheses template
  sync.json
  projects/
    .flow
    projects.json
  tasks/
    .flow
    config.json
    inbox/   .flow
    ready/   .flow
    active/  .flow
    review/  .flow
    meeting/ .flow
    done/    .flow
    archive/ .flow
  notes/
    .flow                        ← index of notes synced from /notes
  wellbeing/
    .flow
    config.json                  ← collect flag and metric definitions
```

**Root `.flow` file** (neuroflow index convention):

```markdown
# flowie

| file / folder | description |
|---|---|
| profile.md | research identity |
| ideas.md | cross-project hypotheses |
| sync.json | GitHub repo URL and last_synced |
| projects/ | project registry |
| tasks/ | Kanban task board |
| notes/ | notes synced from /notes sessions |
| wellbeing/ | daily wellbeing assessments |
```

**`sync.json`:**
```json
{
  "github_repo": "https://github.com/{username}/flowie",
  "last_synced": null
}
```

**`profile.md`:** (empty template)
```markdown
# Research Profile

## Identity
name:
research_domain:

## Methodological preferences
<!-- Tools, approaches, paradigms you prefer -->

## Writing style
<!-- How you write — register, density, hedging patterns -->

## Stances
<!-- Positions you hold on methodological debates -->

## Key beliefs
<!-- 3–5 beliefs about your field that guide your work -->
```

**`ideas.md`:** (empty template)
```markdown
# Ongoing ideas

Ideas and hypotheses that span multiple projects.

---
```

**`projects/.flow`:**
```markdown
# projects

| file | description |
|---|---|
| projects.json | machine index of all projects |
| {name}.md | per-project detail and phase timeline |
```

**`projects/projects.json`:**
```json
{
  "projects": []
}
```

**`tasks/.flow`:**
```markdown
# tasks

Kanban board — one folder per column, one .md file per task.
```

**`tasks/config.json`:**
```json
{
  "columns": [
    { "id": "inbox",   "label": "📥 Inbox",   "default": true },
    { "id": "ready",   "label": "🟢 Ready" },
    { "id": "active",  "label": "⚡ Active" },
    { "id": "review",  "label": "👁 Review" },
    { "id": "meeting", "label": "📅 Meeting" },
    { "id": "done",    "label": "✅ Done" },
    { "id": "archive", "label": "📦 Archive", "archive": true }
  ],
  "projects": {},
  "task_schema": {
    "required": ["title", "project"],
    "optional": ["phase", "due", "tags", "blocked_by"]
  },
  "archive_after_days": 90
}
```

Each column folder (`inbox/`, `ready/`, `active/`, `review/`, `meeting/`, `done/`, `archive/`) gets a `.flow` file:
```markdown
# {column-id}

Tasks in this column.
```

**`notes/.flow`:**
```markdown
# notes

| file | description |
|---|---|
```

**`wellbeing/.flow`:**
```markdown
# wellbeing

| file | description |
|---|---|
| config.json | collection settings |
```

**`wellbeing/config.json`:**
```json
{
  "collect": false,
  "metrics": [
    {"id": "anxiety",   "label": "Anxiety",   "scale": "1=none, 5=normal, 10=very high"},
    {"id": "energy",    "label": "Energy",    "scale": "1=depleted, 5=normal, 10=very high"},
    {"id": "happiness", "label": "Happiness", "scale": "1=very low, 5=normal, 10=very high"}
  ],
  "prompt_on_sync": true
}
```

Update `.neuroflow/flow.md` to add a row for `flowie/`.

**Init and push to GitHub:**

```bash
cd .neuroflow/flowie
git init
git remote add origin https://github.com/{username}/flowie
git add -A
git commit -m "init: scaffold flowie research OS"
git push -u origin main || true
```

Tell the user:
```
flowie directory created at .neuroflow/flowie/
GitHub repo linked: https://github.com/{username}/flowie

Run /flowie --init to build your research profile,
or /flowie --sync to pull an existing profile from GitHub.
```

Go to Step 3.

---

## Step 3 — Mode menu

If the user invoked the command with a mode flag, go directly to that mode. Otherwise, show the menu:

```
flowie — what would you like to do?

  --init        Build your research profile (interview-based)
  --sync        Pull from GitHub, then push local changes
  --link        Link this project to your flowie profile
  --view        Show your current profile summary
  --identify    Generate a "who you are" paragraph from existing data
  --tasks       Show Kanban board / manage tasks
  --projects    Show / manage project registry
  --assess      Log today's wellbeing (anxiety, energy, happiness 1–10)
  --credentials Show custom LLM settings as ready-to-paste export commands
```

Wait for the user to choose.

---

## Mode: --init

**Trigger:** user runs `/flowie --init` or selects from the menu, and there is no substantial content in `profile.md`.

If `profile.md` already contains meaningful content (more than the template headings), confirm before overwriting:
```
A profile already exists. Overwrite it with a fresh interview? [Y/n]
```

If the user confirms (or if the profile is empty), run the interview:

Ask each question one at a time. Do not rush.

1. *"What is your name?"*
2. *"What is your primary research domain? (e.g. cognitive neuroscience, clinical neurology, systems neuroscience)"*
3. *"What methods do you use most? List freely — paradigms, recording modalities, analysis tools, programming languages."*
4. *"How would you describe your writing style? (e.g. dense and technical, accessible, hedged, direct)"*
5. *"Are there any methodological stances you hold firmly? (e.g. preregistration is non-negotiable, Bayesian over frequentist, open data always)"*
6. *"List 3 to 5 beliefs you hold about your field that guide your research decisions. These can be controversial."*
7. *"Is there anything else you want Claude to know about how you think — your research values, pet peeves, or preferences?"*
8. *"Would you like to track your daily wellbeing — anxiety, energy, and happiness on a 1–10 scale? Claude will prompt you to fill in a rating each day when you sync flowie. [y/N]"*

   If yes: read `wellbeing/config.json`, set `collect` to `true`, write the file, then push:
   ```bash
   git -C .neuroflow/flowie add wellbeing/config.json && git -C .neuroflow/flowie commit -m "wellbeing: enable daily tracking" && git -C .neuroflow/flowie push || true
   ```

After collecting all answers, write a structured `profile.md`:

```markdown
# Research Profile

## Identity
name: {name}
research_domain: {domain}

## Methodological preferences
{methods, formatted as bullet list}

## Writing style
{writing style description}

## Stances
{stances as bullet list}

## Key beliefs
{beliefs as numbered list}

## Additional context
{anything extra from question 7, if provided}
```

Show the full profile to the user before writing it:
```
Here is your profile. Does this look right? [Y / edit]
```

If the user wants to edit, accept their corrections. Only write the file once they confirm.

After writing, push to GitHub:
```bash
git -C .neuroflow/flowie add profile.md && git -C .neuroflow/flowie commit -m "profile: initial build" && git -C .neuroflow/flowie push || true
```

Offer to sync to GitHub immediately if push fails:
```
Profile saved. Push to your flowie GitHub repo now? [Y/n]
```

---

## Mode: --sync

**Trigger:** user runs `/flowie --sync` or selects "Pull from GitHub, then push local changes".

Read `sync.json` for the repo URL. If it is missing, tell the user to run `/flowie` first to connect a repo.

### Pull step

```bash
git -C .neuroflow/flowie pull --rebase origin main || true
```

If the pull succeeds, report what changed (use `git -C .neuroflow/flowie diff --stat HEAD@{1} HEAD` to summarise).

- If nothing changed, report "No changes to pull."
- If there are changes, show a brief diff summary.

### Push step

Check for local uncommitted changes:

```bash
git -C .neuroflow/flowie status --short
```

If there are staged or unstaged changes:

```bash
git -C .neuroflow/flowie add -A && git -C .neuroflow/flowie commit -m "sync: {YYYY-MM-DD HH:MM}" && git -C .neuroflow/flowie push || true
```

Update `last_synced` in `sync.json` to current ISO 8601 timestamp, then commit the update:

```bash
git -C .neuroflow/flowie add sync.json && git -C .neuroflow/flowie commit -m "sync: update last_synced" && git -C .neuroflow/flowie push || true
```

### Wellbeing check

After the push step, read `wellbeing/config.json`. If `collect` is `true` and `prompt_on_sync` is `true`, check whether `wellbeing/{today}.json` exists. If it does not exist, run the `--assess` flow inline before reporting (see Mode: --assess). If it exists, skip silently.

Report:
```
Sync complete — {YYYY-MM-DD HH:MM}
  Pulled: {summary or "no changes"}
  Pushed: {N files or "nothing to push"}
  Last synced: {timestamp}
```

If push fails (e.g. auth error, network), report the error clearly and do not update `last_synced`.

---

## Mode: --credentials

**Trigger:** user runs `/flowie --credentials`.

Display the custom LLM settings from `flowie/integrations.json` as ready-to-run export commands, so the user can paste them into their terminal before starting Claude Code.

**Do not read from `.neuroflow/integrations.json`** (local file, contains the API key). Read only from `.neuroflow/flowie/integrations.json` (synced, non-secrets only).

**If `.neuroflow/flowie/integrations.json` does not exist or has no `custom_llm` section:**

> No custom LLM configured in your flowie profile. Run `/neuroflow:setup` and choose Step 5 to configure one.

**If it exists and `custom_llm` has `provider`, `base_url`, and `model` set:**

Show:

```
Custom LLM settings from your flowie profile:

  Provider:   {provider}
  Endpoint:   {base_url}
  Model:      {model}
  Proxy port: {proxy_port}  (shown only if set)

To activate — paste in your terminal before starting Claude Code:

  export ANTHROPIC_BASE_URL="{base_url}"
  export ANTHROPIC_API_KEY="<your-api-key>"

Or to persist across sessions, add to your ~/.zshrc or ~/.bashrc.

To use the proxy instead (for model selection):
  node <path-to-proxy.mjs> {model}                                    # Terminal 1
  ANTHROPIC_BASE_URL=http://localhost:{proxy_port} ANTHROPIC_API_KEY=any claude  # Terminal 2

Note: Your API key is stored locally in .neuroflow/integrations.json — it is never
synced to your flowie GitHub repo.
```

Do not write anything during `--credentials`. This is a read-only display mode.

---

## Mode: --link

**Trigger:** user runs `/flowie --link` or selects "Link this project to your flowie profile".

Pull first:
```bash
git -C .neuroflow/flowie pull --rebase origin main || true
```

After pulling, run the wellbeing check (same as in `--sync`): if `wellbeing/config.json` has `collect: true` and today's entry is missing, run `--assess` inline before continuing.

Read `projects/projects.json`. List the available projects:

```
Available projects in your flowie registry:

  1. AlphaModulation — EEG alpha modulation study [active]
  2. RT_DES — EEG RT-DES paradigm [active]
  3. (create new)

Which project does this neuroflow repo belong to? [1/2/3]
```

If the user selects an existing project:
- Write `flowie_project: {name}` to `.neuroflow/project_config.md` (replacing any existing `flowie_project:` or old `flowie_profile:` field)
- Open `projects/{name}.md`, add the current repo path under a `## Linked repos` section if not already present

If the user selects "create new", run `--projects --add` inline to register the project first, then link.

Confirm to the user:
```
This project is now linked to {name} in your flowie registry.
Claude will read your profile and project registry when assisting in any neuroflow phase.
```

Push changes:
```bash
git -C .neuroflow/flowie add -A && git -C .neuroflow/flowie commit -m "link: {project} ← {repo-basename}" && git -C .neuroflow/flowie push || true
```

Write to `sessions/YYYY-MM-DD.md`.

---

## Mode: --view

**Trigger:** user runs `/flowie --view` or selects "Show your current profile summary".

Pull first:
```bash
git -C .neuroflow/flowie pull --rebase origin main || true
```

Read `.neuroflow/flowie/profile.md`. Display it formatted:

```
─────────────────────────────────────
  flowie profile
─────────────────────────────────────
  Name:    {name}
  Domain:  {research_domain}

  Methods:  {bullet list, indented}

  Writing:  {style description}

  Stances:  {bullet list}

  Beliefs:  {numbered list}

  Last synced: {sync.json.last_synced or "never"}
─────────────────────────────────────
```

If `profile.md` does not exist or is empty, tell the user to run `/flowie --init` first.

Do not write anything during `--view`.

---

## Mode: --identify

**Trigger:** user runs `/flowie --identify` or selects "Generate a 'who you are' paragraph from existing data".

Pull first:
```bash
git -C .neuroflow/flowie pull --rebase origin main || true
```

Read all files in `.neuroflow/flowie/`. Also read `.neuroflow/project_config.md` and any reasoning logs in `.neuroflow/reasoning/` to gather additional signal about how the user thinks.

Generate a short "who you are" paragraph — 4 to 6 sentences — describing the user's intellectual identity from the evidence available. (This length is intentional: short enough for the user to read and confirm in one pass, long enough to capture the two or three most distinctive traits without flattening nuance into a single generic line.)

```
Based on your profile and project history, here is how I understand you:

{paragraph — e.g. "You are a cognitive neuroscientist working primarily with EEG and
eye-tracking data. Your methods are systematic: you preregister before collecting,
prefer Bayesian inference for small samples, and are skeptical of vague theoretical
constructs. Your writing is dense and precise — you hedge only when the evidence
genuinely warrants it. You are particularly interested in attention systems and
have a running tension with the way 'working memory' is defined in the literature."}

Is this accurate? [Y / correct it]
```

If the user corrects it, incorporate their corrections. Then ask:

```
Update your profile with this description? [Y/n]
```

If yes, append a `## Claude's read` section to `profile.md` with the confirmed paragraph, then push:
```bash
git -C .neuroflow/flowie add profile.md && git -C .neuroflow/flowie commit -m "profile: add Claude's read" && git -C .neuroflow/flowie push || true
```

---

## Mode: --tasks

**Trigger:** user runs `/flowie --tasks` (with or without sub-flags).

Pull first:
```bash
git -C .neuroflow/flowie pull --rebase origin main || true
```

Read `tasks/config.json` for column definitions. Read all `.md` files from all column folders (excluding `.flow`).

### --tasks (no sub-flag) — ASCII Kanban board

Show the non-archive columns as a horizontal board. Show at most 5 tasks per column, truncated to 20 chars. Always show the done count at the bottom. Apply `--project` filter if provided.

```
┌─ 📥 Inbox ──────────┐  ┌─ ⚡ Active ──────────┐  ┌─ 👁 Review ──────────┐
│ spin-tests-5ht2a    │  │ fix-rt-glasses       │  │ grant-draft          │
│ ethics-form         │  │ eeg-param-sweep      │  │                      │
└─────────────────────┘  └──────────────────────┘  └──────────────────────┘
[done: 3 tasks]
```

Omit empty columns unless they are `inbox` or `active`. Show `meeting` and `ready` only if they contain tasks.

### --tasks --list

Flat list of all tasks across all non-archive columns, sorted by column order then by `due` date (soonest first, undated tasks last).

```
[inbox]   spin-tests-5ht2a     AlphaModulation  due: 2026-04-15
[inbox]   ethics-form          RT_DES           due: —
[active]  fix-rt-glasses       RT_DES           due: 2026-04-10
[active]  eeg-param-sweep      AlphaModulation  due: —
[review]  grant-draft          AlphaModulation  due: 2026-04-20
```

### --tasks --add

Before starting, run the wellbeing check: if `wellbeing/config.json` has `collect: true` and today's entry is missing, run `--assess` inline before proceeding.

Mini interview to create a new task. Ask:

1. *"Task title?"*
2. *"Which project? (list projects from projects.json)"*
3. *"Phase? (optional — press enter to skip)"*
4. *"Due date? (YYYY-MM-DD, optional)"*
5. *"Tags? (comma-separated, optional)"*
6. *"Blocked by? (comma-separated slugs, optional)"*

Generate slug from title: lowercase, spaces to hyphens, strip special chars, max 40 chars.

Write task file to `tasks/inbox/{slug}.md`:

```markdown
---
title: {title}
project: {project}
phase: {phase or omit}
created: {YYYY-MM-DD}
due: {due or omit}
tags: [{tags or empty}]
blocked_by: [{blocked_by or empty}]
---

## Context


## Links

```

Confirm:
```
Task created: tasks/inbox/{slug}.md
```

Push:
```bash
git -C .neuroflow/flowie add tasks/inbox/{slug}.md && git -C .neuroflow/flowie commit -m "task: add {slug}" && git -C .neuroflow/flowie push || true
```

### --tasks --move \<slug\> \<column\>

Move a task file from its current column folder to the target column folder.

1. Find `{slug}.md` across all column folders
2. If not found, report "Task not found: {slug}"
3. If found, move: `git -C .neuroflow/flowie mv tasks/{current}/{slug}.md tasks/{column}/{slug}.md`
4. Commit and push:
   ```bash
   git -C .neuroflow/flowie commit -m "task: move {slug} → {column}" && git -C .neuroflow/flowie push || true
   ```
5. Confirm: `Moved {slug} → {column}`

### --tasks --done \<slug\>

Shorthand for `--tasks --move {slug} done`. Move the task to `tasks/done/`.

### --tasks --archive

Manual archive sweep. Read all tasks in `tasks/done/`. For each task, check `created` date. If the task has been in done/ for more than `archive_after_days` (from config.json, default 90), move it to `tasks/archive/`.

Report:
```
Archive sweep complete.
  Moved to archive: {N} tasks
  Kept in done: {M} tasks (not yet {archive_after_days} days old)
```

Push all moves in a single commit:
```bash
git -C .neuroflow/flowie add -A && git -C .neuroflow/flowie commit -m "tasks: archive sweep {YYYY-MM-DD}" && git -C .neuroflow/flowie push || true
```

### --tasks --project \<name\>

Filter the board (or list, if combined with `--list`) to show only tasks where `project:` matches `{name}`. Applies to `--tasks` (board view) and `--tasks --list`.

---

## Mode: --projects

**Trigger:** user runs `/flowie --projects` (with or without sub-flags).

Pull first:
```bash
git -C .neuroflow/flowie pull --rebase origin main || true
```

Read `projects/projects.json`.

### --projects (no sub-flag) — ASCII phase timeline

Display all projects as an ASCII phase timeline. For each project, show current phase (◉), visited phases (✓), and upcoming phases (·). Use the standard neuroflow phase sequence:

`ideation → preregistration → experiment → data → analyze → paper → review`

```
AlphaModulation [active]
  repos: github.com/user/alpha-modulation — Main analysis codebase
  [ideation ✓]→[experiment ✓]→[data ✓]→[analyze ◉]→[paper ·]

RT_DES [active]
  repos: github.com/user/rt-des — EEG RT-DES paradigm
  [ideation ✓]→[experiment ◉]→[data ·]
```

Only show phases that have been visited or are current/future relative to `current_phase`. Skip phases not yet reached and not in `visited_phases` unless `current_phase` is past them (show all visited + current + one next).

### --projects --add

Before starting, run the wellbeing check: if `wellbeing/config.json` has `collect: true` and today's entry is missing, run `--assess` inline before proceeding.

Register a new project. Ask:

1. *"Project ID (short name, no spaces — e.g. AlphaModulation)?"*
2. *"Description (one line)?"*
3. *"GitHub repo URL(s)? (comma-separated, or press enter to skip)"*
   - For each URL, ask: *"Brief description of this repo?"*
4. *"Current phase? (ideation / preregistration / experiment / data / analyze / paper / review)"*
5. *"Status? [active / paused / complete]"*

Build the project entry:

```json
{
  "id": "{id}",
  "description": "{description}",
  "repos": [
    { "url": "{url}", "description": "{repo description}" }
  ],
  "current_phase": "{phase}",
  "visited_phases": [
    { "phase": "{phase}", "entered": "{YYYY-MM-DD}" }
  ],
  "status": "{status}"
}
```

Append to `projects/projects.json`.

Create `projects/{id}.md`:

```markdown
# {id}

{description}

## Repos

| url | description |
|---|---|
| {url} | {repo description} |

## Phase timeline

| phase | entered | notes |
|---|---|---|
| {phase} | {YYYY-MM-DD} | initial |

## Notes

```

Confirm:
```
Project registered: {id}
```

Push:
```bash
git -C .neuroflow/flowie add projects/projects.json projects/{id}.md && git -C .neuroflow/flowie commit -m "projects: add {id}" && git -C .neuroflow/flowie push || true
```

---

## Mode: --assess

**Trigger:** user runs `/flowie --assess`, or invoked automatically when `collect: true` and today's entry is missing (during `--sync`, `--link`, `--tasks --add`, `--projects --add`).

Pull first (skip if already pulled this session).

Read `wellbeing/config.json`. If `collect` is `false`:

```
Wellbeing tracking is disabled. Enable it? [y/N]
```

If yes: set `collect: true`, write `wellbeing/config.json`, push. If no: stop.

Check whether `wellbeing/{today}.json` exists. If it already exists:

```
Wellbeing already logged for today ({today}). Update it? [y/N]
```

If no: stop.

Ask each metric one at a time:

```
Anxiety today? (1=none, 5=normal, 10=very high) [1–10]:
Energy today? (1=depleted, 5=normal, 10=very high) [1–10]:
Happiness today? (1=very low, 5=normal, 10=very high) [1–10]:
Any notes? (optional — press enter to skip):
```

Validate that each score is an integer 1–10. Re-ask if invalid.

Write `wellbeing/{today}.json`:

```json
{
  "date": "{today}",
  "anxiety": N,
  "energy": N,
  "happiness": N,
  "notes": ""
}
```

Update `wellbeing/.flow` — append a row: `| {today}.json | wellbeing entry |`.

Push:
```bash
git -C .neuroflow/flowie add wellbeing/{today}.json wellbeing/.flow && git -C .neuroflow/flowie commit -m "wellbeing: {today}" && git -C .neuroflow/flowie push || true
```

Confirm: `Wellbeing logged for {today}.`

---

## Phase sync (called programmatically by /phase)

This section is invoked automatically when the active phase in `project_config.md` changes. It is not a user-facing mode — `/phase` calls this logic after updating its own state.

1. Read `flowie_project` from `.neuroflow/project_config.md`. If the field is not present or empty, skip silently.
2. Pull:
   ```bash
   git -C .neuroflow/flowie pull --rebase origin main || true
   ```
3. Read `projects/projects.json`. Find the project entry where `id` matches `flowie_project`.
   - Update `current_phase` to the new phase.
   - If the new phase is not already in `visited_phases`, append `{ "phase": "{new_phase}", "entered": "{YYYY-MM-DD}" }`.
4. Write the updated `projects/projects.json`.
5. Read `projects/{name}.md`. Append a new row to the Phase timeline table:
   ```
   | {new_phase} | {YYYY-MM-DD} | — |
   ```
6. Commit and push:
   ```bash
   git -C .neuroflow/flowie add projects/projects.json projects/{name}.md && git -C .neuroflow/flowie commit -m "phase: {project} → {new_phase}" && git -C .neuroflow/flowie push || true
   ```

If any step fails (file not found, JSON parse error), fail silently and log the error only to the session file. Do not surface the error to the user during a `/phase` run — flowie sync is a background concern.

---

## Privacy rules

- Never print the PAT to the terminal or write it to any file.
- The `flowie` repo must be private. Do not confirm or suggest making it public.
- Do not log task content, project details, or profile contents to `.neuroflow/sessions/` beyond the one-line summary.

---

## At end

Append to `.neuroflow/sessions/YYYY-MM-DD.md`:

```
[HH:MM] /flowie — {mode}: {brief summary of what happened}
```

Examples:
- `[14:22] /flowie — --init: built initial profile for {name}`
- `[14:45] /flowie — --sync: pulled 3 changes from GitHub, pushed 1 file`
- `[15:01] /flowie — --link: linked current project to AlphaModulation`
- `[15:10] /flowie — --view: displayed profile`
- `[15:18] /flowie — --identify: generated identity paragraph, user confirmed`
- `[15:30] /flowie — --tasks: showed Kanban board (5 tasks across 3 columns)`
- `[15:35] /flowie — --tasks --add: created task spin-tests-5ht2a in inbox`
- `[15:40] /flowie — --tasks --move: moved fix-rt-glasses → active`
- `[16:00] /flowie — --projects: showed phase timeline for 2 projects`
- `[16:10] /flowie — --projects --add: registered project RT_DES`
