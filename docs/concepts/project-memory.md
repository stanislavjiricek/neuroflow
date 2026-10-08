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
├── project_config.md       ← frontmatter facts (active phase, recommended phases, collaborators) + notes
├── flow.md                 ← index of all subfolders
├── sentinel.md             ← sentinel audit report
├── timeline.md             ← milestones and deadlines (optional)
├── sessions/               ← one .md per day — local only, gitignored
├── reasoning/              ← per-phase decision logs (JSON Lines)
├── tasks/                  ← project task board, one file per task
├── wiki/                   ← project wiki (its .pending/ review queue is local only)
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

The most important file in `.neuroflow/`. Every command reads this first. It has two parts:

- **A YAML frontmatter** with the facts commands and scripts read: `nf_schema` (format version), `project_name`, `active_phase`, `recommended_phases`, optional `default_mode`, `target_journal`, `raw_roots`, `hive_repo`, `collaborators`, and `plugin_version` (the neuroflow version the project was last brought up to date to — only the scaffold and `/neuroflow:migrate` write it)
- **Free markdown notes** — institution, research question, modality, tools, and the output paths each phase writes to

**Example:**

```markdown
---
nf_schema: 1
project_name: OddballStudy2026
active_phase: data-preprocess
recommended_phases: [experiment, data, data-preprocess, data-analyze, paper]
target_journal: NeuroImage
raw_roots: [sourcedata/]
plugin_version: 0.2.22
---

# OddballStudy2026

Institution: University of Example

Research question: Does white noise background (65 dB) reduce P300 amplitude
in a visual oddball task compared to silence?

Modality: EEG (64 channels). Tools: Python 3.11, MNE 1.6, PsychoPy 2024.

## Output paths

| Phase | Path |
|---|---|
| experiment | paradigm/ |
| data-preprocess | scripts/preprocessing/ |
| data-analyze | scripts/analysis/, results/, figures/ |
| paper | manuscript/ |
```

Projects created by older neuroflow versions use plain `key: value` lines or bold labels instead of the frontmatter. Commands still read them; [`/migrate`](../commands/migrate.md) converts them after showing you the plan.

### Personal settings — `~/.neuroflow/user.yaml`

Some answers are about you, not the project: whether neuroflow may offer issue reports, your preferred working mode, your name and writing style. They live in `~/.neuroflow/user.yaml` on your machine — never in `project_config.md`, which your collaborators share through git.

### `flow.md`

An index of everything in `.neuroflow/`. Each subfolder has its own `flow.md` too — an index of the files inside it. Commands use `flow.md` to navigate without scanning the whole disk.

### `reasoning/`

Per-phase decision logs in JSON Lines format — one file per phase (`data-preprocess.jsonl`, plus `general.jsonl` for project-level decisions), one decision per line, only ever appended to:

```json
{"statement": "Use the average reference instead of linked mastoids", "source": "command:data-preprocess | 2026-03-05", "reasoning": "Linked mastoids do not suit this cap layout; the average reference is standard for 64-channel EEG", "at": "2026-03-05T10:12:00Z"}
```

One line per entry means two collaborators can add decisions on the same day and git merges both without a conflict.

### `sessions/`

One Markdown file per day, automatically appended to by every command. Gives you a chronological log of what was done.

!!! note "Local only"
    Session logs may contain personal notes and intermediate thoughts, so they stay on your machine — `/neuroflow` adds `.neuroflow/sessions/` to your `.gitignore`.

---

## How commands use project memory

Every command follows the same lifecycle. Started from a subfolder, a command finds `.neuroflow/` in the folder above (up to the repository root).

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

`/neuroflow` (and `/migrate` for older projects) adds these lines to your project's `.gitignore`, so local-only memory never reaches git:

```gitignore
.neuroflow/sessions/
.neuroflow/review/
.neuroflow/integrations.json
.neuroflow/flowie/
.neuroflow/paper/xray-*
.neuroflow/wiki/.pending/
```

`.neuroflow/review/` holds manuscripts you referee in confidence; `integrations.json` holds credentials; `paper/xray-*` files are the sentence-level critique of your unpublished manuscript (`/paper --xray`); `wiki/.pending/` holds wiki cards waiting for your review (`/wiki --review`). These local-only paths are never exported either: `/output` drops them before anything is copied.

It also adds union-merge rules to `.gitattributes`, so append-only logs (decision logs, session logs, `fails/`, preregistration deviations) merge cleanly when two collaborators add entries on the same day:

```
.neuroflow/reasoning/*.jsonl merge=union
.neuroflow/sessions/*.md merge=union
.neuroflow/fails/*.md merge=union
.neuroflow/preregistration/deviations.md merge=union
.neuroflow/data-analyze/multiverse.md merge=union
```

Everything else in `.neuroflow/` should be git-tracked — it is the shared memory of your project and should be part of the repo.
