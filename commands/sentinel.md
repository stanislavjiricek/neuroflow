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

Invoke the **sentinel agent** to run a full coherence audit of `.neuroflow/`. The agent performs all checks, writes the report, and asks the user what to fix.
