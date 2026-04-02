---
title: Flowie Profile
---

# Flowie Profile

**Flowie is your personal research OS — a private GitHub repository that stores your identity, preferences, and project history so neuroflow can personalise every session around who you actually are.**

Without flowie, neuroflow treats you as a generic researcher. With it, every command response is shaped by your documented stances, writing style, methodological preferences, and active projects.

---

## What flowie stores

Flowie is a private GitHub repo with three layers:

### 1. Identity profile (`profile.md`)

Your intellectual fingerprint:
- Research stances and positions
- Writing style preferences
- Methodological commitments (e.g. "I always report effect sizes", "I prefer non-parametric tests for small samples")
- Domain knowledge areas
- Collaboration style

The [`flowie` agent](../concepts/agents.md) reads this profile silently at the start of every session and applies it without exposing the contents in external-facing outputs.

### 2. Kanban task board (`tasks/`)

A personal task board linked to your active projects:
- Configurable columns (default: Inbox → Next → Active → Waiting → Done → Archive)
- Tasks can be linked to projects in the project registry
- Managed via `/flowie --tasks` with `--add`, `--move`, `--done`, `--archive` subcommands

### 3. Project registry (`projects/`)

A list of all your neuroflow projects with phase timelines:
- Tracks which project is at which phase
- Phase changes in your project repos automatically sync to the registry
- Managed via `/flowie --projects`

---

## How to set up flowie

1. Create a **private** GitHub repository (e.g. `yourname/flowie`)
2. Run `/flowie --init` in any neuroflow project to link and clone it
3. Answer a few questions to seed your initial profile
4. On subsequent sessions, `/flowie --sync` keeps the profile up to date

---

## How neuroflow uses your profile

When flowie is linked, at the start of any command that benefits from personalisation, the `flowie` agent:

1. Reads your `profile.md` silently
2. Surfaces your active tasks for the current project
3. Applies your documented preferences to how advice is framed, what caveats are raised, and which options are recommended

**Privacy rule:** flowie profile data never appears verbatim in external outputs (manuscripts, grant documents, reports). It shapes the interaction — it does not leak into deliverables.

---

## Daily wellbeing tracking (optional)

Run `/flowie --assess` to opt in to a short daily check-in (anxiety, energy, happiness on a 1–10 scale). Stored in `flowie/wellbeing/YYYY-MM-DD.md`. Claude will nudge you to fill it in if you sync without having done so that day. Entirely optional and never shared.

---

## Commands

| Command | What it does |
|---|---|
| `/flowie --init` | First-time setup: links your GitHub repo, seeds the profile |
| `/flowie --sync` | Pull latest profile, push any local changes |
| `/flowie --identify` | Show your current profile summary |
| `/flowie --tasks` | View your Kanban board |
| `/flowie --tasks --add` | Add a new task (guided interview) |
| `/flowie --tasks --move` | Move a task to a different column |
| `/flowie --tasks --done` | Mark a task as done |
| `/flowie --projects` | List all projects in the registry |
| `/flowie --projects --add` | Register a new project |
| `/flowie --assess` | Daily wellbeing check-in |
