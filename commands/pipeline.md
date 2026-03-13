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

> "Run ideation, then data, then data-analyze, then paper"

becomes:

```
Step 1: /ideation
Step 2: /data
Step 3: /data-analyze
Step 4: /paper
```

Validate that each step is a known neuroflow command. If an unknown command appears, flag it and ask the user to clarify before proceeding.

### If no plan was supplied

Infer the full natural pipeline from the project state:

1. Identify which phases have existing work in `.neuroflow/` (listed in `flow.md`)
2. Map what remains using the standard research sequence:

```
ideation → grant-proposal? → experiment? → data → data-preprocess → data-analyze → paper
```

Mark completed phases with `[done]`. Propose the remaining phases as the pipeline steps.

Present the plan clearly:

```
Pipeline plan for: [project name]
Active phase: [current]

Steps:
  [done] ideation
  [done] experiment
  [ ] data              ← next step
  [ ] data-preprocess
  [ ] data-analyze
  [ ] paper
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

## Step 3b — Ask where to stop

After the plan is confirmed, **always** ask the user how far they want to go before executing anything. Present numbered options based on the pending steps in the plan, plus an "all the way through" option:

```
How far would you like to run the pipeline?

  1. Stop after ideation
  2. Stop after experiment
  3. Stop after data-analyze
  4. All the way through → paper  ← full journey
  (or type a custom stop point)
```

- If the user picks **a specific phase**: set that phase as the `stop_after` boundary. Execute only steps up to and including that phase. Phases after the boundary are shown as `[deferred]` in the plan and are not executed this run.
- If the user picks **all the way through** (or there are only 1–2 steps in the plan): proceed with the full plan unchanged.
- In **brutal mode** (`--nomistake`): skip this question and run all pending steps (the mode already implies full execution).

### Full-journey joke

If the user selects the full pipeline from `ideation` all the way to `paper` (i.e., the pipeline spans the complete research journey with no custom stop point), generate and display a **fresh, unique, original joke** before starting execution. The joke must be:

- **Newly composed each time** — never reuse a preset joke. Generate it spontaneously.
- **Themed around the absurdity of doing an entire research project in one go** — self-aware academic humour is ideal (neuroscience, statistics, publication, grant pressure, etc. are all fair game).
- **Short** — one or two lines maximum.
- Followed by: "Alright, brave soul. Let's do this. 🚀"

Example style (do NOT reuse this — always write a fresh one):
> "Why did the researcher run the full pipeline in one sitting? Because their grant ends tomorrow and denial is a legitimate cognitive strategy."
> Alright, brave soul. Let's do this. 🚀

---

## Step 4 — Save the pipeline plan

Before running anything, write the confirmed plan to `.neuroflow/pipeline/pipeline-plan.md`. Include the `Stop after` field if the user chose a specific stop point:

```markdown
# Pipeline plan
Generated: YYYY-MM-DD
Mode: interactive | brutal (--nomistake)
Stop after: /data-analyze | all the way through

## Steps

| # | Command | Status | Notes |
|---|---|---|---|
| 1 | /ideation | done | Completed 2026-03-01 |
| 2 | /data | pending | — |
| 3 | /data-preprocess | pending | — |
| 4 | /data-analyze | pending | — |
| 5 | /paper | deferred | Beyond stop point — run /pipeline again to continue |
```

Create `.neuroflow/pipeline/flow.md` referencing this file.

Update root `.neuroflow/flow.md` to add the `pipeline/` subfolder if it is new.

Log a decision to `.neuroflow/reasoning/pipeline.json`:
```json
{
  "statement": "Pipeline defined with N steps: [list]",
  "source": "command:pipeline | YYYY-MM-DD",
  "reasoning": "Steps inferred from project state / supplied by user. Mode: interactive|brutal. Stop after: [phase or 'all']."
}
```

---

## Step 5 — Execute the pipeline

Work through the pipeline steps in order, skipping any already marked `[done]` or `[deferred]` (steps beyond the chosen stop point).

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

When all steps up to the stop point are done (or the user stops):

Print a pipeline summary:

```
Pipeline complete.

Steps executed:
  ✅ ideation       — research-question.md saved
  ✅ data           — intake report saved, BIDS validated
  ✅ data-preprocess — preprocessing config saved, QC passed
  ✅ data-analyze   — analysis plan and results saved

Deferred (beyond stop point):
  ⏸ paper          — run /neuroflow:pipeline again to continue

Skipped:
  — review (not part of this pipeline)

Files written: [list of key outputs]
Next suggested step: /neuroflow:pipeline  (to continue from /paper) or /neuroflow:review
```

If all steps including deferred ones are done, omit the "Deferred" section and suggest `/neuroflow:review` as the next step.

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
   > "Resuming pipeline. 2 of 5 steps complete. Next step: /[next-pending-command]."
   > If there are `[deferred]` steps: "You previously stopped after /[stop-phase]. The following steps were deferred: /[deferred-phases]."
3. Ask: "Continue from where we left off? (Y / restart from scratch / extend stop point)"
4. If **Y**: skip `[done]` and `[skipped]` steps, promote any `[deferred]` steps to `[pending]` and re-run Step 3b to ask the new stop point, then continue from the first `pending` step
5. If **restart**: prompt the user to build a new plan from Step 3
6. If **extend stop point**: re-run Step 3b only, keeping completed steps intact

---

## Error handling

If a step fails or produces an unexpected result:

- **Interactive mode:** stop, report the error clearly, and ask the user how to proceed:
  > "⚠️ Step N (/[command]) encountered a problem: [description]. Options: retry / skip / stop"
- **Brutal mode:** log the error to `pipeline-plan.md` and the session file, mark the step as `[error]`, and continue to the next step. Print a full error summary at the end.

Never silently swallow errors. Always surface them — in brutal mode at the summary, in interactive mode immediately.
