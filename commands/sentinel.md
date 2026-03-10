---
name: sentinel
description: Full audit of .neuroflow/ — checks flow.md timestamps, detects drift, compares preregistration vs actual progress, and writes a report to sentinel.md.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/sentinel.md
  - .neuroflow/preregistration/
  - .neuroflow/sessions/
  - .claude/CLAUDE.md
writes:
  - .neuroflow/sentinel.md
  - .neuroflow/project_config.md
  - .claude/CLAUDE.md
---

# /sentinel

Check the working directory and route to the correct agent:

1. If `.claude-plugin/plugin.json` exists → plugin repo. Invoke the **sentinel-dev agent**. Stop here regardless of what else exists.
2. Otherwise, if `.neuroflow/` exists → project repo. Invoke the **sentinel agent**.
3. Otherwise → stop and tell the user to run `/start` first.
