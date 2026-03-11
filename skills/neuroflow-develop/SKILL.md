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
└── hooks/
    └── hooks.json         ← event hooks (PostToolUse, PreToolUse, etc.)
```

## Before adding anything — overlap audit

Every proposed addition (skill, command, agent, hook) must be checked against what already exists. Do this before writing a single line:

1. **Read all existing SKILL.md files** in `skills/*/SKILL.md` — extract the name, description, and key responsibilities of each.
2. **Read all existing command files** in `commands/*.md`.
3. **Read all existing agent files** in `agents/*.md`.
4. **Read `hooks/hooks.json`** for active hooks.

Then answer these questions explicitly:

| Question                                                           | If YES →                                                             |
| ------------------------------------------------------------------ | --------------------------------------------------------------------- |
| Does an existing skill cover more than 50% of the proposed scope?  | Extend that skill instead                                             |
| Does the proposed skill duplicate a command's instructions?        | Merge into the command or drop the skill                              |
| Does the proposed agent repeat logic already in a skill?           | The skill is enough — agents add autonomous execution, not knowledge |
| Does the proposed hook fire on the same event as an existing hook? | Combine into one hook command                                         |
| Is the proposed addition genuinely new territory?                  | Proceed with adding it                                                |

**Write your conclusion before proceeding.** Example:

> "The proposed `eeg-analysis` skill overlaps with the `eeg-preprocessing` skill (filtering, ICA) and the `feature-extraction` skill (band power). The unique contribution is connectivity analysis. Recommendation: extend `eeg-preprocessing` with a connectivity section rather than adding a new skill."

Only if the contribution is clearly new and non-overlapping should you create a new file.

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

Create a `.md` file in `commands/`. The filename becomes the command name. Every command must include the standard frontmatter defined in `neuroflow:neuroflow-core`:

```markdown
---
name: my-command
description: What this command does
phase: <phase-name>        # matches command name, or "utility" for stateless commands
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/{phase}/flow.md    # only if command has a phase subfolder
writes:
  - .neuroflow/sessions/YYYY-MM-DD.md
  - .neuroflow/{phase}/           # only if command has a phase subfolder
  - .neuroflow/{phase}/flow.md    # only if command has a phase subfolder
---

Instructions Claude follows when the user runs /neuroflow:my-command...
```

Valid phase values: `ideation`, `grant-proposal`, `experiment`, `tool-build`, `tool-validate`, `data`, `data-preprocess`, `data-analyze`, `paper-write`, `paper-review`, `notes`, `write-report`, `brain-build`, `brain-optimize`, `brain-run`, `export`, `utility`

Every command must also follow the lifecycle defined in `neuroflow:neuroflow-core` — read `project_config.md` + `flow.md` at the start, write to `sessions/` and update `flow.md` at the end.

## Project memory — .neuroflow/

Project state lives in the **user's working directory**, not inside the plugin. The `/neuroflow` command creates `.neuroflow/` there by interviewing the user.

Skills, commands, and agents that need project context must explicitly `Read` `.neuroflow/project_config.md` from the working directory at runtime. It is never auto-injected.

**When building a new skill/command/agent that needs project context:**
1. Read `neuroflow:neuroflow-core` to understand the full `.neuroflow/` structure
2. Declare what you read and write in the frontmatter `reads` / `writes` fields
3. Handle the case where `.neuroflow/` doesn't exist — prompt the user to run `/neuroflow` first, or proceed with sensible defaults

There is no config folder in the plugin — project state is always per-project, in the user's repo.

## Adding a new agent

Create a `.md` file in `agents/`. Define the agent's role, focus, and any tool restrictions in the body.

## Release workflow

1. Make your changes
2. **Update `README.md`** — two places:
   - Replace the `## What's new in X.Y.Z` section with the new version number and up to 3 bullet points describing what changed. Each bullet should link to the relevant file. This is the first thing users see after the header — keep it tight.
   - Add the new command or skill to the Commands or Skills table if applicable, with a link to the file.
3. If it's a new item, **add it to the Roadmap** as completed or remove it from the planned list.
4. Bump the patch version in `.claude-plugin/plugin.json` (always patch: `0.1.0` → `0.1.1` → `0.1.2`, regardless of how large the change is)
4. Commit and push to GitHub:

```bash
git add -A
git commit -m "feat: describe what changed"
git push
```

5. Users update their local install:

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
