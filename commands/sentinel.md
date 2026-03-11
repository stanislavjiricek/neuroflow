---
name: sentinel
description: Audit of .neuroflow/ — checks flow.md completeness, timestamps, broken references, preregistration drift, and session consistency. Scoped to .neuroflow/ by default; asks before scanning the full workspace. Writes a report to .neuroflow/sentinel.md.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/sentinel.md
  - .neuroflow/reasoning/
  - .neuroflow/preregistration/
  - .neuroflow/sessions/
  - .claude/CLAUDE.md
writes:
  - .neuroflow/sentinel.md
  - .neuroflow/sentinel-dev.md
  - .neuroflow/project_config.md
  - .claude/CLAUDE.md
---

# /sentinel

Check the working directory and route to the correct agent:

1. If `.claude-plugin/plugin.json` exists → plugin repo. Invoke the **sentinel-dev agent**. Stop here regardless of what else exists.
2. Otherwise, if `.neuroflow/` exists → project repo. Invoke the **sentinel agent**.
3. Otherwise → stop and tell the user to run `/start` first.
