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

### Core skills

| Skill | What it does |
|---|---|
| `neuroflow:neuroflow-core` | Core rules and lifecycle for all commands and agents — `.neuroflow/` folder spec, command lifecycle, frontmatter standard |
| `neuroflow:review-neuro` | Rigorous pre-submission peer review of a neuroscience manuscript — invoked by `/paper-review` |

### Phase skills

Each research phase has a corresponding skill that orients Claude's approach, suggests relevant domain tools, and provides workflow hints.

| Skill | Associated command |
|---|---|
| `neuroflow:phase-ideation` | `/ideation` |
| `neuroflow:phase-grant-proposal` | `/grant-proposal` |
| `neuroflow:phase-experiment` | `/experiment` |
| `neuroflow:phase-tool-build` | `/tool-build` |
| `neuroflow:phase-tool-validate` | `/tool-validate` |
| `neuroflow:phase-data` | `/data` |
| `neuroflow:phase-data-preprocess` | `/data-preprocess` |
| `neuroflow:phase-data-analyze` | `/data-analyze` |
| `neuroflow:phase-paper-write` | `/paper-write` |
| `neuroflow:phase-paper-review` | `/paper-review` |
| `neuroflow:phase-notes` | `/notes` |
| `neuroflow:phase-write-report` | `/write-report` |
| `neuroflow:phase-brain-build` | `/brain-build` |
| `neuroflow:phase-brain-optimize` | `/brain-optimize` |
| `neuroflow:phase-brain-run` | `/brain-run` |
| `neuroflow:phase-quiz` | `/quiz` |
| `neuroflow:phase-fails` | `/fails` |

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
