---
name: sentinel
description: Audit of .neuroflow/ — checks flow.md completeness, timestamps, broken references, preregistration drift, session consistency, and personal sensitive information (emails, passwords, private keys, names, institutions). Scoped to .neuroflow/ by default; asks before scanning the full workspace. Writes a report to .neuroflow/sentinel.md.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/sentinel.md
  - .neuroflow/reasoning/
  - .neuroflow/preregistration/
  - .neuroflow/ethics/
  - .neuroflow/sessions/
  - .claude/CLAUDE.md
writes:
  - .neuroflow/sentinel.md
  - .neuroflow/sentinel-dev.md
  - .neuroflow/project_config.md
  - .claude/CLAUDE.md
lifecycle: light
requires:
  - .neuroflow/project_config.md
produces:
  - .neuroflow/sentinel.md
---

# /sentinel

Check the working directory and route to the correct agent:

1. If `.claude-plugin/plugin.json` exists → plugin repo. Invoke the **sentinel-dev agent**. Stop here regardless of what else exists.
2. Otherwise, if `.neuroflow/` exists → project repo. Invoke the **sentinel agent**.
3. Otherwise → stop and tell the user to run `/neuroflow` first.

Both agents start with a script and spend their own reading only on the judgement checks: sentinel-dev runs `scripts/automation/validate_pr.py` (the checks CI runs on every PR), sentinel runs `nf_check.py` from the `neuroflow:neuroflow-core` skill's `scripts/` folder (Claude Code shows the skill's base directory when it loads — pass that path to the agent).

When the agent has written its report (or applied fixes) and `.neuroflow/sessions/` exists, append one line to `.neuroflow/sessions/YYYY-MM-DD.md`: `## HH:MM — [sentinel] audit: N issues, M fixed (report in .neuroflow/sentinel.md)` — `sentinel-dev.md` in the plugin repo.
