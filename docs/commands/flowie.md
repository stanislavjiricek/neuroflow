---
title: /flowie
---

# `/neuroflow:flowie`

**Personal identity layer — link a private GitHub repository to store your research profile and personalize Claude's assistance.**

`/flowie` connects neuroflow to a private GitHub repository that holds your research identity: your stances, writing style, methodological preferences, and key beliefs about your field. Claude reads this profile to tailor its assistance to how you actually think, not a generic researcher.

Flowie is entirely optional. Nothing in neuroflow breaks if you do not use it.

---

## What Flowie stores

| File | Contents |
|---|---|
| `profile.md` | Your research identity — name, domain, preferred methods, writing style, stances, key beliefs |
| `ideas.md` | Ongoing hypotheses and ideas that span multiple projects |
| `sync.json` | GitHub repo URL, last sync timestamp, list of linked projects |

All data lives in `.neuroflow/.flowie/` locally, mirrored to a **private** GitHub repository that only you control. It is never included in exports or external-facing documents.

---

## Prerequisites

- A GitHub account
- One of the following for authentication:
  - **GitHub CLI (`gh`)** — recommended; run `gh auth login` before using `/flowie`
  - **Personal Access Token (PAT)** — create one at [github.com/settings/tokens](https://github.com/settings/tokens) with the `repo` scope

---

## Getting started

Run `/flowie` in any neuroflow project. On first run, you will be guided through:

1. GitHub authentication (CLI or PAT)
2. Checking for an existing `flowie` repository on your account — or creating one
3. Initialising the local `.neuroflow/.flowie/` directory

Then run `/flowie --init` to build your profile through a short interview.

---

## Modes

| Mode | What it does |
|---|---|
| `--init` | Build your profile from scratch via an interview — name, domain, methods, writing style, stances, 3–5 key beliefs |
| `--sync` | Pull the latest profile from GitHub, then push any local changes; shows diffs before applying |
| `--link` | Link the current neuroflow project to your flowie profile; adds a `flowie_profile` field to `project_config.md` |
| `--view` | Display your current profile summary |
| `--identify` | Claude reads all available profile data and generates a short "who you are" paragraph; you confirm or correct it |

If no mode flag is provided, `/flowie` shows the mode menu.

---

## How Claude uses the profile

Once a project is linked (via `--link`), Claude reads the profile at the start of each session and applies it:

- In **`/ideation`**: suggestions are framed around your research domain and existing ideas from `ideas.md`
- In **`/paper`**: drafts match your documented writing style and register
- In **`/data-analyze`**: statistical approaches are presented in your preferred framework (e.g. Bayesian-first if that is your stance)
- In **all phases**: if a documented stance or belief is relevant to a decision, Claude surfaces it once and asks whether it applies

The profile informs suggestions — it does not override your explicit instructions.

---

## Privacy

- The `flowie` GitHub repository is always private
- Profile data never appears in outputs intended for external readers (papers, grant proposals, reports)
- `.neuroflow/.flowie/` is excluded from `/export` by default
- The PAT (if used) is held in memory only — never written to disk

---

## Sync behaviour

The `--sync` mode always pulls before pushing:

1. Fetches remote changes and shows a diff
2. You confirm before remote changes are applied
3. Merge conflicts are shown side by side — never silently resolved
4. Local changes are pushed after the pull step
5. `last_synced` in `sync.json` is updated only if the push succeeds

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/.flowie/profile.md`, `.neuroflow/.flowie/ideas.md`, `.neuroflow/.flowie/sync.json` |
| Writes | `.neuroflow/.flowie/profile.md`, `.neuroflow/.flowie/ideas.md`, `.neuroflow/.flowie/sync.json`, `.neuroflow/project_config.md`, `.neuroflow/sessions/YYYY-MM-DD.md` |

---

## Related commands and agents

- [`/neuroflow`](neuroflow.md) — project setup and status; run before `/flowie`
- [`flowie` agent](../concepts/agents.md) — apply the profile autonomously during a session
- [`/output`](output.md) — flowie data is excluded from project exports by default
