---
name: flowie
description: Personal identity layer — link a private GitHub repository to store your research profile (stances, writing style, methodological preferences, key beliefs). Supports profile creation, sync with GitHub, and cross-project linking.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/.flowie/profile.md
  - .neuroflow/.flowie/ideas.md
  - .neuroflow/.flowie/sync.json
writes:
  - .neuroflow/.flowie/profile.md
  - .neuroflow/.flowie/ideas.md
  - .neuroflow/.flowie/sync.json
  - .neuroflow/project_config.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /flowie

Personal identity layer for neuroflow. Links the current project to a private GitHub repository — the user's "flowie" profile — which stores their research identity: stances, writing style, methodological preferences, and intellectual fingerprint. Claude uses this profile to personalize assistance across all neuroflow phases.

Read the `neuroflow:phase-flowie` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` and `flow.md` before starting.

Flowie is fully optional. Nothing breaks if it is not set up.

---

## Step 0 — Check for .neuroflow/

If `.neuroflow/` does not exist, stop and tell the user to run `/neuroflow` first.

---

## Step 1 — Read project state

Read `.neuroflow/project_config.md` and `.neuroflow/flow.md`.

Check whether `.neuroflow/.flowie/` exists:

- **If it does not exist** — this is first run. Go to Step 2.
- **If it exists** — read `sync.json` to confirm the linked GitHub repo and last sync time. Go to Step 3 (mode menu).

---

## Step 2 — First run: ask whether to set up flowie

Print:

```
flowie — personal identity layer

Your flowie profile is a private GitHub repository that stores your research identity:
  • research stances and key beliefs about your field
  • methodological preferences and tools
  • writing style and voice
  • ongoing ideas and hypotheses across projects

Claude reads this profile to personalize its assistance — tailoring suggestions
to how you actually think, not a generic researcher.

Set up or connect a flowie profile now? [Y/n]
```

If the user declines, stop. Do not create `.neuroflow/.flowie/` or write anything.

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

---

## Step 2b — Check for existing flowie repo

Using `gh` CLI or the GitHub API (with the PAT), check whether a private repository named `flowie` exists on the user's account.

If it exists:
```
Found an existing flowie repository on your GitHub account.
Connect to it? [Y/n]
```

If confirmed, set the repo URL and continue to Step 2c.

If it does not exist:
```
No flowie repository found on your GitHub account.
Create a new private repository named "flowie"? [Y/n]
```

If confirmed, create the repository:
- Using `gh repo create flowie --private` (if `gh` CLI is available)
- Or via the GitHub API: `POST /user/repos` with `{ "name": "flowie", "private": true }`

Confirm creation succeeded, then continue to Step 2c.

---

## Step 2c — Initialise local flowie directory

Create `.neuroflow/.flowie/` and write initial files:

**`sync.json`:**
```json
{
  "github_repo": "https://github.com/{username}/flowie",
  "last_synced": null,
  "linked_projects": []
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

Update `.neuroflow/flow.md` to add a row for `.flowie/`.

Tell the user:
```
flowie profile directory created at .neuroflow/.flowie/

Your GitHub repo is linked. Run /flowie --init to build your profile,
or /flowie --sync to pull an existing profile from GitHub.
```

Go to Step 3.

---

## Step 3 — Mode menu

If the user invoked the command with a mode flag, go directly to that mode. Otherwise, show the menu:

```
flowie — what would you like to do?

  --init      Build your profile from scratch (interview-based)
  --sync      Pull from GitHub, then push local changes
  --link      Link this project to your flowie profile
  --view      Show your current profile summary
  --identify  Generate a "who you are" paragraph from existing data
```

Wait for the user to choose.

---

## Mode: --init

**Trigger:** user runs `/flowie --init` or selects "Build your profile from scratch" from the menu, and there is no substantial content in `profile.md`.

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

After writing, offer to sync to GitHub immediately:
```
Profile saved. Push to your flowie GitHub repo now? [Y/n]
```

If yes, run the sync push (see `--sync` logic below, push only step).

---

## Mode: --sync

**Trigger:** user runs `/flowie --sync` or selects "Pull from GitHub, then push local changes".

Read `sync.json` for the repo URL. If it is missing, tell the user to run `/flowie` first to connect a repo.

### Pull step

Clone or fetch from the linked repo into a staging directory inside the project:

```bash
git clone --depth=1 {repo_url} .neuroflow/.flowie/.remote-sync
```

Or if `.neuroflow/.flowie/.remote-sync` already exists, run `git -C .neuroflow/.flowie/.remote-sync pull`. Clean up `.remote-sync` after the sync is complete (regardless of success or failure).

Compare remote files with local `.neuroflow/.flowie/` files:

- If remote and local are identical, report "No changes to pull."
- If remote has updates, show the diff:

```
Changes from GitHub:

profile.md:
  + [new line or section]
  - [removed or changed line]

Apply these changes? [Y/n / merge manually]
```

If the user confirms, apply the remote changes to the local files.

If the user selects "merge manually", open each conflicting file in sequence and show both versions side by side. Wait for the user to resolve each conflict before proceeding.

### Push step

After the pull is complete (or if no pull changes), check for local changes by comparing local `.neuroflow/.flowie/` files against the remote staging clone at `.neuroflow/.flowie/.remote-sync`.

If local has changes not yet on remote, commit and push:

```bash
git -C .neuroflow/.flowie/.remote-sync add .
git -C .neuroflow/.flowie/.remote-sync commit -m "sync: {YYYY-MM-DD HH:MM}"
git -C .neuroflow/.flowie/.remote-sync push
```

Update `last_synced` in `sync.json` to current ISO 8601 timestamp.

Report:
```
Sync complete — {YYYY-MM-DD HH:MM}
  Pulled: {N changes} from GitHub
  Pushed: {N files} to GitHub
  Last synced: {timestamp}
```

If push fails (e.g. auth error, network), report the error clearly and do not update `last_synced`.

---

## Mode: --link

**Trigger:** user runs `/flowie --link` or selects "Link this project to your flowie profile".

Read `sync.json`. Add the current project path to `linked_projects` (if not already present):

```json
"linked_projects": [
  "/path/to/current/project"
]
```

Read `.neuroflow/project_config.md`. Add or update a `flowie_profile` field:

```
flowie_profile: .neuroflow/.flowie/profile.md
```

Confirm to the user:
```
This project is now linked to your flowie profile.
Claude will read your profile when assisting in any neuroflow phase.
```

Write to `sessions/YYYY-MM-DD.md`.

---

## Mode: --view

**Trigger:** user runs `/flowie --view` or selects "Show your current profile summary".

Read `.neuroflow/.flowie/profile.md`. Display it formatted:

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

Read all files in `.neuroflow/.flowie/`. Also read `.neuroflow/project_config.md` and any reasoning logs in `.neuroflow/reasoning/` to gather additional signal about how the user thinks.

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

If yes, append a `## Claude's read` section to `profile.md` with the confirmed paragraph.

---

## At end

Append to `.neuroflow/sessions/YYYY-MM-DD.md`:

```
[HH:MM] /flowie — {mode}: {brief summary of what happened}
```

Examples:
- `[14:22] /flowie — --init: built initial profile for {name}`
- `[14:45] /flowie — --sync: pulled 2 changes from GitHub, pushed 1 file`
- `[15:01] /flowie — --link: linked current project to flowie profile`
- `[15:10] /flowie — --view: displayed profile`
- `[15:18] /flowie — --identify: generated identity paragraph, user confirmed`
