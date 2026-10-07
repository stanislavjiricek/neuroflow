---
title: /pipeline
---

# `/neuroflow:pipeline`

**Define and run a multi-step research pipeline across any sequence of neuroflow phases.**

`/pipeline` lets you plan and execute a sequence of neuroflow commands in order, **one step per invocation** — either interactively (asks for your approval before each step) or in brutal mode (`--executor`, no questions). The plan is saved, so each new `/pipeline` picks up the next step.

---

## When to use it

- You want to run several phases in a planned order — one `/pipeline` per step, without remembering which command comes next
- You want a plan-first approach: see the full pipeline before executing any step
- You need to resume a pipeline that was interrupted mid-run
- You want automated end-to-end execution with error logging

---

## Modes

=== "Interactive (default)"

    Claude asks for confirmation before each step, runs it, and ends by telling you the next step — run `/neuroflow:pipeline` again to do it. You can skip individual steps, adjust the plan, or stop at any point. Claude also asks you **where you want to stop** upfront, so you can run the pipeline in stages.

    ```
    /neuroflow:pipeline
    ```

=== "Brutal mode"

    You confirm the plan once; after that, every `/neuroflow:pipeline --executor` runs the next pending step without asking. Errors are logged and the next invocation moves on — unless the next step depends on the failed one, or two steps in a row failed. The stop-point question is skipped — all pending steps run. To leave it running unattended, wrap it in Claude Code's `/loop`.

    ```
    /neuroflow:pipeline --executor
    /loop /neuroflow:pipeline --executor
    ```

---

## How it works

1. **Read project state** — Claude checks `flow.md` and `project_config.md` to understand which phases have been worked on
2. **Draft a pipeline plan** — a `pipeline-plan.md` is written to `.neuroflow/pipeline/` listing all steps with status (`[pending]`, `[done]`, `[skipped]`, `[deferred]`)
3. **Choose your stop point** — Claude asks how far you want to go this session (a specific phase, or all the way through). Steps beyond the stop point are saved as `[deferred]` and picked up next time.
4. **Confirm before running** — in interactive mode, Claude shows the plan and waits for your go-ahead
5. **Run one step** — the next pending step, following the same lifecycle as running the command directly; then Claude updates the plan, names the next step, and stops (a `/compact` between long steps keeps the context lean)
6. **Continue** — each new `/neuroflow:pipeline` reads `pipeline-plan.md` and runs the next step, including any previously deferred steps once you extend the stop point. When the last step is done, Claude suggests its natural follow-up (after `/paper`: `/paper --submit`)

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
| Writes | `.neuroflow/pipeline/pipeline-plan.md`, `.neuroflow/pipeline/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md`, `.neuroflow/reasoning/pipeline.jsonl`, phase subfolders (via the commands it invokes) |

---

## Related commands

- [`/phase`](phase.md) — check or switch the active phase before planning a pipeline
- [`/neuroflow`](neuroflow.md) — get a full project status overview
- [`/sentinel`](sentinel.md) — audit `.neuroflow/` for consistency after a full pipeline run
