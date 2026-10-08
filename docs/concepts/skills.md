---
title: Skills
---

# Skills

**Skills are structured domain knowledge that Claude loads automatically when working in a specific phase.**

Skills are not commands you run — they are context files that Claude reads in the background. When you run `/neuroflow:data-preprocess`, Claude automatically loads the `neuroflow:phase-data-preprocess` skill, which gives it neuroscience-specific guidance for that phase: what pipeline steps to apply, what domain conventions to follow, what common pitfalls to avoid.

---

## How skills work

When a command runs, it starts by reading its associated skill. For example:

```
/neuroflow:data-preprocess
  → reads: neuroflow:phase-data-preprocess
  → reads: neuroflow:neuroflow-core (lifecycle rules)
  → reads: project_config.md and flow.md
  → starts the preprocessing pipeline
```

Skills give Claude phase-specific expertise without you having to instruct it manually.

---

## Available skills

### Core skills and protocols

| Skill | What it does |
|---|---|
| `neuroflow:neuroflow-core` | Core rules and lifecycle for all commands and agents — `.neuroflow/` folder spec, the `project_config.md` contract, shared formats (decision logs, integrity markers, merge safety, sharing tiers), command lifecycle and frontmatter standard. Ships `scripts/scaffold.py` (used by `/neuroflow`) and `scripts/migrate.py` (used by `/migrate`) |
| `neuroflow:worker-critic` | Worker-critic loop protocol — a worker agent and a critic agent across up to 3 revision cycles; used by `/paper` and `/poster` |
| `neuroflow:autoresearch-protocol` | The improvement-loop protocol — the single-agent loop, its per-loop wiki, caps, the integrity gate and `ar.py` bookkeeping; used by `/autoresearch` |
| `neuroflow:wiki-protocol` | Knowledge-base protocol for the LLM-maintained wikis at three levels (flowie, project, hive) — ingest, query, lint and add workflows; used by `/wiki`, `/flowie --wiki-*`, `/hive --wiki-*` and `/autoresearch` |

### Domain skills

| Skill | What it does |
|---|---|
| `neuroflow:review-neuro` | Rigorous eight-area peer review of a neuroscience manuscript — invoked by `/review` |
| `neuroflow:bids` | Brain Imaging Data Structure — folder hierarchy, entities, required files per modality, sidecars, derivatives, the validator, pybids and MNE-BIDS; loaded in the data phases |
| `neuroflow:humanizer` | Style editing on request — cuts filler, varies rhythm and matches the register while keeping every fact, number, citation and hedge; never a way to hide AI use, which is always disclosed |
| `neuroflow:pupil-labs-neon-realtime` | Real-time data streams (video, gaze, IMU, events) from Pupil Labs Neon eye-tracking glasses through the Real-time API |

### Integration skills

| Skill | What it does |
|---|---|
| `neuroflow:setup-guide` | Configure integrations — Google Workspace, optional Miro and Anthropic-compatible LLM gateways — without ever asking for a secret in chat; used by `/setup` |
| `neuroflow:notebooklm` | Google NotebookLM through the `notebooklm-py` CLI — notebooks, sources (each upload confirmed first), generated artifacts and downloads |

### Phase skills

Each research phase has a corresponding skill that orients Claude's approach, suggests relevant domain tools, and provides workflow hints.

| Skill | Associated command |
|---|---|
| `neuroflow:phase-git` | `/git` |
| `neuroflow:phase-ideation` | `/ideation` |
| `neuroflow:phase-preregistration` | `/preregistration` |
| `neuroflow:phase-grant-proposal` | `/grant-proposal` |
| `neuroflow:phase-finance` | `/finance` |
| `neuroflow:phase-experiment` | `/experiment` |
| `neuroflow:phase-tool-build` | `/tool-build` |
| `neuroflow:phase-tool-validate` | `/tool-validate` |
| `neuroflow:phase-data` | `/data` |
| `neuroflow:phase-data-preprocess` | `/data-preprocess` |
| `neuroflow:phase-data-analyze` | `/data-analyze` |
| `neuroflow:phase-paper` | `/paper` |
| `neuroflow:phase-review` | `/review` |
| `neuroflow:phase-poster` | `/poster` |
| `neuroflow:phase-notes` | `/notes` |
| `neuroflow:phase-write-report` | `/write-report` |
| `neuroflow:phase-slideshow` | `/slideshow` |
| `neuroflow:phase-brain-build` | `/brain-build` |
| `neuroflow:phase-brain-optimize` | `/brain-optimize` |
| `neuroflow:phase-brain-run` | `/brain-run` |
| `neuroflow:phase-quiz` | `/quiz` |
| `neuroflow:phase-fails` | `/fails` |
| `neuroflow:phase-output` | `/output` |
| `neuroflow:phase-pipeline` | `/pipeline` |
| `neuroflow:phase-search` | `/search` |
| `neuroflow:phase-flowie` | `/flowie` |
| `neuroflow:phase-hive` | `/hive` |
| `neuroflow:phase-meeting` | `/meeting` |

### Development skills

| Skill | What it does |
|---|---|
| `neuroflow:neuroflow-develop` | Guide for developing and maintaining the neuroflow plugin |
| `neuroflow:skill-creator` | Guide for creating new neuroflow skills |

---

## For contributors

If you want to add a new skill:

1. Create a folder under `skills/` with the skill name: `skills/my-new-skill/`
2. Add a `SKILL.md` file with the frontmatter and content
3. Reference the skill from the relevant command with `Read the neuroflow:my-new-skill skill first`

See the `neuroflow:skill-creator` skill for the full authoring guide.

!!! warning "Skills must not create their own folders in .neuroflow/"
    All skill output must be written to the active command's phase subfolder (e.g. `.neuroflow/data-preprocess/`). A skill named `my-skill` must not create `.neuroflow/my-skill/`. The `sentinel-dev` agent checks for this.
