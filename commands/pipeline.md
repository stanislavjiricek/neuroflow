---
name: pipeline
description: Define and run a multi-step research pipeline across any sequence of neuroflow phases. Interactive by default — pauses between steps for approval. Pass --nomistake to run in brutal mode with no stops.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
writes:
  - .neuroflow/pipeline/
  - .neuroflow/pipeline/flow.md
  - .neuroflow/pipeline/pipeline-plan.md
  - .neuroflow/sessions/YYYY-MM-DD.md
  - .neuroflow/reasoning/pipeline.json
---

# /pipeline

Read the `neuroflow:phase-pipeline` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` and `flow.md` before starting.

## What this command does

Defines a multi-step pipeline across any sequence of neuroflow commands — then runs them in order. Two modes:

- **Interactive mode** (default) — pauses after each step, shows what was done, and asks for approval before moving to the next. The user can adjust, skip, or stop at any point.
- **Brutal mode** (`--nomistake`) — runs the full pipeline from start to finish without pausing. Designed for experienced users who trust the plan and want maximum throughput.

The pipeline can be built from:
1. **What already exists** — reads `.neuroflow/` to infer which phases are done and what remains
2. **A user-supplied plan** — the user describes a sequence and the command formalizes it
3. **A combination** — infers the current state, then asks the user to confirm or extend the plan

---

## Step 1 — Detect mode

Check whether the user invoked with `--nomistake`:

- If `--nomistake` is present → **brutal mode**. No pauses between steps. Confirm once at the start before executing.
- Otherwise → **interactive mode**. Pause and confirm after each step.

---

## Step 2 — Read project state

Read `.neuroflow/project_config.md` and `.neuroflow/flow.md`.

Extract:
- Active phase
- Phases already worked on (subfolders listed in `flow.md`)
- Research question, modality, tools (from `project_config.md`)

If `.neuroflow/` does not exist: ask the user to run `/neuroflow:neuroflow` first to initialize the project, then stop.

---

## Step 3 — Build the pipeline plan

### If the user supplied a plan

Parse the user's description into an ordered list of neuroflow commands. For example:

> "Run ideation, then data, then data-analyze, then paper-write"

becomes:

```
Step 1: /ideation
Step 2: /data
Step 3: /data-analyze
Step 4: /paper-write
```

Validate that each step is a known neuroflow command. If an unknown command appears, flag it and ask the user to clarify before proceeding.

### If no plan was supplied

Infer the full natural pipeline from the project state:

1. Identify which phases have existing work in `.neuroflow/` (listed in `flow.md`)
2. Map what remains using the standard research sequence:

```
ideation → grant-proposal? → experiment? → data → data-preprocess → data-analyze → paper-write → paper-review
```

Mark completed phases with `[done]`. Propose the remaining phases as the pipeline steps.

Present the plan clearly:

```
Pipeline plan for: [project name]
Active phase: [current]

Steps:
  [done] ideation
  [done] experiment
  [ ] data              ← start here
  [ ] data-preprocess
  [ ] data-analyze
  [ ] paper-write
  [ ] paper-review
```

Ask the user:
> "Does this plan look right? You can add, remove, or reorder steps before I start."

Apply any changes the user requests.

### Optional step: include brain simulation or tool phases

If the project involves brain simulation (detected from `project_config.md`), ask:
> "Should I include brain-build / brain-optimize / brain-run in the pipeline?"

If the project mentions tool development, ask:
> "Should I include tool-build and tool-validate?"

---

## Step 4 — Save the pipeline plan

Before running anything, write the confirmed plan to `.neuroflow/pipeline/pipeline-plan.md`:

```markdown
# Pipeline plan
Generated: YYYY-MM-DD
Mode: interactive | brutal (--nomistake)

## Steps

| # | Command | Status | Notes |
|---|---|---|---|
| 1 | /ideation | done | Completed 2026-03-01 |
| 2 | /data | pending | — |
| 3 | /data-preprocess | pending | — |
| 4 | /data-analyze | pending | — |
| 5 | /paper-write | pending | — |
```

Create `.neuroflow/pipeline/flow.md` referencing this file.

Update root `.neuroflow/flow.md` to add the `pipeline/` subfolder if it is new.

Log a decision to `.neuroflow/reasoning/pipeline.json`:
```json
{
  "statement": "Pipeline defined with N steps: [list]",
  "source": "command:pipeline | YYYY-MM-DD",
  "reasoning": "Steps inferred from project state / supplied by user. Mode: interactive|brutal."
}
```

---

## Step 5 — Execute the pipeline

Work through the pipeline steps in order, skipping any already marked `[done]`.

### Interactive mode (default)

For each pending step:

1. Announce the step:
   > **Step N of M: /[command]**
   > I'm about to run `/neuroflow:[command]`. This will [brief description of what the command does].
   >
   > Ready to proceed? (Y / skip / stop)

2. If the user says **Y** or just hits enter: run the command inline. Follow every instruction in the corresponding command file exactly as if the user had invoked it directly.
3. If the user says **skip**: mark that step as `[skipped]` in `pipeline-plan.md`, log the skip in the session file, and move to the next step.
4. If the user says **stop** or **pause**: stop the pipeline. Print a summary of completed steps so far. Tell the user they can resume by running `/neuroflow:pipeline` again — the plan in `pipeline-plan.md` will be picked up and completed steps will be skipped.

After each step completes:
- Update the step status to `[done]` in `pipeline-plan.md` with the completion date
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Announce completion and confirm before moving to the next step:
  > ✅ `/[command]` complete. Moving to Step N+1: /[next-command]

### Brutal mode (`--nomistake`)

1. Print the full pipeline plan once, then confirm with the user:
   > "Running in brutal mode — no stops. I will execute all N steps in sequence. Last chance to cancel. Continue? (Y/n)"

2. If the user confirms: execute each step in sequence without pausing. Run each command inline exactly as written in the corresponding command file.

3. After each step: update `pipeline-plan.md`, append to sessions, then immediately move to the next without asking.

4. On completion: print a full summary of all steps executed, any outputs produced, and any notable decisions made.

---

## Step 6 — Pipeline completion

When all steps are done (or the user stops):

Print a pipeline summary:

```
Pipeline complete.

Steps executed:
  ✅ ideation       — research-question.md saved
  ✅ data           — intake report saved, BIDS validated
  ✅ data-preprocess — preprocessing config saved, QC passed
  ✅ data-analyze   — analysis plan and results saved
  ✅ paper-write    — manuscript draft saved

Skipped:
  — paper-review (skipped by user)

Files written: [list of key outputs]
Next suggested step: /neuroflow:paper-review
```

Update `pipeline-plan.md` with final statuses.

Append a final entry to `.neuroflow/sessions/YYYY-MM-DD.md` summarising the full pipeline run.

Log a final decision to `.neuroflow/reasoning/pipeline.json`:
```json
{
  "statement": "Pipeline run complete: N/M steps executed.",
  "source": "command:pipeline | YYYY-MM-DD",
  "reasoning": "All pending pipeline steps completed. Skipped steps: [list or none]."
}
```

---

## Resuming a paused pipeline

When the user runs `/neuroflow:pipeline` again on a project that already has a `pipeline-plan.md`:

1. Read the existing plan
2. Show status:
   > "Resuming pipeline. 2 of 5 steps complete. Next step: /data-analyze."
3. Ask: "Continue from where we left off? (Y / restart from scratch)"
4. If **Y**: skip `[done]` and `[skipped]` steps, continue from the first `pending` step
5. If **restart**: prompt the user to build a new plan from Step 3

---

## Error handling

If a step fails or produces an unexpected result:

- **Interactive mode:** stop, report the error clearly, and ask the user how to proceed:
  > "⚠️ Step N (/[command]) encountered a problem: [description]. Options: retry / skip / stop"
- **Brutal mode:** log the error to `pipeline-plan.md` and the session file, mark the step as `[error]`, and continue to the next step. Print a full error summary at the end.

Never silently swallow errors. Always surface them — in brutal mode at the summary, in interactive mode immediately.
