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
writes:
  - .neuroflow/sentinel.md
  - .neuroflow/project_config.md
---

# /sentinel

Check the working directory and route to the correct agent:

- If `.claude-plugin/plugin.json` exists → this is the neuroflow plugin repo. Invoke the **sentinel-dev agent**.
- If `.neuroflow/` exists → this is a project repo. Invoke the **sentinel agent**.
- If neither exists → stop and tell the user to run `/start` first.
