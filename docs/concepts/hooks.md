---
title: Hooks
---

# Hooks

**Hooks fire automatically on tool use events — no manual invocation needed.**

Hooks let neuroflow act in the background while you work. They respond to tool events (file edits, Bash commands) and perform lightweight automatic actions: formatting code, logging session activity.

---

## Available hooks

### Ruff formatter

**Trigger:** `PostToolUse` — whenever Claude uses the Edit or Write tool on a `.py` file

**What it does:** Auto-formats any Python file written or edited during a session using [Ruff](https://docs.astral.sh/ruff/), the fast Python linter and formatter.

This means any analysis or preprocessing script Claude generates is always PEP 8 compliant — no manual formatting step needed.

```
Claude writes scripts/analysis/erp_analysis.py
   → Hook fires automatically
   → ruff format scripts/analysis/erp_analysis.py
   → File is formatted before you see it
```

### Session logger

**Trigger:** `PostToolUse` — whenever Claude uses Write, Edit, or Bash tools

**Condition:** Only fires if `.neuroflow/` exists in the working directory

**What it does:** Appends a timestamped entry to today's session log at `.neuroflow/sessions/YYYY-MM-DD.md`.

Example session log entry:

```markdown
# Session: 2026-03-09

- [10:32] Edit: scripts/preprocessing/preprocess.py — added ICA component rejection
- [10:45] Bash: python scripts/preprocessing/preprocess.py — ran preprocessing on sub-01
- [11:03] Write: .neuroflow/data-preprocess/preprocess-report.md — saved QC report
```

This gives you a chronological record of everything Claude did in a session — useful for debugging, reproducibility, and supervision reports.

---

## How hooks are configured

Hooks are defined in the plugin's `plugin.json` and are activated automatically when neuroflow is installed. You don't need to configure anything.

---

## Pre-session orientation

In addition to event hooks, neuroflow uses `.claude/CLAUDE.md` injection for pre-session orientation. When `/start` runs, it writes a neuroflow block to `.claude/CLAUDE.md`:

```markdown
## neuroflow

This project uses the neuroflow workflow. Project memory is in `.neuroflow/`.

- Active phase: data-preprocess
- Config: `.neuroflow/project_config.md`
- Start any session by reading `project_config.md` and `flow.md` first.
```

Claude Code reads `.claude/CLAUDE.md` at the start of every session, so Claude always knows your active phase and where to find project context — even before you type the first message.
