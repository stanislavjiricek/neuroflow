# neuroflow — Agent Instructions

This file describes the structure and conventions of the neuroflow plugin for AI agents (Codex, OpenCode, and other AGENTS.md-compatible systems).

neuroflow is a Claude Code plugin for agentic neuroscience research. It provides slash commands, specialist skill files, and custom agent definitions that guide Claude through the full research lifecycle — from hypothesis to publication.

---

## Repository layout

```
neuroflow/
├── skills/                    ← agent-invoked skill instructions (SKILL.md per folder)
│   ├── neuroflow-core/        ← core lifecycle, project memory, personality modes, issue monitoring
│   ├── neuroflow-develop/     ← plugin development guide
│   ├── phase-{name}/          ← one skill per research phase
│   ├── notebooklm/            ← Google NotebookLM integration
│   ├── phase-hive/            ← team-level research coordination
│   └── review-neuro/          ← 8-agent pre-submission manuscript review
├── commands/                  ← slash command definitions (one .md per command)
│   ├── neuroflow.md           ← /neuroflow — project setup and status
│   ├── phase.md               ← /phase — phase map and switching
│   ├── fails.md               ← /fails — structured problem reporting
│   ├── hive.md                ← /hive — team Hive management
│   └── {name}.md              ← one command per research phase
├── agents/                    ← specialist sub-agent definitions
│   ├── scholar.md             ← literature search + download agent
│   ├── flowie.md              ← personal research workflow coordinator
│   └── {name}.md              ← other specialist agents
├── hooks/
│   └── hooks.json             ← PostToolUse / PreToolUse event hooks
└── .claude-plugin/
    ├── plugin.json            ← plugin manifest (name, version, entry point)
    └── marketplace.json       ← marketplace catalog entry
```

---

## Key conventions

### Project memory

neuroflow stores per-project state in `.neuroflow/` inside the **user's working directory** (not the plugin repo). This folder is created by the `/neuroflow` command.

```
.neuroflow/
├── project_config.md          ← project identity, active phase, personality mode
├── flow.md                    ← root index of all subfolders
├── sessions/                  ← daily session logs
├── reasoning/                 ← structured decision logs (JSON)
└── {phase}/                   ← per-phase working files
```

Every skill and command reads `project_config.md` and `flow.md` at the start of each invocation. Nothing is auto-injected — files must be explicitly read.

### Command lifecycle (from `neuroflow-core`)

Every command follows this lifecycle:
1. Check `.neuroflow/` exists (if not: prompt user to run `/neuroflow`)
2. Read `project_config.md` and `flow.md`
3. Do the command's work
4. Write outputs to the appropriate `{phase}/` subfolder
5. Update `{phase}/flow.md`
6. Append a one-liner to `sessions/YYYY-MM-DD.md`

### Personality modes

The plugin supports three personality modes stored as `default_mode` in `project_config.md`:

| Mode key | Name | Behaviour |
|---|---|---|
| `snowflake` | 🧐 Teacher | Explains each step, checks assumptions, waits for approval |
| `nomistake` | ⚡ Executor | Acts immediately, self-critiques output |
| `critic` | 🔍 Critic | Interrogates assumptions, surfaces hard questions first |

Set at `/neuroflow` setup. Shown at `/phase`. Overridden per-message via aliases.

### Passive issue monitoring

The plugin monitors every user message for frustration or problem signals (defined in `neuroflow-core`). When a signal fires:
- If `auto_issue_reporting: yes` in `project_config.md`: files a GitHub issue automatically
- Always: appends a one-liner to `.neuroflow/fails/{category}.md`

### Skill naming

Skills are namespaced as `neuroflow:{folder-name}` after installation. A skill is invoked by including its name in a prompt or by a command's `reads:` frontmatter declaration.

---

## Agent entry points for other systems

When using neuroflow outside Claude Code (e.g. Codex, OpenCode, Cursor):

1. Read `skills/neuroflow-core/SKILL.md` first — it defines the full lifecycle and project memory format
2. Read the relevant phase skill (e.g. `skills/review-neuro/SKILL.md` for manuscript review)
3. Read `commands/{command}.md` for the specific command workflow you want to trigger
4. Create `.neuroflow/` manually or prompt the agent to follow the `/neuroflow` command steps

For full compatibility, ensure you provide the agent with the path to `skills/neuroflow-core/SKILL.md` as a background instruction file.

---

## Plugin version

See `.claude-plugin/plugin.json` → `version` field for the current plugin version.
