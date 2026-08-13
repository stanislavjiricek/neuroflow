---
title: Project Memory
---

# Project Memory

**Project memory is the `.neuroflow/` folder at the root of your project repository.**

It is the shared brain of your neuroflow project — a set of structured Markdown and JSON files that every command reads at the start of a session and writes to at the end. This means Claude always knows your research question, your active phase, and what has been done before — without you having to re-explain anything.

---

## Structure

```
.neuroflow/
├── project_config.md       ← current phase, research question, modality, tools, plugin_version
├── flow.md                 ← index of all subfolders
├── sentinel.md             ← sentinel audit report
├── timeline.md             ← milestones and deadlines (optional)
├── sessions/               ← one .md per day — add to .gitignore
├── reasoning/              ← structured per-phase decision logs (JSON)
├── ethics/                 ← IRB documents, consent forms
├── preregistration/        ← OSF / AsPredicted documents
├── finance/                ← grant documents, expense tracking
├── ideation/               ← research questions, proposals, literature reviews
├── grant-proposal/         ← grant application drafts
├── experiment/             ← paradigm scripts, recording setup docs
├── tool-build/             ← tool specs and build notes
├── tool-validate/          ← validation plans and results
├── data/                   ← data inventory and intake reports
├── data-preprocess/        ← preprocessing configs and QC reports
├── data-analyze/           ← analysis plans and result summaries
├── paper/                  ← manuscript drafts and critic logs
├── notes/                  ← structured notes from meetings and talks
└── write-report/           ← project reports
```

---

## Key files

### `project_config.md`

The most important file in `.neuroflow/`. Every command reads this first. It contains:

- **Project name and institution**
- **Active phase** — which pipeline phase is currently in progress
- **Research question** — the core scientific question
- **Modality** — EEG, fMRI, iEEG, eye tracking, etc.
- **Tools** — Python/MNE, MATLAB, R, etc.
- **`plugin_version`** — tracked by sentinel to flag plugin updates
- **Output paths** — where each phase writes its files (code, results, figures, manuscripts)

**Example:**

```markdown
# project_config.md

project: OddballStudy2026
institution: Charles University, Prague
plugin_version: 0.1.2

active_phase: data-preprocess

research_question: Does white noise background (65 dB) reduce P300 amplitude 
                   in a visual oddball task compared to silence?

modality: EEG (BrainProducts actiCHamp, 64 ch)
tools: Python 3.11, MNE 1.6, PsychoPy 2024

## Output paths

| Phase | Path |
|---|---|
| experiment | paradigm/ |
| data-preprocess | scripts/preprocessing/ |
| data-analyze | scripts/analysis/, results/, figures/ |
| paper | manuscript/ |
```

### `flow.md`

An index of everything in `.neuroflow/`. Each subfolder has its own `flow.md` too — an index of the files inside it. Commands use `flow.md` to navigate without scanning the whole disk.

### `reasoning/`

Structured per-phase decision logs in JSON format. Each entry has three fields:

```json
{
  "statement": "Using average reference instead of linked mastoids",
  "source": "data-preprocess session 2026-03-05",
  "reasoning": "Linked mastoids are not appropriate for this cap layout; average reference is standard for 64-channel EEG"
}
```

### `sessions/`

One Markdown file per day, automatically appended to by every command. Gives you a chronological log of what was done.

!!! warning "Add to .gitignore"
    Session logs are local — they may contain personal notes and intermediate thoughts. Add `.neuroflow/sessions/` to your `.gitignore`.

---

## How commands use project memory

Every command follows the same lifecycle:

```
1. Read neuroflow-core skill          ← understand the lifecycle rules
2. Read project_config.md             ← orient to the current project
3. Read root flow.md                  ← understand what has been done
4. Read phase-specific flow.md        ← understand what exists in this phase
5. Do the work (interact with user)
6. Write outputs to phase subfolder
7. Update flow.md
8. Append to sessions/YYYY-MM-DD.md
9. Update project_config.md if phase changed
```

This means every command has full project context without you needing to paste anything.

---

## Multiple projects

Cross-project context lives at the personal and team levels rather than in per-project link files: your global [flowie profile](flowie.md) tracks all your projects in its registry (`~/.neuroflow/flowie/projects/`), and a shared [hive](../commands/hive.md) connects projects across a team. (Earlier versions used a `linked_flows.md` file — removed in 0.2.17.)

---

## Git recommendations

```gitignore
# Add to your project .gitignore:
.neuroflow/sessions/          # local daily logs
.neuroflow/integrations.json  # credential file (already excluded by neuroflow)
```

Everything else in `.neuroflow/` should be git-tracked — it is the shared memory of your project and should be part of the repo.
