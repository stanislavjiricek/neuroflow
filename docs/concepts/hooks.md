---
title: Hooks
---

# Hooks

**Hooks fire automatically on tool use events — no manual invocation needed.**

Hooks let neuroflow act in the background while you work. They respond to tool events (file edits, literature-server calls) and perform lightweight automatic actions: formatting code, syncing your personal flowie repo, checking PsychoPy paradigms for timing problems, blocking Sci-Hub.

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

**What it does:** Commits only the file Claude just wrote (`git commit -- <file>`, never `git add -A`), pulls with rebase, then pushes to your private flowie repo. `integrations.json`, gitignored files, and repos in the middle of a rebase or merge are skipped. It never blocks: a failed pull, commit or push (offline, auth, or a conflict, whose rebase is aborted at once) leaves the commit local and appends one line to `~/.neuroflow/flowie-sync.log`; `/flowie` mentions the log and `/flowie --sync` resolves and clears it.

### Sci-Hub block

**Trigger:** `PreToolUse` — before Claude calls the bundled literature server (`biorxiv`): its Sci-Hub tools `search_scihub` and `check_scihub_mirrors`, or any of its tools with `platform: scihub`

**What it does:** Denies the call before it runs and tells Claude to take an open-access route instead (`download_paper` from arXiv, bioRxiv, medRxiv or Semantic Scholar; `download_public_paper` from the publisher) or your institutional library access. The literature search never uses Sci-Hub; the block makes sure a stray call cannot either.

### PsychoPy paradigm audit

**Trigger:** `PostToolUse` — whenever Claude uses the Edit or Write tool on a `.py` file inside a `paradigm/` folder or on a PsychoPy Builder `.psyexp` file

**What it does:** Runs the static timing audit of the experiment phase (`skills/phase-experiment/scripts/psychopy_audit.py --hook`) on the file just written, without running the paradigm. Timing warnings — for example a trigger sent outside `win.callOnFlip()`, or `core.wait()` timing a stimulus — go back to Claude (up to eight), so it can fix them in the same turn; a clean file, or a `.py` file that does not use PsychoPy, produces nothing. It fails silently: if `python` is missing or the file cannot be read, the hook skips.

!!! note "Session logging is not a hook"
    Earlier versions had a session-logger hook; it was removed in 0.2.8. Session logs at `.neuroflow/sessions/YYYY-MM-DD.md` are now written directly by Claude as part of the command lifecycle defined in `neuroflow-core`.

---

## How hooks are configured

Hooks are defined in the plugin's `hooks/hooks.json` and are activated automatically when neuroflow is installed. You don't need to configure anything.

Technically: each hook is a small POSIX shell command that receives the tool event as JSON on stdin; the file-edit hooks read the edited file path from `tool_input.file_path` (parsed with `jq` or `python`). All hooks fail silently by design — a hook that breaks never interrupts your session. Because a silent hook can also break silently, CI feeds the ruff and flowie hooks a simulated tool event on every pull request and checks that ruff ran and that the flowie change was committed and pushed without `integrations.json`.

The same `hooks.json` also loads the optional neuroflow mod, a hooks module (`hooks/mod/neuroflow.ts`) named in its `modules` list, next to these shell hooks; see [The neuroflow mod](mods.md). The shell hooks work with or without it.

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
