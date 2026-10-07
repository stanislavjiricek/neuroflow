---
name: flowie
description: Personal research OS — link a private GitHub repository to store your research profile, cross-project Kanban task board, project registry, and personal wiki. Supports profile creation, task management, project registry, GitHub sync, phase auto-tracking, credential export, and LLM-maintained personal knowledge base.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/tasks/**
  - ~/.neuroflow/flowie/profile.md
  - ~/.neuroflow/flowie/ideas.md
  - ~/.neuroflow/flowie/sync.json
  - ~/.neuroflow/flowie/tasks/config.json
  - ~/.neuroflow/flowie/projects/projects.json
  - ~/.neuroflow/flowie/wellbeing/config.json
  - ~/.neuroflow/flowie/wellbeing/*.json
  - ~/.neuroflow/flowie/wiki/schema.md
  - ~/.neuroflow/flowie/wiki/index.md
  - ~/.neuroflow/flowie/wiki/log.md
  - ~/.neuroflow/flowie/wiki/pages/**
  - ~/.neuroflow/local-projects.json
  - ~/.neuroflow/flowie-sync.log
  - skills/wiki-protocol/SKILL.md
writes:
  - ~/.neuroflow/flowie/profile.md
  - ~/.neuroflow/flowie/ideas.md
  - ~/.neuroflow/flowie/sync.json
  - ~/.neuroflow/flowie/tasks/**
  - .neuroflow/tasks/**
  - ~/.neuroflow/flowie/projects/projects.json
  - ~/.neuroflow/flowie/projects/*.md
  - ~/.neuroflow/flowie/notes/
  - ~/.neuroflow/flowie/wellbeing/config.json
  - ~/.neuroflow/flowie/wellbeing/*.json
  - ~/.neuroflow/flowie/wiki/
  - ~/.neuroflow/local-projects.json
  - ~/.neuroflow/flowie-sync.log
  - .neuroflow/project_config.md
  - .neuroflow/sessions/YYYY-MM-DD.md
lifecycle: light
---

# /flowie

Personal research OS for neuroflow. Links the current project to a private GitHub repository — the user's `flowie` repo — which stores four layers of research infrastructure:

1. **Identity layer** — `profile.md`, `ideas.md`: research stances, writing style, methodological preferences, cross-project hypotheses
2. **Kanban task board** — `tasks/`: column-per-folder, task-per-.md-file, ASCII board view (format and board rules: `/tasks`)
3. **Project registry** — `projects/`: `projects.json` machine index + one `{name}.md` per project with phase timeline
4. **Personal wiki** — `wiki/`: LLM-maintained knowledge base with indexed pages, source summaries, concept synthesis, and method library

The `flowie` directory at `~/.neuroflow/flowie/` **is the git repo itself** — cloned from GitHub. GitHub is canonical. Pull before every read, push after every write.

Read the `neuroflow:phase-flowie` skill first. For any `--wiki-*` mode, also read the `neuroflow:wiki-protocol` skill. Then follow the neuroflow-core lifecycle: read `project_config.md` and `flow.md` before starting.

Flowie is fully optional. Nothing breaks if it is not set up.

---

## Git operations pattern

All git operations use the `-C` flag to target the flowie repo directory. Network failures never block the person — but they are reported, not swallowed.

**Pull** (before any read):

```bash
git -C ~/.neuroflow/flowie pull --rebase
```

If the pull stops on a conflict, run `git -C ~/.neuroflow/flowie rebase --abort` — never leave a half-finished rebase — tell the person, and resolve it with them in `--sync`. If it fails for network reasons, say so once and carry on with the local copy.

**Sync** (after a write) — `{paths}` are exactly the files this mode changed:

```bash
git -C ~/.neuroflow/flowie add -- {paths}
git -C ~/.neuroflow/flowie commit -m "{message}" -- {paths}   # "nothing to commit" is fine: the auto-sync hook already did it
git -C ~/.neuroflow/flowie pull --rebase && git -C ~/.neuroflow/flowie push
```

<!-- nf-rule: GIT-NO-SECRETS -->
Never `git add -A`, never stage `integrations.json`. If the pull stops on a conflict, abort it as above and leave the push for `--sync`.

Files written with Edit/Write are synced by the plugin's **flowie auto-sync hook**: it commits that one file, pulls with rebase, then pushes. It skips `integrations.json` and gitignored files, does nothing while a rebase or merge is in progress, and never blocks — each failure is appended as one line to `~/.neuroflow/flowie-sync.log` (machine-local, never synced). The Sync step above still runs for every write, so the prose works with hooks disabled, and it is the only thing that commits changes made through Bash (`git mv`, deletions).

Never use a staging/remote-sync subdirectory. The flowie directory is the repo.

---

## Step 0 — Check for .neuroflow/

If `.neuroflow/` does not exist, stop and tell the user to run `/neuroflow` first.

---

## Step 1 — Read project state

Read `.neuroflow/project_config.md` and `.neuroflow/flow.md`.

Check whether `~/.neuroflow/flowie/` exists:

- **If it does not exist** — this is first run. Go to Step 2.
- **If it exists** — pull latest from GitHub (Git operations pattern), then read `sync.json` to confirm the linked GitHub repo and last sync time. If `~/.neuroflow/flowie-sync.log` exists and is not empty, tell the person once: *"{N} flowie auto-sync failure(s) since {first timestamp} — run `/flowie --sync` to resolve."* Go to Step 3 (mode menu).

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

If the user declines, stop. Do not create `~/.neuroflow/flowie/` or write anything.

If the user agrees, continue to Step 2a.

---

## Step 2a — GitHub authentication

Explain the GitHub requirements:

```
To use flowie, you need a GitHub account and one of:

  Option A — GitHub CLI (recommended if installed):
    Run: gh auth login
    Then come back and re-run /flowie.

  Option B — git with a stored GitHub credential:
    Store a GitHub credential for git yourself, in your own terminal
    (your git credential manager, or: git credential approve).
    Then come back and re-run /flowie.

Never paste a token into this chat — neuroflow never asks for one.

Which option are you using? [A / B]
```

If Option A: check whether `gh auth status` succeeds. If it fails, ask the user to run `gh auth login` first and stop.

If Option B: never ask for a token in chat — git uses the credential the person stored in their own terminal. Step 2b's `git ls-remote` shows whether it works; if it does not, ask the person to store the credential in their own terminal (`git credential approve`, or their credential manager), then retry Step 2b once.

Ask for the user's GitHub username (needed to construct the repo URL).

---

## Step 2b — Check for existing flowie repo

Check whether a private repository named `flowie` exists on the user's account: `gh repo view {username}/flowie` (Option A) or `GIT_TERMINAL_PROMPT=0 git ls-remote https://github.com/{username}/flowie.git` (Option B). With Option B a failure can also mean the stored credential is missing, so ask the person whether the repository exists before treating it as missing.

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
- Otherwise (Option B), ask the person to create it on GitHub themselves — a new **private** repository named `flowie`, empty (no README, `.gitignore` or license) — and to say when it is done

Confirm creation succeeded, then continue to Step 2c (init path).

---

## Step 2c — Initialise local flowie directory

**If connecting to an existing repo** (Step 2b found one):

```bash
git clone --depth 1 https://github.com/{username}/flowie ~/.neuroflow/flowie
```

After cloning, scaffold any missing files/folders from the spec below without overwriting existing content. If `.gitignore` exists but does not list `integrations.json`, append that line.

**If creating a new repo** (Step 2b created one):

Create `~/.neuroflow/flowie/` and scaffold the full structure:

```
~/.neuroflow/flowie/
  .flow                          ← root index (neuroflow convention)
  .gitignore                     ← integrations.json (never synced)
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
email:
research_domain:
hives: []          # list of hive repos this person is a member of: [{org}/{repo}, ...]

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

> The canonical 3-tier task-board spec (levels, task frontmatter, rendering rules) lives in `/tasks` (`commands/tasks.md`). `--tasks` here is the flowie-level entry point to that spec.

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
    "required": ["title", "status", "created", "updated", "project"],
    "optional": ["owner", "due", "phase", "tags", "blocked_by", "source"]
  },
  "archive_after_days": 90
}
```

`task_schema` mirrors the one task format defined in `/tasks` — that file wins if they ever disagree.

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

**`.gitignore`:**
```
integrations.json
```

**Init and push to GitHub** (stage the scaffold by name — never `git add -A`):

```bash
cd ~/.neuroflow/flowie
git init -b main
git remote add origin https://github.com/{username}/flowie
git add -- .gitignore .flow profile.md ideas.md sync.json projects tasks notes wellbeing
git commit -m "init: scaffold flowie research OS"
git push -u origin main
```

If the push fails, say why (auth, network) and leave it for `/flowie --sync`.

Tell the user:
```
flowie directory created at ~/.neuroflow/flowie/
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

  Personal wiki (powered by neuroflow:wiki-protocol skill):
  --wiki        Show wiki overview — page count, recent activity, index summary
  --wiki-ingest Ingest a new source into your wiki
  --wiki-query  Ask a question answered from your wiki
  --wiki-lint   Health-check the wiki — orphans, contradictions, stale pages
  --wiki-add    Manually create or update a wiki page
  --wiki-schema View or update the wiki's operating conventions
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
8. *"Which team Hives are you a member of? (list as {org}/{repo}, comma-separated — or press Enter to skip)"*

   Store the list as `hives: [{org}/{repo}, ...]` in `profile.md`. This lets `/hive --init` offer to pre-fill the hive repo when a project is connected to one of the listed hives.

9. *"Would you like to track your daily wellbeing — anxiety, energy, and happiness on a 1–10 scale? Claude will prompt you to fill in a rating each day when you sync flowie. [y/N]"*

   If yes: read `wellbeing/config.json`, set `collect` to `true`, write the file, then Sync `wellbeing/config.json` (`wellbeing: enable daily tracking`).

After collecting all answers, write a structured `profile.md`:

```markdown
# Research Profile

## Identity
name: {name}
email: {email or omit if not given}
research_domain: {domain}
hives: [{org}/{repo}, ...}]   # omit if none given

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

After writing, Sync `profile.md` (`profile: initial build`).

Offer to sync to GitHub immediately if push fails:
```
Profile saved. Push to your flowie GitHub repo now? [Y/n]
```

---

## Mode: --sync

**Trigger:** user runs `/flowie --sync` or selects "Pull from GitHub, then push local changes".

Read `sync.json` for the repo URL. If it is missing, tell the user to run `/flowie` first to connect a repo.

### Pull step

Pull (Git operations pattern). If the pull succeeds, report what changed (use `git -C ~/.neuroflow/flowie diff --stat HEAD@{1} HEAD` to summarise).

- If nothing changed, report "No changes to pull."
- If there are changes, show a brief diff summary.

If the pull stops on a conflict, run `git -C ~/.neuroflow/flowie rebase --abort`, show the conflicting files with both versions side by side (local vs `git -C ~/.neuroflow/flowie show @{u}:{path}`), and agree each one with the person. Then pull again, write the agreed version of each conflicting file, `git add` it and `git rebase --continue` — never pick a side silently, and push nothing before the rebase is finished (phase-flowie → GitHub sync protocol).

### Push step

Check for local uncommitted changes and unpushed commits:

```bash
git -C ~/.neuroflow/flowie status --short
git -C ~/.neuroflow/flowie rev-list --count @{u}..HEAD
```

If files changed, list them for the person, then Sync exactly those paths (`sync: {YYYY-MM-DD HH:MM}`) — never `add -A`, never `integrations.json`. If only unpushed commits remain, push them.

Update `last_synced` in `sync.json` to the current ISO 8601 timestamp, then Sync `sync.json` (`sync: update last_synced`).

### Auto-sync log

If `~/.neuroflow/flowie-sync.log` has lines, show them (newest last). Once the pull and the push above have both succeeded, the failures it records are resolved: empty the file. If either step failed, leave the log as it is.

### Wellbeing check

After the push step, read `wellbeing/config.json`. If `collect` is `true` and `prompt_on_sync` is `true`, check whether `wellbeing/{today}.json` exists. If it does not exist, run the `--assess` flow inline before reporting (see Mode: --assess). If it exists, skip silently.

Report:
```
Sync complete — {YYYY-MM-DD HH:MM}
  Pulled: {summary or "no changes"}
  Pushed: {N files or "nothing to push"}
  Auto-sync failures: {N cleared, or "none"}
  Last synced: {timestamp}
```

If push fails (e.g. auth error, network), report the error clearly and do not update `last_synced`.

---

## Mode: --credentials

**Trigger:** user runs `/flowie --credentials`.

Display the custom LLM settings from `flowie/integrations.json` as ready-to-run export commands, so the user can paste them into their terminal before starting Claude Code.

Read only from `~/.neuroflow/flowie/integrations.json` (non-secret settings only). No `integrations.json` holds the gateway key: the person's launch command reads it from their key file (`skills/setup-guide/references/custom-gateway.md` → Storing the key).

**If `~/.neuroflow/flowie/integrations.json` does not exist or has no `custom_llm` section:**

> No custom LLM configured in your flowie profile. Run `/neuroflow:setup` and choose Step 4 to configure one.

**If it exists and `custom_llm` has `provider`, `base_url`, and `model` set:**

Show:

```
Custom LLM settings from your flowie profile:

  Provider:   {provider}
  Endpoint:   {base_url}
  Model:      {model}
  Proxy port: {proxy_port}  (shown only if set)

To activate — paste in your terminal before starting Claude Code (the key is read
from your key file; change the path if yours is elsewhere):

  export ANTHROPIC_BASE_URL="{base_url}"
  export ANTHROPIC_AUTH_TOKEN="$(cat ~/.claude-gateway/gateway-key)"

Or to persist across sessions, add to your ~/.zshrc or ~/.bashrc.

To use the proxy instead (for model selection):
  GATEWAY_URL="{base_url}" GATEWAY_KEY="$(cat ~/.claude-gateway/gateway-key)" node <path-to-proxy.mjs> {model} {proxy_port}  # Terminal 1
  ANTHROPIC_BASE_URL=http://localhost:{proxy_port} ANTHROPIC_AUTH_TOKEN=dummy claude  # Terminal 2

Note: neuroflow never stores your gateway key — integrations.json holds non-secret
settings only. Full launch command, Windows PowerShell version and model mapping:
skills/setup-guide/references/custom-gateway.md.
```

Do not write anything during `--credentials`. This is a read-only display mode.

---

## Mode: --link

**Trigger:** user runs `/flowie --link` or selects "Link this project to your flowie profile".

Pull first (Git operations pattern).

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
- Read `.neuroflow/project_config.md`. If a `flowie_profiles:` list already exists, append a new entry `- handle: {username}\n  repo: {username}/flowie` if this handle is not already present. If no `flowie_profiles:` list exists, add one (replacing any legacy `flowie_project:` or `flowie_profile:` scalar field). The entry for the user who ran `--link` becomes the first entry if the list was empty.
- Open `projects/{name}.md` and, under a `## Linked repos` section, add this repo's remote URL (`git remote get-url origin`) if it has one and it is not listed yet. Never write the local folder path there — flowie syncs to every machine you use.
- Record the local folder in the machine-local registry `~/.neuroflow/local-projects.json` (create it if missing; it lives outside the flowie repo and is never committed or synced). One entry per local folder, forward slashes; if the path is already listed, update `last_opened`:
  ```json
  {
    "projects": [
      { "name": "AlphaModulation", "path": "/home/me/code/alpha-modulation", "remote": "https://github.com/me/alpha-modulation", "last_opened": "2026-10-07" }
    ]
  }
  ```
  `name` is the flowie project id; `remote` is optional.

If the user selects "create new", run `--projects --add` inline to register the project first, then link.

Confirm to the user:
```
This project is now linked to {name} in your flowie registry.
Claude will read your profile and project registry when assisting in any neuroflow phase.
```

Sync `projects/{name}.md` if it changed (`link: {project} ← {repo-basename}`). `~/.neuroflow/local-projects.json` is never staged.

Write to `sessions/YYYY-MM-DD.md`.

---

## Mode: --view

**Trigger:** user runs `/flowie --view` or selects "Show your current profile summary".

Pull first (Git operations pattern).

Read `~/.neuroflow/flowie/profile.md`. Display it formatted:

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

Pull first (Git operations pattern).

Read all files in `~/.neuroflow/flowie/`. Also read `.neuroflow/project_config.md` and any reasoning logs in `.neuroflow/reasoning/` to gather additional signal about how the user thinks.

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

If yes, append a `## Claude's read` section to `profile.md` with the confirmed paragraph, then Sync `profile.md` (`profile: add Claude's read`).

---

## Mode: --tasks

**Trigger:** user runs `/flowie --tasks` (with or without sub-flags).

`/flowie --tasks [sub-flags]` is `/tasks --level flowie [sub-flags]`: follow `commands/tasks.md` exactly — the task file format (`tasks/{column}/{slug}.md` with `status`, `owner`, `updated`, …), the columns, the modes (`--list`, `--add`, `--move`, `--done`, `--archive`, `--project`), moves, and the mandatory ASCII board. This section only adds what is specific to flowie:

- **Default level is `flowie`.** `--level project` and `--level hive` behave exactly as in `/tasks`.
- Pull first (Git operations pattern). Column labels come from `tasks/config.json` when it exists.
- `--add` at flowie level: `project` is required — suggest the current repo's entry in `~/.neuroflow/local-projects.json`, else the projects in `projects/projects.json`. Before `--add`, run the wellbeing check: if `wellbeing/config.json` has `collect: true` and today's entry is missing, run `--assess` inline first.
- New and edited task files are synced by the auto-sync hook and the Sync step; moves and the archive sweep are committed by path as in `/tasks` → Moves.

---

## Mode: --projects

**Trigger:** user runs `/flowie --projects` (with or without sub-flags).

Pull first (Git operations pattern).

Read `projects/projects.json`, and `~/.neuroflow/local-projects.json` if it exists (where each project lives on this machine).

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

If the project has an entry in `~/.neuroflow/local-projects.json`, add a `local: {path}` line under its repos — or `local: {path} (not found on this machine)` when the folder is gone. Never delete a registry entry unless the person asks.

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

Sync `projects/projects.json projects/{id}.md` (`projects: add {id}`).

---

## Mode: --assess

**Trigger:** user runs `/flowie --assess`, or invoked automatically when `collect: true` and today's entry is missing (during `--sync`, `--link`, `--tasks --add`, `--projects --add`).

Pull first (skip if already pulled this session).

Read `wellbeing/config.json`. If `collect` is `false`:

```
Wellbeing tracking is disabled. Enable it? [y/N]
```

If yes: set `collect: true`, write `wellbeing/config.json`, Sync it. If no: stop.

Wellbeing is opt-in and self-reported: record exactly what the person answers — never estimate, suggest or pre-fill a score.

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

Sync `wellbeing/{today}.json wellbeing/.flow` (`wellbeing: {today}`).

Confirm: `Wellbeing logged for {today}.`

---

---

## Wiki modes — `--wiki-*`

All wiki modes load the `neuroflow:wiki-protocol` skill and follow its full operation workflows. The wiki lives at `~/.neuroflow/flowie/wiki/`. The skill file defines all page formats, index/log conventions, ingest/query/lint/add workflows, and the neuroflow-specific integrations (project tagging, ideas.md sync, profile evolution, fails integration).

Pull before every wiki read operation (Git operations pattern).

After every wiki write, Sync the pages, `index.md` and `log.md` that the operation changed (`wiki: {description}`) — by path, never `add -A`.

### Mode: --wiki

Show the wiki at a glance:

1. Read `wiki/index.md` (if exists) — report page count by type
2. Read last 5 lines of `wiki/log.md` — show recent activity
3. Print:

```
wiki — personal knowledge base
  Pages:  {N total} ({n} concepts, {n} sources, {n} synthesis, {n} entities, {n} methods)
  Recent: {last 5 log entries}
  Size:   {raw/ folder: N files}

  --wiki-ingest   Add a new source
  --wiki-query    Ask a question
  --wiki-lint     Health check
  --wiki-add      Create a page manually
  --wiki-schema   View/edit wiki conventions
```

If `wiki/` does not exist: tell the user and offer to initialize via `--wiki-schema`.

### Mode: --wiki-ingest [path|text]

Load `neuroflow:wiki-protocol` skill. Follow the **Ingest workflow** defined there. Key steps:

1. Read `schema.md` (create starter via interview if missing — this initializes the wiki)
2. Read the source file or accept pasted text from the user
3. Discuss: ask what to emphasize, any framing context
4. **Read `projects/projects.json`** → suggest active project names → ask for `projects:` tags (mandatory — always ask)
5. Write source page, update affected pages, create missing concept/entity/method pages, update `index.md`, append to `log.md`
6. Push to GitHub
7. After ingest: ask whether it cross-links to `ideas.md` or warrants a `profile.md` stance update

If no path or text provided, ask: "What would you like to ingest? (paste text, or give me a file path)"

### Mode: --wiki-query [question]

Load `neuroflow:wiki-protocol` skill. Follow the **Query workflow** defined there. Key steps:

1. Read `schema.md` + `index.md`
2. Identify and read relevant pages
3. Synthesize answer with citations
4. Ask whether to file the answer as a synthesis page (with `projects:` tagging)
5. Append to `log.md`, push if anything written

If no question provided, ask: "What would you like to know from your wiki?"

### Mode: --wiki-lint

Load `neuroflow:wiki-protocol` skill. Follow the **Lint workflow** defined there. Check for: orphan pages, stale pages, missing concept pages, missing project tags, log/page mismatches, cross-reference gaps, methods without fails check. Report findings and offer iterative fixes.

### Mode: --wiki-add [title]

Load `neuroflow:wiki-protocol` skill. Follow the **Add workflow** defined there. Guides the user through creating or updating a specific page with type, tags, project links, and body content.

### Mode: --wiki-schema

Load `neuroflow:wiki-protocol` skill. Follow the **Schema workflow** defined there. If `wiki/` does not exist, run **Initialization** to scaffold the full structure and generate a starter `schema.md` through a brief interview.

---

## Phase sync (called programmatically by /phase)

This section is invoked automatically when `active_phase` in `project_config.md` changes. It is not a user-facing mode — `/phase` calls this logic after updating its own state.

1. Read `flowie_profiles` from `.neuroflow/project_config.md`. Use the first entry (`flowie_profiles[0]`). If the list is absent or empty, skip silently.
2. Pull (Git operations pattern).
3. Read `projects/projects.json`. Find the linked project: the `name` of this repo's entry in `~/.neuroflow/local-projects.json`, else the entry whose `repos[].url` matches this repo's remote URL. If neither matches, skip silently.
   - Update `current_phase` to the new phase.
   - If the new phase is not already in `visited_phases`, append `{ "phase": "{new_phase}", "entered": "{YYYY-MM-DD}" }`.
4. Write the updated `projects/projects.json`.
5. Read `projects/{name}.md`. Append a new row to the Phase timeline table:
   ```
   | {new_phase} | {YYYY-MM-DD} | — |
   ```
6. Sync `projects/projects.json projects/{name}.md` (`phase: {project} → {new_phase}`).

If any step fails (file not found, JSON parse error), fail silently and log the error only to the session file. Do not surface the error to the user during a `/phase` run — flowie sync is a background concern.

---

## Privacy rules

- Never ask for a GitHub token in chat, print one to the terminal or write one to any file.
- The `flowie` repo must be private. Do not confirm or suggest making it public.
- Do not log task content, project details, or profile contents to `.neuroflow/sessions/` beyond the one-line summary.
- Never write machine-local absolute paths (`C:/Users/…`, `/home/…`) into any flowie file — they sync to every machine. Local folders live only in `~/.neuroflow/local-projects.json`.
- Wellbeing is self-reported only: never infer mood, stress or energy from messages, typing, timing or work patterns, and never record an inferred value anywhere.

---

## At end

Append to `.neuroflow/sessions/YYYY-MM-DD.md` (canonical format — neuroflow-core → Command lifecycle):

```
## HH:MM — [flowie] {mode}: {brief summary of what happened}
```

Examples:
- `## 14:22 — [flowie] --init: built initial profile for {name}`
- `## 14:45 — [flowie] --sync: pulled 3 changes from GitHub, pushed 1 file, cleared 2 auto-sync failures`
- `## 15:01 — [flowie] --link: linked current project to AlphaModulation`
- `## 15:10 — [flowie] --view: displayed profile`
- `## 15:18 — [flowie] --identify: generated identity paragraph, user confirmed`
- `## 15:30 — [flowie] --tasks: showed Kanban board (5 tasks across 3 columns)`
- `## 15:35 — [flowie] --tasks --add: created task spin-tests-5ht2a in inbox`
- `## 15:40 — [flowie] --tasks --move: moved fix-rt-glasses → active`
- `## 16:00 — [flowie] --projects: showed phase timeline for 2 projects`
- `## 16:10 — [flowie] --projects --add: registered project RT_DES`
- `## 16:30 — [flowie] --wiki: showed wiki overview (24 pages, 8 sources)`
- `## 16:45 — [flowie] --wiki-ingest: ingested "Gamma in WM" paper, updated 6 pages, tagged AlphaModulation`
- `## 17:00 — [flowie] --wiki-query: answered "what do I know about ICA?", filed as synthesis page`
- `## 17:20 — [flowie] --wiki-lint: found 3 orphan pages, 1 missing concept page, fixed 2`
- `## 17:30 — [flowie] --wiki-add: created method page for "FOOOF spectral parameterization"`
- `## 17:45 — [flowie] --wiki-schema: initialized wiki for EEG/cognition domain`
