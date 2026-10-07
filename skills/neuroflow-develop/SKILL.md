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
│   └── workflows/
│       ├── validate.yml             ← every PR and push to main: validate_pr.py, unit tests, strict docs build;
│       │                              mod job: claude plugin validate / test on 2.1.292, mod_policy.py
│       ├── mod-canary.yml           ← weekly: the same mod checks on the newest Claude Code; opens an issue on failure
│       ├── deploy-docs.yml          ← builds and deploys MkDocs site on push to main
│       ├── daily-maintenance.yml    ← posts daily maintainer report (Discussion #167)
│       ├── research-radar.yml       ← posts weekly research radar (Discussion #169)
│       └── sentinel-dev.yml         ← daily repo-check report + version auto-fix PR (Discussion #168)
├── .githooks/pre-push     ← local version-bump check (install_hooks.py)
├── scripts/
│   └── automation/                  ← maintainer and CI scripts (stdlib)
│       ├── repo_checks.py           ← the one implementation of every repo check (V1–V15)
│       ├── validate_pr.py           ← runs repo_checks — CI on every PR, and locally
│       ├── sentinel_check.py        ← daily report on the same checks
│       ├── bump_version.py          ← bumps or syncs the four version sites
│       ├── pre_push_version_check.py, install_hooks.py
│       ├── daily_maintenance.py, research_radar.py, post_discussion.py
│       └── requirements.txt
├── tests/                 ← unittest suites: automation/ (repo tooling), scripts/ (skill scripts)
├── skills/                ← agent-invoked skills (SKILL.md per folder; portable checks in scripts/)
├── commands/              ← slash commands (one .md file per command)
├── agents/                ← Claude Code custom agent definitions (.md files)
├── hooks/
│   ├── hooks.json         ← event hooks (PostToolUse, PreToolUse, etc.) and the optional `modules` entry
│   └── mod/               ← the optional hooks module (docs/concepts/mods.md)
├── docs/
│   └── commands/          ← MkDocs source pages (one .md per command)
├── overrides/             ← MkDocs theme overrides (main.html)
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

3. **Never reuse a command's name for a skill folder.** A command and a skill with the same name share `neuroflow:<name>`, and the command wins: "read the `neuroflow:<name>` skill" then loads the command. `validate_pr.py` V9 fails on it.
4. Add the skill to the Skills table in `README.md` and to the `mkdocs.yml` nav (V10).
5. A deterministic check the skill needs goes in `skills/<skill>/scripts/<name>.py`: Python 3.10+, stdlib first, `argparse` with `--json`, exit 0 = clean / 1 = findings / 2 = usage or runtime error. Add `tests/scripts/test_<name>.py` (stdlib `unittest`, temp dirs, no network). The prose says how to run it — `python <skill base dir>/scripts/<name>.py …` — and what to do with each exit code. One executable home per check: the prose, CI and the hooks module all run that file, never a copy.

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
lifecycle: full                   # full | light | quiet
requires:                         # optional — memory paths it expects (warn-only)
  - .neuroflow/{phase}/plan.md
produces:                         # optional — main outputs
  - .neuroflow/{phase}/summary.md
next:                             # optional — commands that usually follow (bare names)
  - paper
---

Instructions Claude follows when the user runs /neuroflow:my-command...
```

Valid phase values: see the **Phase taxonomy** section in `neuroflow:neuroflow-core` (`skills/neuroflow-core/SKILL.md`) — the one canonical list. Do not copy it here or into any command. What `lifecycle`, `requires`, `produces` and `next` mean is defined there too (Command frontmatter standard).

Every command must also follow the lifecycle defined in `neuroflow:neuroflow-core` — read `project_config.md` + `flow.md` at the start, write to `sessions/` and update `flow.md` at the end.

A new command is finished only when every propagation site exists:

- `docs/commands/<name>.md` (V4)
- a `mkdocs.yml` nav entry in its section of the docs index (Phases, Memory & team or Commands) and a row in the README Commands table (V10)
- for a phase command: the phase skill `skills/phase-<name>/SKILL.md` with its `## Slash command` section, and the phase in neuroflow-core's taxonomy

Run `python scripts/automation/validate_pr.py` — V3, V4 and V10 name any site still missing.

## Project memory — .neuroflow/

Project state lives in the **user's working directory**, not inside the plugin. The `/neuroflow` command creates `.neuroflow/` there by interviewing the user.

Skills, commands, and agents that need project context must explicitly `Read` `.neuroflow/project_config.md` from the working directory at runtime. It is never auto-injected.

**When building a new skill/command/agent that needs project context:**
1. Read `neuroflow:neuroflow-core` to understand the full `.neuroflow/` structure
2. Declare what you read and write in the frontmatter `reads` / `writes` fields
3. Handle the case where `.neuroflow/` doesn't exist — prompt the user to run `/neuroflow` first, or proceed with sensible defaults

There is no config folder in the plugin — project state is always per-project, in the user's repo.

## Adding a new agent

Create a `.md` file in `agents/`. Define the agent's role, focus, and any tool restrictions in the body. The frontmatter `name:` equals the filename (V5). Add a row to the README Agents table and a `mkdocs.yml` nav entry under Agents (V10).

## Adding or modifying hooks

Hooks are defined in `hooks/hooks.json` as shell commands triggered by tool-use events.

**Every hook command MUST fail silently.** Hook failures that surface to the user create noise during sessions. Enforce this by always ending hook commands with one of:
- `; true` — guarantees exit code 0 regardless of what preceded it
- `|| true` — falls back gracefully on any error

`2>/dev/null` alone is not enough: it hides stderr, not the exit code — use it alongside `; true`. `validate_pr.py` V6 fails on a command hook that does not end with `; true` or `|| true`.

Use plain shell commands where possible (they are simpler and avoid Python import/quoting issues). Redirect both stdout and stderr of any tool invocation (`>/dev/null 2>&1`).

Example of a well-formed hook:
```bash
# Hook input arrives as JSON on stdin — the edited file path is in
# tool_input.file_path. There is NO env var carrying the path (the old
# CLAUDE_TOOL_RESULT_FILE_PATH pattern silently never fired). Parse with jq,
# fall back to python if jq is missing, normalize Windows backslashes, and
# check extension AND existence (the file may be gone by the time the hook runs).
in=$(cat); f=$(printf '%s' "$in" | jq -r '.tool_input.file_path // empty' 2>/dev/null); [ -n "$f" ] || f=$(printf '%s' "$in" | python -c "import sys,json;print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null); f=$(printf '%s' "$f" | tr '\\' '/'); case "$f" in *.py) [ -f "$f" ] && ruff format "$f" >/dev/null 2>&1;; esac; true
```

**Never invent hook env vars.** The documented ones are `CLAUDE_PROJECT_DIR` (and `CLAUDE_PLUGIN_ROOT` in plugins); everything else must come from the stdin JSON. After changing a hook, verify it actually fires. Silent-fail wrappers make a broken hook indistinguishable from a working one, so `tests/automation/test_hooks_json.py` pipes a simulated PostToolUse event into every command hook and checks the outcome (ruff ran on the `.py` file; the flowie edit was committed and pushed without `integrations.json`). Extend it when you add or change a hook, and run it with `python -m unittest discover -s tests -p "test_hooks_json.py" -v`. `claude --debug` shows which hooks ran and why one was skipped.

**The hooks module.** `hooks.json` may also name one hooks module next to the shell hooks — `"modules": ["./mod/neuroflow.ts"]`, path relative to `hooks/`; Claude Code loads both and refuses a second module entry. V6 checks that the entry resolves. The module is optional: many sessions run without it (rollout flag off, hooks disabled, older builds, headless runs), so **no duty moves into code** — every rule and every bookkeeping step stays in the prose, and the module only adds speed, visibility and guards on top. If a duty ever has to move into the module, add a check that the prose path still meets it with the module off before shipping it.

## Rule markers

A rule that a guard in the hooks module may enforce is stated in a skill or command, with a marker on the line before it:

```markdown
<!-- nf-rule: PREREG-FROZEN -->
Frozen preregistration files are never edited; record changes in deviations.md.
```

The ids come from the rule table in neuroflow-core. A guard cites the id it enforces as the literal text `nf-rule: <ID>` — a comment above its registration, or inside its deny reason. `validate_pr.py` V8 fails on a marker with an unknown id and on a guard whose rule has no marker in `skills/` or `commands/`: a guard may only enforce what the prose states. The marker proves the prose exists, not that guard and prose agree — sentinel-dev J4 reads both.

## Release workflow

1. Make your changes
   - If you added, renamed, or removed a **command, skill, or agent**: place it in the docs index (`mkdocs.yml` nav, each page once) — `validate_pr.py` V10 fails the PR otherwise. A new phase also belongs on the landing page's ring (`overrides/home.html`) and in the Phases list of `docs/overview.md`.
2. **Update `README.md`** — two places:
   - Add a `## What's new in X.Y.Z` section above the previous one, with up to 3 bullet points describing what changed. Each bullet should link to the relevant file. This is the first thing users see after the header — keep it tight. Move the `<a id="whats-new"></a>` line so it stays right above the newest heading: the header's What's new link points at it.
   - Add the new command or skill to the Commands or Skills table if applicable, with a link to the file.
3. Add an entry to **`docs/changelog.md`** — same bullet points as the README section, formatted as `## X.Y.Z` heading followed by one-line summaries.
4. **`mkdocs.yml` `extra.version`** must match the new version — `bump_version.py` writes it in step 7.
5. If the release changes a format that existing projects keep (`project_config.md`, task files, reasoning logs, git files), make sure `/neuroflow:migrate` converts it — the first command after the update points every person there (`docs/upgrading.md`).
6. Review **`commands/neuroflow.md` one-liners** — add, remove, or rotate the random lines printed below the ASCII logo if any feel stale for this release.
7. Bump the patch version in **all four places** (always patch: `0.1.0` → `0.1.1` → `0.1.2`, regardless of how large the change is) with `python scripts/automation/bump_version.py` (`--dry-run` shows the change first; `--sync` repairs drift without bumping). It rewrites only the version strings:
   - `.claude-plugin/plugin.json` → `version` field
   - `.claude-plugin/marketplace.json` → `plugins[].version` field
   - `.neuroflow/project_config.md` → `plugin_version` (the plugin's own project memory; the `Plugin version:` line in the legacy dialect)
   - `mkdocs.yml` → `extra.version` field
8. Run `python scripts/automation/validate_pr.py --base origin/main` and `python -m unittest discover -s tests -p "test_*.py"` — CI runs both on the PR (`validate.yml`). Run sentinel-dev for the checks that need judgement.
9. Commit and push to GitHub:

```bash
git add -A
git commit -m "feat: describe what changed"
git push
```

10. Users update their local install. From a shell:

```bash
claude plugin marketplace update neuroflow
claude plugin update neuroflow@neuroflow
```

In a session, `/plugin` → **Installed** → neuroflow → **Update now** does the same (so does **Marketplaces** → neuroflow → **Update marketplace**, which refreshes the listing and updates its plugins). `/plugin marketplace update neuroflow` on its own only refreshes the listing; the installed plugin stays at its version. A running session keeps the version it loaded: run `/reload-plugins` or restart Claude Code, then `/neuroflow:migrate` in each project. Auto-update is off by default for third-party marketplaces like this one; each person can switch it on in `/plugin` → **Marketplaces** → neuroflow → **Enable auto-update**.

> Claude Code detects updates by comparing version numbers. If the version is not bumped, the update will not be pulled even if files changed.

## Local development (test before pushing)

Load the local repo directly without installing:

```bash
claude --plugin-dir ./neuroflow
```

Skills and commands will be available as `/neuroflow:skill-name`. Run `/reload-plugins` after an edit to pick it up without restarting; restart only if a change still does not show.

To work in your normal sessions instead, install from the working copy: remove the GitHub-sourced marketplace (`/plugin marketplace remove neuroflow`), then `/plugin marketplace add <path to your clone>` and `/plugin install neuroflow@neuroflow`. `marketplace.json` uses `source: "./"`, so the installed plugin is the working copy itself — one copy, and `/reload-plugins` picks up edits. Never load `--plugin-dir` and an installed copy together: every skill, command, agent and MCP server would load twice.

**Tests:** `python -m unittest discover -s tests -p "test_*.py" -v` — `tests/automation/` covers the repo checks, `bump_version.py`, the pre-push hook and a smoke test of the `hooks.json` commands; `tests/scripts/` covers the skill scripts.

**One-time hook setup** (required after every fresh clone):

```bash
uv run python scripts/automation/install_hooks.py
```

This sets `core.hooksPath = .githooks`, enabling the pre-push version check. Like CI (V7), the hook compares the pushed commits with their merge base on origin's default branch and uses the same exempt list (`repo_checks.py`), so a bumped branch passes on every later push. It rejects pushes where substantive files changed but the `plugin.json` version was not bumped. Override with `git push --no-verify` if needed.

**Optional: validate at the end of every turn.** To have Claude fix a red repo before it stops, add a Stop hook to your own `.claude/settings.local.json` (per machine, never committed — a mid-work red state such as a docs page not yet written re-prompts once per stop):

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "in=$(cat); printf '%s' \"$in\" | python -c \"import sys,json; sys.exit(0 if json.load(sys.stdin).get('stop_hook_active') else 1)\" && exit 0; python \"$CLAUDE_PROJECT_DIR/scripts/automation/validate_pr.py\" >&2; [ $? -eq 1 ] && exit 2; exit 0"
          }
        ]
      }
    ]
  }
}
```

Exit 2 hands the failures to Claude; `stop_hook_active` lets the next stop through, so it blocks at most once in a row.

## Reviewing a contributor PR

Check the branch out in a separate worktree so your own work stays untouched, then run what CI runs:

```bash
git fetch origin pull/<n>/head:pr-<n>
git worktree add ../neuroflow-pr-<n> pr-<n>
cd ../neuroflow-pr-<n>
python scripts/automation/validate_pr.py --base origin/main
python -m unittest discover -s tests -p "test_*.py"
```

Then read the diff for what the checks cannot see: overlap with existing skills (the audit above), prose that contradicts neuroflow-core, and any change under `hooks/mod/` (sentinel-dev J4). Remove the worktree when done (`git worktree remove ../neuroflow-pr-<n>`). Merge by hand on GitHub — never from a script.

## Installation (for new users)

```
/plugin marketplace add stanislavjiricek/neuroflow
/plugin install neuroflow@neuroflow
```
