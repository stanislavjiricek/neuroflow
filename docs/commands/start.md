---
title: /start
---

# `/neuroflow:start`

**The main entry point for every neuroflow project.**

`/start` is the first command you run in any project folder. It either shows you the current status of an existing project or interviews you and creates the `.neuroflow/` project memory structure from scratch.

---

## When to use it

- **New project** — run `/start` to create `.neuroflow/` and get oriented
- **Returning to a project** — run `/start` to see your current phase and status at a glance
- **Starting a new session** — it's a good habit to run `/start` at the beginning of each work session

---

## What it does

### Existing project

If `.neuroflow/project_config.md` already exists, `/start` reads it and prints a brief status:

```
Current phase: data-preprocess
Research question: Does auditory attention modulate N2 amplitude in healthy adults?
Last session: 2026-03-09

Continue? Or switch phase / do something specific?
```

It then waits for your instruction — no setup, no interview, just status + next step.

### New project

If `.neuroflow/` does not exist, `/start` runs through a setup sequence:

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

```
.neuroflow/
├── project_config.md    ← research question, modality, tools, active phase
├── flow.md              ← index of all subfolders
├── sessions/            ← daily session logs (.gitignore this)
└── reasoning/
    └── general.json     ← project-level decisions (JSON)
```

**4. Update `.claude/CLAUDE.md`**

Appends a neuroflow block so Claude always loads project context automatically:

```markdown
## neuroflow

This project uses the neuroflow workflow. Project memory is in `.neuroflow/`.

- Active phase: ideation
- Config: `.neuroflow/project_config.md`
- Start any session by reading `project_config.md` and `flow.md` first.
```

**5. Optional: integration setup**

Asks whether you want to connect PubMed and Miro now. You can skip and run `/neuroflow:setup` later.

**6. Suggest next step**

Based on your phase, Claude suggests the next command to run.

---

## Example session

```
/neuroflow:start
```

```
I found a `paradigm/` folder with PsychoPy scripts and a `scripts/` folder with Python code.
This looks like an EEG study in progress.

What are you working on?
> An auditory oddball study on attention modulation in healthy adults.

Project name and institution?
> OddballStudy2026 — Charles University, Prague

Modality?
> EEG (64-channel BrainProducts)

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
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/integrations.json` |
| Writes | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md`, `.neuroflow/integrations.json`, `.claude/CLAUDE.md` |

---

## Related commands

- [`/setup`](setup.md) — configure PubMed and Miro credentials
- [`/phase`](phase.md) — check or switch the active phase
- [`/sentinel`](sentinel.md) — audit `.neuroflow/` for consistency
