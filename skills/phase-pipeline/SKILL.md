---
name: phase-pipeline
description: Phase guidance for the neuroflow /pipeline command. Loaded automatically when /pipeline is invoked to orient agent behavior for planning and executing multi-step research pipelines.
---

# phase-pipeline

The `/pipeline` command orchestrates a sequence of neuroflow commands in order — either interactively (pause and confirm at each step) or in brutal mode (`--nomistake`, run straight through without stops).

## Approach

- **Read the project state before proposing anything.** The pipeline must reflect where the project actually is, not a generic template. Check `flow.md` for completed phases and `project_config.md` for the active phase and tools.
- **Be conservative when inferring what is "done".** A phase subfolder exists if any work happened there — but "done" in a pipeline context means the user intentionally finished that phase. When in doubt, mark it `[pending]` and let the user decide.
- **Never skip a step silently.** Every skip must be user-initiated and logged.
- **In brutal mode, speed is the goal — but accuracy is non-negotiable.** Each step must still follow its command's instructions fully. Brutal mode removes pauses, not thoroughness.
- **Resume gracefully.** When re-invoked on a project with an existing `pipeline-plan.md`, read it first, show the current status, and continue from where execution stopped.
- **Always ask where to stop.** After presenting the plan (in interactive mode), ask the user to choose their stop point before executing anything. This lets them run the pipeline in stages without having to manually stop mid-run.

## Interactive vs brutal mode

| Behaviour | Interactive | Brutal (`--nomistake`) |
|---|---|---|
| Pause between steps | ✅ Always | ❌ Never |
| Ask where to stop | ✅ Yes (Step 3b) | ❌ No — all pending steps run |
| User can skip individual steps | ✅ Yes | ❌ No — all pending steps run |
| User can stop mid-pipeline | ✅ Yes | ❌ Errors logged; pipeline continues |
| Error handling | Stop and ask | Log and continue; report at end |
| Summary at end | ✅ Yes | ✅ Yes (more detailed) |

## Stop-point selection

After the plan is confirmed (Step 3b in the command), present numbered choices for each pending phase plus an "all the way through" option. The user's answer determines the `stop_after` value:

- **Specific phase chosen:** mark all subsequent steps as `[deferred]` in `pipeline-plan.md`. Save `Stop after:` in the plan header. Execute only up to the stop point.
- **All the way through:** run the full plan. Trigger the full-journey joke (see below).
- **Brutal mode:** skip the question entirely — all steps run regardless.

When resuming, `[deferred]` steps are surfaced prominently so the user knows there is more to run. Re-run Step 3b on resume to let the user pick a new (or extended) stop point.

## Full-journey joke

When the user selects the full pipeline covering the complete research journey (ideation → paper), generate a **fresh, original joke** on the spot. Rules:

- Never use a preset joke. Generate a new one each time.
- Keep it short — one or two lines.
- Theme: the absurdity/bravery of doing an entire research project in one uninterrupted sitting. Academic, neuroscience, statistics, or publication-pressure humour all work.
- Follow the joke immediately with: "Alright, brave soul. Let's do this. 🚀"

## Standard research pipeline sequence

Use this as the default order when inferring a pipeline from project state:

```
ideation → grant-proposal (optional) → experiment (optional) → tool-build (optional) → tool-validate (optional) → data → data-preprocess → data-analyze → paper
```

Brain simulation phases insert between `data-analyze` and `paper`:
```
… → data-analyze → brain-build → brain-optimize → brain-run → paper → …
```

Phases marked `optional` should only be included if:
- The user explicitly requests them, OR
- Evidence of that phase's work exists in `.neuroflow/` or the repo

## Pipeline plan format

The `pipeline-plan.md` file is the canonical record of what was planned and what happened. Keep it up to date as execution proceeds — treat it as a live log, not a one-time snapshot.

```markdown
# Pipeline plan
Generated: YYYY-MM-DD
Mode: interactive | brutal (--nomistake)
Stop after: /data-analyze | all the way through

## Steps

| # | Command | Status | Notes |
|---|---|---|---|
| 1 | /ideation | done | Completed YYYY-MM-DD |
| 2 | /data | pending | — |
| 3 | /data-analyze | pending | — |
| 4 | /paper | deferred | Beyond stop point — resume to continue |
```

Valid status values: `pending`, `done`, `skipped`, `error`, `deferred`

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle, `.neuroflow/` write rules, and the end-of-command checklist
- `neuroflow:neuroflow-develop` — relevant when the pipeline includes plugin development steps or when the user is building something inside neuroflow itself

## Workflow hints

- Log the pipeline plan to `reasoning/pipeline.json` at the start and update it at the end — this pipeline definition is a significant project-level decision
- Log the chosen stop point in `reasoning/pipeline.json` — it is a deliberate scope decision
- Update `pipeline-plan.md` after every step, not just at the end
- If the user adjusts the plan mid-run (adds a step, changes order, changes stop point), write a new `reasoning/pipeline.json` entry recording the change and why
- In brutal mode, print a brief progress line after each step so the user can follow along even without interactive prompts
- Never create a phase subfolder just for the pipeline — all memory goes in `.neuroflow/pipeline/`
