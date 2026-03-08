---
name: neuroflow-develop
description: Guide for developing and maintaining the neuroflow plugin. Use when adding skills, commands, agents, or hooks to neuroflow, bumping the version, or publishing updates to GitHub.
---

# neuroflow Development Guide

## Repo structure

```
neuroflow/
├── .claude-plugin/
│   ├── plugin.json        ← plugin manifest (bump version here on release)
│   └── marketplace.json   ← marketplace catalog (lists neuroflow as installable plugin)
├── skills/                ← agent-invoked skills (SKILL.md per folder)
├── commands/              ← slash commands (one .md file per command)
├── agents/                ← custom agent definitions (.md files)
├── hooks/
│   └── hooks.json         ← event hooks (PostToolUse, PreToolUse, etc.)
└── config/
    └── team.json          ← example lab profile
```

## Adding a new skill

1. Create a folder under `skills/` — the folder name becomes the skill name
2. Add a `SKILL.md` with frontmatter and instructions:

```markdown
---
name: my-skill
description: One-line description Claude uses to decide when to invoke this skill.
---

Instructions for Claude to follow when this skill is invoked...
```

Skills are namespaced as `neuroflow:my-skill` after installation.

## Adding a new command

Create a `.md` file in `commands/`. The filename becomes the command name:

```markdown
---
description: What this command does
---

Instructions Claude follows when the user runs /neuroflow:my-command...
```

## Adding a new agent

Create a `.md` file in `agents/`. Define the agent's role, focus, and any tool restrictions in the body.

## Release workflow

1. Make your changes
2. Bump the version in `.claude-plugin/plugin.json` (semantic versioning — `0.1.0` → `0.2.0`)
3. Commit and push to GitHub:

```bash
git add -A
git commit -m "feat: describe what changed"
git push
```

4. Users update their local install:

```
/plugin marketplace update neuroflow
```

> Claude Code detects updates by comparing version numbers. If the version is not bumped, the update will not be pulled even if files changed.

## Local development (test before pushing)

Load the local repo directly without installing:

```bash
claude --plugin-dir ./neuroflow
```

Skills and commands will be available as `/neuroflow:skill-name`. Restart Claude Code after each change to pick up edits.

## Installation (for new users)

```
/plugin marketplace add stanislavjiricek/neuroflow
/plugin install neuroflow@neuroflow
```
