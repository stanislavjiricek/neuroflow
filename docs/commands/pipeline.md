---
title: /pipeline
---

# `/neuroflow:pipeline`

**Define and run a multi-step research pipeline across any sequence of neuroflow phases.**

`/pipeline` lets you plan and execute a sequence of neuroflow commands in order — either interactively (pauses for your approval between steps) or in brutal mode (`--executor`, runs straight through without stops).

---

## When to use it

- You want to run several phases back-to-back without manually invoking each command
- You want a plan-first approach: see the full pipeline before executing any step
- You need to resume a pipeline that was interrupted mid-run
- You want automated end-to-end execution with error logging

---

## Modes

=== "Interactive (default)"

    Claude pauses between each step and asks for confirmation before proceeding. You can skip individual steps, adjust the plan, or stop at any point. Claude also asks you **where you want to stop** upfront, so you can run the pipeline in stages without having to interrupt it mid-run.

    ```
    /neuroflow:pipeline
    ```

=== "Brutal mode"

    Claude runs straight through all pending steps without stopping. Errors are logged and the pipeline continues. A full summary is shown at the end. The stop-point question is skipped — all pending steps run.

    ```
    /neuroflow:pipeline --executor
    ```

---

## How it works

1. **Read project state** — Claude checks `flow.md` and `project_config.md` to understand which phases have been worked on
2. **Draft a pipeline plan** — a `pipeline-plan.md` is written to `.neuroflow/pipeline/` listing all steps with status (`[pending]`, `[done]`, `[skipped]`, `[deferred]`)
3. **Choose your stop point** — Claude asks how far you want to go this session (a specific phase, or all the way through). Steps beyond the stop point are saved as `[deferred]` and picked up next time.
4. **Confirm before running** — in interactive mode, Claude shows the plan and waits for your go-ahead
5. **Execute steps in order** — each step follows the same lifecycle as running the command directly
6. **Resume gracefully** — if re-invoked on a project with an existing `pipeline-plan.md`, Claude reads it and continues from where execution stopped, including any previously deferred steps

---

## Stop-point selection

After confirming the plan, Claude presents your pending steps as numbered options:

```
How far would you like to run the pipeline?

  1. Stop after ideation
  2. Stop after experiment
  3. Stop after data-analyze
  4. All the way through → paper
```

Pick a number (or type a custom stop point). Steps beyond your chosen point are marked `[deferred]` in the plan — run `/neuroflow:pipeline` again to continue from where you left off.

If you choose **all the way through** from ideation to paper, expect a surprise. 🎉

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/pipeline/pipeline-plan.md` |
| Writes | `.neuroflow/pipeline/pipeline-plan.md`, `.neuroflow/pipeline/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md`, `.neuroflow/reasoning/pipeline.json`, phase subfolders (via the commands it invokes) |

---

## Related commands

- [`/phase`](phase.md) — check or switch the active phase before planning a pipeline
- [`/neuroflow`](neuroflow.md) — get a full project status overview
- [`/sentinel`](sentinel.md) — audit `.neuroflow/` for consistency after a full pipeline run
