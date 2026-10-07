---
title: /neuroflow
---

# `/neuroflow:neuroflow`

**The main entry point for every neuroflow project.**

`/neuroflow` is the first command you run in any project folder. It either shows you the current status of an existing project or interviews you and creates the `.neuroflow/` project memory structure from scratch.

---

## When to use it

- **New project** — run `/neuroflow` to create `.neuroflow/` and get oriented
- **Returning to a project** — run `/neuroflow` to see your current phase and status at a glance
- **Starting a new session** — it's a good habit to run `/neuroflow` at the beginning of each work session

---

## What it does

### Existing project

If `.neuroflow/project_config.md` already exists, `/neuroflow` reads it and prints a brief status:

```
Current phase: data-preprocess
Research question: Does auditory attention modulate N2 amplitude in healthy adults?
Last session: 2026-03-09

Continue? Or switch phase / do something specific?
```

It then asks what you want to do next — continue, switch phase, or something else — as a menu you answer with the arrow keys or a click. No setup, no interview, just status + next step. Started from a subfolder, it finds the project in the folder above.

Two one-time checks can appear here:

- **Older project format** — if `project_config.md` predates the current format, it offers [`/migrate`](migrate.md).
- **Global instructions** — if an older neuroflow version wrote a neuroflow block into your `~/.claude/CLAUDE.md`, it shows you the block and offers to remove it (that block pushes one project's phase into every Claude Code session on your machine). Nothing is removed without your yes.

### New project

If `.neuroflow/` does not exist, `/neuroflow` runs through a setup sequence:

**1. Scan the repo**

Claude inspects your folder automatically before asking anything. It looks for signals:

| What it finds | Inferred signal |
|---|---|
| `sub-*/`, `dataset_description.json`, `participants.tsv` | BIDS dataset → data phase |
| `*.py`, `*.m`, `*.R` analysis scripts | Processing underway |
| `derivatives/`, `results/`, `figures/` | Analysis done |
| `*.tex`, `*.docx`, `manuscript/` | Writing phase |
| `paradigm/`, `*.psyexp` PsychoPy scripts | Experiment phase |
| Empty or only README | Fresh start |

**2. Short interview**

Claude asks a few focused questions — one or two at a time:

- What are you working on?
- Project name and institution?
- Neuroscience modality? (EEG, fMRI, iEEG, eye tracking, ECG, other)
- Programming language and tools?
- Phase-specific questions based on what you described

**3. Create `.neuroflow/`**

A small script (`scaffold.py` in the `neuroflow-core` skill) creates the structure in one step. It never overwrites a file that already exists:

```
.neuroflow/
├── project_config.md    ← frontmatter facts (active phase, recommended phases, collaborators) + your notes
├── flow.md              ← index of all subfolders
├── sessions/            ← daily session logs (local only, gitignored)
├── tasks/               ← project task board
├── wiki/                ← project wiki skeleton
└── reasoning/
    └── general.jsonl    ← project-level decisions (JSON Lines)
```

It also adds a few lines to `.gitignore` (session logs, confidential reviews and credentials stay out of git) and to `.gitattributes` (append-only logs merge without conflicts).

Your personal answers — whether neuroflow may offer issue reports, your preferred working mode, your name and writing style — go to `~/.neuroflow/user.yaml` on your machine, never into the shared project files.

**4. Add the neuroflow block to `.claude/CLAUDE.md`**

Claude Code loads this file whenever the folder is opened. The block is static — it names no phase, so it never goes stale:

```markdown
## neuroflow

This project uses neuroflow, a Claude Code plugin. Project memory is in `.neuroflow/`.

- Read `.neuroflow/project_config.md` (its frontmatter holds `active_phase` and the other project facts) and `.neuroflow/flow.md` at the start of every session.
- Record project decisions in `.neuroflow/reasoning/`, not in Claude's auto-memory.
- Keep this block static: no phase or other changing facts here.
```

The block is written only to the project's `.claude/CLAUDE.md` — never to your global `~/.claude/CLAUDE.md`.

**5. Optional: integration setup**

Asks whether you want to set up integrations now — Miro (which you add yourself, in your own terminal) and a custom LLM gateway. You can skip and run `/neuroflow:setup` later. neuroflow never asks you to paste a token into the chat.

**5b. Optional: fewer permission prompts**

Offers once to allow neuroflow's routine bookkeeping writes (session logs, decision logs, `flow.md` indexes) without a prompt each time, by adding three narrow `Edit(...)` rules to `.claude/settings.json`. You see the exact rules first; nothing is added without your yes.

**6. Checklist and next step**

Prints a short checklist of what is set up and what is still open (objectives, timeline, integrations), then suggests the next command for your phase.

---

## Example session

```
/neuroflow:neuroflow
```

```
I found a `paradigm/` folder with PsychoPy scripts and a `scripts/` folder with Python code.
This looks like an EEG study in progress.

What are you working on?
> An auditory oddball study on attention modulation in healthy adults.

Project name and institution?
> OddballStudy2026 — University of Example

Modality?
> EEG (64 channels)

Tools?
> Python + MNE, PsychoPy

Is the data already collected?
> Yes — data is in BIDS format under data/

✅ Created .neuroflow/
✅ Active phase: data-preprocess

Next step: /neuroflow:data-preprocess
```

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `~/.neuroflow/user.yaml`, `~/.neuroflow/flowie/` (if set up), `~/.claude/CLAUDE.md` (only to find an old neuroflow block) |
| Writes | `.neuroflow/` (scaffold), `.neuroflow/project_config.md`, `.neuroflow/objectives.md`, `.neuroflow/timeline.md`, `.neuroflow/sessions/YYYY-MM-DD.md`, `.claude/CLAUDE.md`, `.gitattributes`, `.gitignore`, `~/.neuroflow/user.yaml`, `.claude/settings.json` (only if you agree) |

---

## Related commands

- [`/setup`](setup.md) — set up integrations (Miro, Google Workspace, a custom LLM gateway)
- [`/phase`](phase.md) — check or switch the active phase
- [`/migrate`](migrate.md) — bring an older project up to the current format
- [`/sentinel`](sentinel.md) — audit `.neuroflow/` for consistency
