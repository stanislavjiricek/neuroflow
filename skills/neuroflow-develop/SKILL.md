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
├── .github/
│   ├── agents/
│   │   └── neuroflow-developer.md   ← GitHub/Copilot-compatible dev agent
│   └── workflows/
│       ├── deploy-docs.yml          ← builds and deploys MkDocs site on push to main
│       ├── daily-maintenance.yml    ← posts daily maintainer report (Discussion #167)
│       ├── research-radar.yml       ← posts weekly research radar (Discussion #169)
│       └── sentinel-dev.yml         ← runs sentinel consistency checks (Discussion #168)
├── scripts/
│   └── automation/                  ← Python scripts used by GitHub Actions
│       ├── sentinel_check.py
│       ├── daily_maintenance.py
│       ├── research_radar.py
│       ├── post_discussion.py
│       └── requirements.txt
├── skills/                ← agent-invoked skills (SKILL.md per folder)
├── commands/              ← slash commands (one .md file per command)
├── agents/                ← Claude Code custom agent definitions (.md files)
├── hooks/
│   └── hooks.json         ← event hooks (PostToolUse, PreToolUse, etc.)
├── docs/
│   └── commands/          ← MkDocs source pages (one .md per command)
├── overrides/             ← MkDocs theme overrides (main.html)
├── AGENTS.md              ← agent entry points for non-Claude Code tools (Codex, OpenCode)
├── mkdocs.yml             ← docs site nav, theme, plugins, extra.version
├── requirements.txt       ← Python deps for the docs build (mkdocs-material)
├── .neuroflow/            ← plugin-level project memory (dev decisions, sentinel reports)
└── README.md              ← public docs: What's new, Commands/Skills/Agents/Hooks tables
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

Valid phase values: `ideation`, `preregistration`, `grant-proposal`, `finance`, `experiment`, `tool-build`, `tool-validate`, `data`, `data-preprocess`, `data-analyze`, `paper`, `review`, `notes`, `write-report`, `output`, `hive`, `brain-build`, `brain-optimize`, `brain-run`, `utility`

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

## Adding or modifying hooks

Hooks are defined in `hooks/hooks.json` as shell commands triggered by tool-use events.

**Every hook command MUST fail silently.** Hook failures that surface to the user create noise during sessions. Enforce this by always ending hook commands with one of:
- `; true` — guarantees exit code 0 regardless of what preceded it
- `|| true` — falls back gracefully on any error
- `2>/dev/null` — suppresses all stderr output (use alongside `; true`)

Use plain shell commands where possible (they are simpler and avoid Python import/quoting issues). Redirect both stdout and stderr of any tool invocation (`>/dev/null 2>&1`).

Example of a well-formed hook:
```bash
# CLAUDE_TOOL_RESULT_FILE_PATH may not always be set (or the file may be gone
# by the time the hook runs), so check for .py extension AND file existence.
f="${CLAUDE_TOOL_RESULT_FILE_PATH:-}"; case "$f" in *.py) [ -f "$f" ] && ruff format "$f" >/dev/null 2>&1;; esac; true
```

Run `sentinel-dev` after changing `hooks/hooks.json` — Check 8b will flag any hook command that lacks error suppression.

## Release workflow

1. Make your changes
   - If you added, renamed, or removed a **command, skill, or agent**: update `docs/javascripts/mind.js` — add (or remove) the node in `NODES`, the link in `LINKS`, the phase angle in `PHASE_ANGLES` (if a new phase), and the entry in `NODE_PHASE_MAP`. Run a quick `Select-String -Pattern "sk-|cmd-|ag-" docs/javascripts/mind.js` sanity check after editing.
   - **Blocking step — do not skip.** Omitting a `mind.js` entry for a new skill, command, or agent is a consistency error that sentinel-dev Check 11 will flag on the next run.
2. **Update `README.md`** — two places:
   - Replace the `## What's new in X.Y.Z` section with the new version number and up to 3 bullet points describing what changed. Each bullet should link to the relevant file. This is the first thing users see after the header — keep it tight.
   - Add the new command or skill to the Commands or Skills table if applicable, with a link to the file.
3. Add an entry to **`docs/changelog.md`** — same bullet points as the README section, formatted as `## X.Y.Z` heading followed by one-line summaries.
4. Update **`mkdocs.yml` `extra.version`** to match the new version.
5. If it's a new item, **add it to the Roadmap** as completed or remove it from the planned list.
6. Update the **self-assessment bar** in `docs/index.md` — change `sa-bar-version` to the new version, and re-run the probe honestly for this version of Claude (answers may change as the model evolves).
7. Review **`commands/neuroflow.md` one-liners** — add, remove, or rotate the random lines printed below the ASCII logo if any feel stale for this release.
8. Bump the patch version in **all four places** (always patch: `0.1.0` → `0.1.1` → `0.1.2`, regardless of how large the change is):
   - `.claude-plugin/plugin.json` → `version` field
   - `.claude-plugin/marketplace.json` → `plugins[].version` field
   - `.neuroflow/project_config.md` → `Plugin version:` line (the plugin's own project memory)
   - `mkdocs.yml` → `extra.version` field (also covered by step 4 above, but keep in sync)
9. Run sentinel-dev to verify internal consistency before committing.
10. Commit and push to GitHub:

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

**One-time hook setup** (required after every fresh clone):

```bash
uv run python scripts/automation/install_hooks.py
```

This sets `core.hooksPath = .githooks`, enabling the pre-push version check. The hook rejects pushes where tracked files changed but `plugin.json` version was not bumped. Override with `git push --no-verify` if needed.

## Installation (for new users)

```
/plugin marketplace add stanislavjiricek/neuroflow
/plugin install neuroflow@neuroflow
```
