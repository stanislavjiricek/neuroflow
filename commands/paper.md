---
name: paper
description: Unified manuscript writing and review command — drafts a neuroscience paper section by section, then runs every draft through a brutal paper-writer → paper-critic loop before saving anything.
phase: paper
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/fails/core.md
  - .neuroflow/fails/science.md
  - .neuroflow/fails/ux.md
  - .neuroflow/ideation/flow.md
  - .neuroflow/data-analyze/flow.md
  - .neuroflow/paper/flow.md
  - skills/phase-paper/SKILL.md
writes:
  - .neuroflow/paper/
  - .neuroflow/paper/flow.md
  - .neuroflow/paper/critic-log.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /paper

Read the `neuroflow:phase-paper` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/paper/flow.md` before starting. Load upstream context from `.neuroflow/ideation/` (research question, hypothesis) and `.neuroflow/data-analyze/` (results summary, figures).

Apply `neuroflow:humanizer` to every section draft before passing it to the critic — strip AI signatures, fix rhythm, and calibrate register so the prose reads as genuinely human-authored.

## What this command does

Produces a reviewed and approved manuscript — not a raw draft. Every section goes through a structured write→critique loop before it is saved. Nothing is written to disk without critic approval or an explicit user decision to accept an unresolved draft.

Gather four inputs before proceeding:

1. What is the target journal?
2. LaTeX or Word format?
3. Which section(s) should be drafted in this session, or should the full paper be attempted?
4. Is there a specific review focus, or should the critic apply its full six-area methodology to every section?

---

## Workflow

### Step 1 — Activate paper-writer

Pass the four inputs (target journal, format, section scope, review focus) to the `paper-writer` agent. The agent reads upstream phase memory before drafting and presents each section as a standalone draft block.

Drafting order if doing the full paper: Methods → Results → Introduction → Discussion → Abstract (always last).

### Step 2 — Activate paper-critic (after each section draft)

Pass the section draft plus the rubric to the `paper-critic` agent. The critic applies the full `neuroflow:review-neuro` six-area methodology (Language, Internal Consistency, Claim Support, Statistics, Methods Reproducibility, Contribution/Novelty) and returns either `[STATUS: APPROVED]` or `[STATUS: REJECTED]`.

### Step 3 — Worker-critic loop (up to 3 iterations per section)

Follow the `neuroflow:worker-critic` loop protocol strictly:

```
paper-writer (Initial Draft mode) → draft v1
paper-critic (draft v1 + rubric)  → [STATUS: APPROVED] or [STATUS: REJECTED] + feedback

if APPROVED → proceed to next section
if REJECTED → paper-writer (Revision mode: draft v1 + feedback) → draft v2
              paper-critic (draft v2) → verdict

if APPROVED → proceed to next section
if REJECTED → paper-writer (Revision mode: draft v2 + feedback) → draft v3
              paper-critic (draft v3) → verdict

if APPROVED → proceed to next section
if REJECTED (3rd rejection) → halt loop for this section
                              present draft v3 and unresolved critique to user
                              append unresolved feedback to .neuroflow/paper/critic-log.md
                              ask user whether to continue with the next section or stop
```

**After each section verdict — immediately, before moving to the next section:**
- Append a one-liner to `.neuroflow/sessions/YYYY-MM-DD.md`: section name, verdict (`approved` / `halted at v3`), and iteration count
- If any editorial or framing decision was made (target journal confirmed, scope narrowed, section order changed), append to `.neuroflow/reasoning/paper.json`

### Step 4 — Save approved sections only

After each `[STATUS: APPROVED]` verdict, save the approved draft to `output_path` (default: `manuscript/`) — not inside `.neuroflow/`. Do not save a section until it is approved or the user explicitly accepts an unresolved draft.

Write loop state to `.neuroflow/paper/critic-log.md` after each iteration using the format defined in `neuroflow:worker-critic`.

---

## At end

- Save approved section drafts to `output_path` (from `.neuroflow/paper/flow.md`, default: `manuscript/`) — not inside `.neuroflow/`
- Update `.neuroflow/paper/flow.md`
- Update `.neuroflow/paper/critic-log.md` with final loop outcome for each section
- Confirm that session entries were appended to `.neuroflow/sessions/YYYY-MM-DD.md` after each section verdict during the session — if any were missed, append them now
- Confirm that any framing or scope decisions were written to `.neuroflow/reasoning/paper.json` as they occurred — if any were missed, append them now
- Update `project_config.md` if phase changed
