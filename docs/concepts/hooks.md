---
title: Hooks
---

# Hooks

**Hooks fire automatically on tool use events — no manual invocation needed.**

Hooks let neuroflow act in the background while you work. They respond to tool events (file edits) and perform lightweight automatic actions: formatting code, syncing your personal flowie repo.

---

## Available hooks

### Ruff formatter

**Trigger:** `PostToolUse` — whenever Claude uses the Edit or Write tool on a `.py` file

**What it does:** Auto-formats any Python file written or edited during a session using [Ruff](https://docs.astral.sh/ruff/), the fast Python linter and formatter. Requires `ruff` to be installed and on your PATH — if it isn't, the hook silently skips.

```
Claude writes scripts/analysis/erp_analysis.py
   → Hook fires automatically
   → ruff format scripts/analysis/erp_analysis.py
   → File is formatted before you see it
```

### Flowie git-sync

**Trigger:** `PostToolUse` — whenever Claude uses the Edit or Write tool on a file inside `~/.neuroflow/flowie/`

**What it does:** Auto-commits and pushes the change to your linked private flowie GitHub repo (`git add -A && git commit -m "sync: auto" && git push`), so your personal profile, tasks, and notes are always backed up. `integrations.json` is explicitly unstaged before every commit — credentials never enter the sync.

!!! note "Session logging is not a hook"
    Earlier versions had a session-logger hook; it was removed in 0.2.8. Session logs at `.neuroflow/sessions/YYYY-MM-DD.md` are now written directly by Claude as part of the command lifecycle defined in `neuroflow-core`.

---

## How hooks are configured

Hooks are defined in the plugin's `hooks/hooks.json` and are activated automatically when neuroflow is installed. You don't need to configure anything.

Technically: each hook is a small POSIX shell command that receives the tool event as JSON on stdin and reads the edited file path from `tool_input.file_path` (parsed with `jq`, falling back to `python`). All hooks fail silently by design — they never interrupt your session. Because a silent hook can also break silently, CI feeds both hooks a simulated tool event on every pull request and checks that ruff ran and that the flowie change was committed and pushed without `integrations.json`.

The same `hooks.json` can also name the optional neuroflow mod (a hooks module) next to these shell hooks; see [The neuroflow mod](mods.md). The shell hooks work with or without it.

---

## Pre-session orientation

In addition to event hooks, neuroflow uses `.claude/CLAUDE.md` injection for pre-session orientation. When `/neuroflow` runs, it writes a static neuroflow block to the project's `.claude/CLAUDE.md`:

```markdown
## neuroflow

This project uses neuroflow, a Claude Code plugin. Project memory is in `.neuroflow/`.

- Read `.neuroflow/project_config.md` (its frontmatter holds `active_phase` and the other project facts) and `.neuroflow/flow.md` at the start of every session.
- Record project decisions in `.neuroflow/reasoning/`, not in Claude's auto-memory.
- Keep this block static: no phase or other changing facts here.
```

Claude Code reads `.claude/CLAUDE.md` at the start of every session, so Claude always knows where project memory lives and reads your active phase from `project_config.md` — even before you type the first message. The block names no phase, so it never goes stale, and it lives only in the project: never in your global `~/.claude/CLAUDE.md`, which every session on the machine would load.
