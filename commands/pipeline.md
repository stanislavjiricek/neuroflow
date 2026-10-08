---
name: pipeline
description: Define and run a multi-step research pipeline across any sequence of neuroflow phases — one step per invocation, picked up from the saved plan. Interactive by default (asks before each step); pass --executor for brutal mode (no questions).
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/pipeline/pipeline-plan.md
writes:
  - .neuroflow/pipeline/
  - .neuroflow/pipeline/flow.md
  - .neuroflow/pipeline/pipeline-plan.md
  - .neuroflow/sessions/YYYY-MM-DD.md
  - .neuroflow/reasoning/pipeline.jsonl
lifecycle: full
produces:
  - .neuroflow/pipeline/pipeline-plan.md
next:
  - pipeline
  - sentinel
---

# /pipeline

Read the `neuroflow:phase-pipeline` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` (and open with the version notice when the project's `plugin_version` is missing or older than the running neuroflow's version in `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` — **Command lifecycle**, step 3) and `flow.md` before starting.

## What this command does

Defines a multi-step pipeline across any sequence of neuroflow commands — then runs them in order, **one step per invocation**. Each `/pipeline` run executes the next pending step, saves the plan, and ends by naming the command for the step after it. Phase commands are conversations that stop to ask questions, so chaining several in one turn blurs where a step ended and floods the context; the saved `pipeline-plan.md` carries the state between steps instead. Two modes:

- **Interactive mode** (default) — asks before each step, shows what was done after it. The user can adjust, skip, or stop at any point.
- **Brutal mode** (`--executor`) — no questions: the plan is confirmed once, then every invocation runs the next pending step straight away. Designed for experienced users who trust the plan and want maximum throughput.

The pipeline can be built from:
1. **What already exists** — reads `.neuroflow/` to infer which phases are done and what remains
2. **A user-supplied plan** — the user describes a sequence and the command formalizes it
3. **A combination** — infers the current state, then asks the user to confirm or extend the plan

---

## Step 1 — Detect mode

Check whether the user invoked with `--executor`:

- If `--executor` is present → **brutal mode**. No question before a step; the plan is confirmed once, when it is first saved.
- Otherwise → **interactive mode**. Ask before each step.

Either way, this invocation runs at most one step (Step 5).

---

## Step 2 — Read project state

Read `.neuroflow/project_config.md` and `.neuroflow/flow.md`.

Extract:
- Active phase (`active_phase` in the `project_config.md` frontmatter)
- Phases already worked on (subfolders listed in `flow.md`)
- Research question, modality, tools (from `project_config.md`)

If `.neuroflow/` does not exist: ask the user to run `/neuroflow:neuroflow` first to initialize the project, then stop.

If `.neuroflow/pipeline/pipeline-plan.md` already exists, go to **Continuing a pipeline** (below) instead of building a new plan.

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
2. Map what remains using the standard research sequence (a pragmatic subset of the full canonical order — see the **Phase taxonomy** in `neuroflow:neuroflow-core`; include `preregistration`, `tool-build`/`tool-validate`, the `brain-*` track, `poster`, or `write-report` when the project's config or existing folders call for them):

```
ideation → preregistration? → grant-proposal? → experiment? → data → data-preprocess → data-analyze → paper
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
- In **brutal mode** (`--executor`): skip this question — every pending step runs, one per invocation (the mode already implies full execution).

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
Mode: interactive | brutal (--executor)
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

Log the decision as one line appended to `.neuroflow/reasoning/pipeline.jsonl` (one JSON object per line — neuroflow-core):
```json
{"statement": "Pipeline defined with N steps: [list]", "source": "command:pipeline | YYYY-MM-DD", "reasoning": "Steps inferred from project state / supplied by user. Mode: interactive|brutal. Stop after: [phase or 'all'].", "at": "YYYY-MM-DDTHH:MM:SSZ"}
```

---

## Step 5 — Run the next step (one per invocation)

Run **exactly one** step per invocation: the first `pending` step within the stop point. Steps marked `done`, `skipped`, `error` or `deferred` (beyond the chosen stop point) are not run.

### Interactive mode (default)

1. Announce the step:
   > **Step N of M: /[command]**
   > I'm about to run `/neuroflow:[command]`. This will [brief description of what the command does].
   >
   > Ready to proceed? (Y / skip / stop)

2. If the user says **Y** or just hits enter: run the command inline. Follow every instruction in the corresponding command file exactly as if the user had invoked it directly — including its own questions. The step is done when the command's work is done, not when a turn ends.
3. If the user says **skip**: mark that step as `skipped` in `pipeline-plan.md`, log the skip in the session file, and end this invocation — the next one runs the step after it.
4. If the user says **stop** or **pause**: stop the pipeline. Print a summary of completed steps so far. Tell the user they can resume by running `/neuroflow:pipeline` again — the plan in `pipeline-plan.md` will be picked up and completed steps will be skipped.

### Brutal mode (`--executor`)

1. On the invocation that saves the plan, print it once and confirm with the user:
   > "Brutal mode — no questions before each step. Every `/neuroflow:pipeline --executor` runs the next of N steps. Last chance to cancel. Continue? (Y/n)"

2. On every brutal invocation, run the next pending step inline straight away, exactly as written in its command file — no "Ready to proceed?" question.

3. For an unattended run, let Claude Code's built-in `/loop` re-invoke it (`/loop /neuroflow:pipeline --executor`) and end the loop once no pending step is left. A step that needs the user's answer still waits for it.

### After the step — both modes

- Check the step's outputs: the files listed under `produces:` in its command's frontmatter should now exist (match templated names such as dates loosely). If one is missing, the step is not done — interactive mode: say so and offer retry / skip / stop; brutal mode: treat it as an error (Error handling)
- Update the step status to `done` in `pipeline-plan.md` with the completion date
- Append `## HH:MM — [pipeline] Step N /[command] done — [main output]` to `.neuroflow/sessions/YYYY-MM-DD.md`
- Print the result and the next command, then end the invocation — never start the next step in the same invocation:
  > ✅ `/[command]` complete (Step N of M). Next: `/neuroflow:pipeline` → Step N+1: /[next-command]. Long step? Run `/compact` first.
- If no pending step is left within the stop point, go to Step 6 instead.

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
  — experiment (skipped at your request)

Files written: [list of key outputs]
Next suggested step: /neuroflow:pipeline  (to continue from /paper)
```

If all steps including deferred ones are done, omit the "Deferred" section and suggest the natural follow-up of the last step that ran — after `/paper`, that is `/neuroflow:paper --submit` (journal submission package). Never suggest `/neuroflow:review` as a pipeline follow-up: `/review` referees a colleague's paper, not the user's own.

Update `pipeline-plan.md` with final statuses.

Append a final entry to `.neuroflow/sessions/YYYY-MM-DD.md` summarising the full pipeline run (`## HH:MM — [pipeline] complete — N/M steps executed`).

Log the final decision as one line appended to `.neuroflow/reasoning/pipeline.jsonl`:
```json
{"statement": "Pipeline run complete: N/M steps executed.", "source": "command:pipeline | YYYY-MM-DD", "reasoning": "All pending pipeline steps completed. Skipped steps: [list or none].", "at": "YYYY-MM-DDTHH:MM:SSZ"}
```

---

## Continuing a pipeline

Every invocation after the first finds `pipeline-plan.md` and continues it:

1. Read the existing plan and show one status line:
   > "Pipeline: 2 of 5 steps done. Next: Step 3 — /[next-pending-command]."
   If the plan header has a `Stopped:` line, show it and ask how to proceed (retry the failed step / skip it / stop) before running anything — in brutal mode too; remove the line once the user has decided.
2. If pending steps remain within the stop point → go to Step 5 and run the next one. In interactive mode its "Ready to proceed?" question also offers **restart** (build a new plan from Step 3) and **change stop point** (re-run Step 3b, keeping completed steps intact).
3. If none remain but `deferred` steps exist:
   > "You stopped after /[stop-phase]. Deferred: /[deferred-phases]. Continue?"
   On yes, promote the `deferred` steps to `pending`, re-run Step 3b for the new stop point, then go to Step 5.
4. If every step is done → print the Step 6 summary again and suggest the follow-up.

---

## Error handling

If a step fails or produces an unexpected result:

- **Interactive mode:** stop, report the error clearly, and ask the user how to proceed:
  > "⚠️ Step N (/[command]) encountered a problem: [description]. Options: retry / skip / stop"
- **Brutal mode:** log the error to `pipeline-plan.md` and the session file, mark the step as `error`, and end the invocation — the next one moves on to the next pending step. When that next step needs the failed step's outputs (they are listed in its `requires:` frontmatter, or it plainly consumes them — `/data-analyze` after a failed `/data-preprocess`), or after two `error` steps in a row, stop the run instead: add `Stopped: Step N error — [reason]` under the plan header, and end the `/loop` if one drives the run. List every error in the Step 6 summary.

Never silently swallow errors. Always surface them — in brutal mode at the summary, in interactive mode immediately.
