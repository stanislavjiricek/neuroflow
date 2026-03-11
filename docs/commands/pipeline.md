---
title: /pipeline
---

# `/neuroflow:pipeline`

**Define and run a multi-step research pipeline across any sequence of neuroflow phases.**

`/pipeline` lets you plan and execute a sequence of neuroflow commands in order — either interactively (pauses for your approval between steps) or in brutal mode (`--nomistake`, runs straight through without stops).

---

## When to use it

- You want to run several phases back-to-back without manually invoking each command
- You want a plan-first approach: see the full pipeline before executing any step
- You need to resume a pipeline that was interrupted mid-run
- You want automated end-to-end execution with error logging

---

## Modes

=== "Interactive (default)"

    Claude pauses between each step and asks for confirmation before proceeding. You can skip individual steps, adjust the plan, or stop at any point.

    ```
    /neuroflow:pipeline
    ```

=== "Brutal mode"

    Claude runs straight through all pending steps without stopping. Errors are logged and the pipeline continues. A full summary is shown at the end.

    ```
    /neuroflow:pipeline --nomistake
    ```

---

## How it works

1. **Read project state** — Claude checks `flow.md` and `project_config.md` to understand which phases have been worked on
2. **Draft a pipeline plan** — a `pipeline-plan.md` is written to `.neuroflow/` listing all steps with status (`[pending]`, `[done]`, `[skipped]`)
3. **Confirm before running** — in interactive mode, Claude shows the plan and waits for your go-ahead
4. **Execute steps in order** — each step follows the same lifecycle as running the command directly
5. **Resume gracefully** — if re-invoked on a project with an existing `pipeline-plan.md`, Claude reads it and continues from where execution stopped

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/pipeline-plan.md` |
| Writes | `.neuroflow/pipeline-plan.md`, `.neuroflow/sessions/YYYY-MM-DD.md`, phase subfolders (via the commands it invokes) |

---

## Related commands

- [`/phase`](phase.md) — check or switch the active phase before planning a pipeline
- [`/neuroflow`](neuroflow.md) — get a full project status overview
- [`/sentinel`](sentinel.md) — audit `.neuroflow/` for consistency after a full pipeline run
