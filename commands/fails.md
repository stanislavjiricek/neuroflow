---
name: fails
description: Log user dissatisfaction — record what went wrong in core behavior, science quality, or interaction experience. Optionally prepares a GitHub issue report for the neuroflow team.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/fails/flow.md
  - .neuroflow/fails/core.md
  - .neuroflow/fails/science.md
  - .neuroflow/fails/ux.md
writes:
  - .neuroflow/fails/
  - .neuroflow/fails/flow.md
  - .neuroflow/fails/core.md
  - .neuroflow/fails/science.md
  - .neuroflow/fails/ux.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /fails

Capture and triage dissatisfaction. When something doesn't work the way it should — an analysis was wrong, a phase behaved strangely, or the interaction was confusing — this command records it and optionally opens a GitHub issue.

Read the `neuroflow:phase-fails` skill first. Then follow the neuroflow-core lifecycle.

---

## Step 0 — Check for .neuroflow/

If `.neuroflow/` does not exist, stop and tell the user to run `/neuroflow` first.

---

## Step 1 — Read existing fails

Read `.neuroflow/project_config.md` and `.neuroflow/flow.md`.

If `.neuroflow/fails/` does not exist yet, create it now:

- Create `fails/core.md` with header: `# Core fails — plugin behavior problems`
- Create `fails/science.md` with header: `# Science fails — scientific quality problems`
- Create `fails/ux.md` with header: `# UX fails — interaction quality problems`
- Create `fails/flow.md` with the standard index table (all three files listed, today's date)
- Update the root `.neuroflow/flow.md` to add a row for `fails/`

If `fails/` exists, read `fails/flow.md`, then read whichever of the three files exist.

---

## Step 2 — Ask what went wrong

Ask the user to describe what went wrong. Listen in full before categorising.

Route the complaint to the correct file:

| File | What belongs here |
|---|---|
| `core.md` | Plugin behavior problems — a phase acted unexpectedly, saved files in the wrong place, deleted something, looped without progress, ignored an instruction, or corrupted project state |
| `science.md` | Scientific quality problems — a wrong paper was retrieved, an analysis ran on the wrong data or in the wrong direction, a figure has incorrect axes, statistical assumptions were violated, a method was misapplied |
| `ux.md` | Interaction quality problems — prompts were confusing, output was too verbose or sparse, a suggested next step was wrong, the conversation felt circular, the command asked too many questions |

If the complaint spans more than one category, ask the user which is primary, or split it across files if both aspects are equally important.

---

## Step 3 — Write the fail entry

Append a new entry to the appropriate file(s) in this format:

```
---
date: YYYY-MM-DD
context: <active phase or command where this happened>
description: <one to three sentences describing what went wrong>
expected: <what should have happened instead>
```

If the file has only its header comment, write the first entry directly below it.

---

## Step 4 — Update flow.md

Update `.neuroflow/fails/flow.md` to reflect the current state of each file (description: number of entries, last date). If `fails/` was just created, also update the root `.neuroflow/flow.md`.

---

## Step 5 — Offer to report to GitHub

Ask: *"Do you want to report this to the neuroflow GitHub repo as an issue?"*

- If **no**: confirm the entry was saved, append to the session log, and stop.
- If **yes**: proceed to Step 6.

---

## Step 6 — Prepare and open GitHub issue

Read the entry just written and any relevant context from `project_config.md`. Compose:

- **Title**: Short, specific, with a category tag — e.g. `[core] Phase looped without progress after data-preprocess` or `[science] ICA run on transposed matrix in data-analyze`
- **Body**:

```
## What went wrong
<description from the entry>

## Expected behaviour
<expected from the entry>

## Context
Phase: <context>
Date: <date>
Plugin version: <plugin_version from project_config.md, if present>
```

URL-encode the title and body, then construct the GitHub new-issue URL:

```
https://github.com/stanislavjiricek/neuroflow/issues/new?title=<encoded_title>&body=<encoded_body>
```

Attempt to open the URL in the system browser:
- macOS / Linux: `open "<url>"`
- Windows: `start "<url>"`

If the open command succeeds, confirm to the user that the browser was opened and remind them to review and submit the issue.

If the open command fails or is unavailable, print the full URL so the user can paste it into a browser manually.

---

## Step 7 — Append to session log

Append a brief entry to `.neuroflow/sessions/YYYY-MM-DD.md`:

```
[HH:MM] /fails — Logged a <category> fail: <one-line summary>. GitHub issue: [opened in browser / not reported].
```

---

## Passive monitoring

neuroflow passively monitors every user message for frustration or problem signals (as defined in `neuroflow:neuroflow-core`). When a signal fires:

- If `auto_issue_reporting: yes`: a GitHub issue is opened automatically in the background.
- Always: a one-liner is appended to the appropriate `fails/` file silently.

Use `/fails` when you want to describe an issue in detail, review past fails, or file a structured GitHub report manually. The passive system is a low-friction supplement — not a replacement.
