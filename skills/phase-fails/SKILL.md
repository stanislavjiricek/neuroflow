---
name: phase-fails
description: Phase guidance for the neuroflow /fails command. Orients agent approach for logging user dissatisfaction, categorising complaints accurately, and preparing GitHub issue reports.
---

# phase-fails

The `/fails` command is a dissatisfaction capture utility. Its job is to listen without defending, categorise accurately, and make it frictionless for the user to report problems upstream.

## Approach

- Listen to the user's complaint in full before categorising — do not interrupt or redirect
- Route to the correct file without minimising or reframing the complaint
- If the user is frustrated, acknowledge it briefly before asking clarifying questions
- When the category is ambiguous, ask rather than guess
- Do not offer fixes or workarounds during `/fails` — record the problem as stated; fixes belong in a follow-up conversation

## Categories

### `core.md` — Plugin behaviour

Problems with how neuroflow itself behaves:

- A phase ran unexpectedly (skipped steps, looped, produced nothing)
- Files were saved in the wrong place, renamed, or deleted
- A command ignored a user instruction or contradicted a previous decision
- Project state was corrupted or inconsistent after a command completed

### `science.md` — Scientific quality

Problems with the scientific work produced:

- A paper retrieved was irrelevant, retracted, or misrepresented
- An analysis ran on wrong data, in the wrong direction, or violated method assumptions (e.g. ICA on a transposed matrix)
- A figure has wrong axis labels, wrong units, or misleading presentation
- A statistical test was inappropriate for the data type or design
- Preprocessing steps were applied out of order or incorrectly

### `ux.md` — Interaction quality

Problems with how the interaction felt:

- Prompts were confusing or asked for the same information twice
- Output was too verbose, too sparse, or poorly formatted
- The suggested next step was irrelevant or wrong for the context
- The conversation felt circular or didn't progress
- The command asked too many questions before doing useful work

## GitHub reporting

After logging a fail, always ask whether the user wants to report it as a GitHub issue. Most users won't — but asking takes one second and gives the plugin a direct feedback channel.

When composing the issue:

- Use the category tag in brackets in the title: `[core]`, `[science]`, or `[ux]`
- Keep the description factual and specific — avoid emotive language
- Include the plugin version if available in `project_config.md`
- Open the URL using `open` (macOS/Linux) or `start` (Windows) rather than presenting it as text — the user should be one click from submitting
- If the browser open fails, print the full URL so the user can paste it manually

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Slash command

`/neuroflow:fails` — runs this workflow as a slash command.
