<div align="center">
  <img src="logo.png" alt="neuroflow" width="80%" />
  <h1>neuroflow</h1>
  <p><strong>A Claude Code plugin for agentic neuroscience research.</strong></p>
  <p>
    <a href="#whats-new">What's new</a> ·
    <a href="#why-neuroflow">Why</a> ·
    <a href="#commands">Commands</a> ·
    <a href="#skills">Skills</a> ·
    <a href="#roadmap">Roadmap</a> ·
    <a href="#installation">Install</a> ·
    <a href="#contributing">Contribute</a>
  </p>
</div>

---

## What's new in 0.1.0

- [`/neuroflow:new-project`](commands/new-project.md) — context-aware project setup: scans your repo, interviews you about what you're working on, writes `.neuroflow/config.json` tailored to your stage
- [`neuroflow:review-neuro`](skills/review-neuro/SKILL.md) — rigorous pre-submission peer review of neuroscience manuscripts
- [`neuroflow:neuroflow-develop`](skills/neuroflow-develop/SKILL.md) — development guide for building and extending the plugin

---

## Why neuroflow

Most neuroscience software solves one problem at a time — a preprocessing library, a stats package, a reference manager. You still have to stitch everything together yourself, re-explain context at every step, and manually translate between tools and phases.

neuroflow is different. It is not a toolbox. It is a **Claude Code plugin** that brings agentic workflows into neuroscience research — from the first hypothesis all the way to a manuscript draft.

You work in your editor. Claude works alongside you — reading your data, writing analysis code, reviewing your paper, auditing your statistics — guided by skills and agents that understand neuroscience domain conventions.

**Focused on:**

- EEG, iEEG, fMRI, eye tracking, ECG, and other physiological signals
- Cognitive, clinical, and preclinical research
- Experimental paradigm development and real-time systems
- From hypothesis formulation to paper draft

---

## Commands

| Command | What it does |
|---|---|
| [`/neuroflow:new-project`](commands/new-project.md) | Interview-based project setup — scans your repo, asks what you're working on, writes `.neuroflow/config.json` |

---

## Skills

Skills are invoked by Claude automatically when relevant, or you can trigger them explicitly.

| Skill | What it does |
|---|---|
| [`neuroflow:review-neuro`](skills/review-neuro/SKILL.md) | Pre-submission peer review of a neuroscience manuscript |
| [`neuroflow:skill-creator`](skills/skill-creator/SKILL.md) | Guide for creating new neuroflow skills |
| [`neuroflow:neuroflow-develop`](skills/neuroflow-develop/SKILL.md) | Guide for developing and maintaining the neuroflow plugin |

---

## Roadmap

Planned additions — contributions welcome:

**Skills**
- EEG preprocessing — MNE-Python pipeline: filtering, ICA, epochs, artifact rejection
- fMRI analysis — GLM, contrasts, ROI extraction, resting state connectivity
- Experimental paradigm design — oddball, N-back, go/no-go, resting state, custom
- Literature review — PubMed + bioRxiv search, synthesis, gap identification
- Statistical analysis audit — assumptions, multiple comparisons, effect sizes
- Results interpretation — ERP components, fMRI clusters, decoding accuracy

**Commands**
- `/analyze` — launch a modality-appropriate analysis pipeline on a dataset
- `/write-paper` — generate a LaTeX manuscript draft from results and figures
- `/check-bids` — validate BIDS directory structure

**Agents**
- `literature-reviewer` — autonomous PubMed/bioRxiv search and synthesis
- `stats-auditor` — audit statistical methods and reporting before submission
- `paradigm-auditor` — verify timing, markers, and edge cases in experiment code
- `data-quality-checker` — assess recording quality, artifacts, and trial counts

---

## Installation

```bash
claude plugin marketplace add stanislavjiricek/neuroflow
claude plugin install neuroflow@neuroflow
```

Or from within Claude Code:

```
/plugin marketplace add stanislavjiricek/neuroflow
/plugin install neuroflow@neuroflow
```

For local development:

```bash
git clone https://github.com/stanislavjiricek/neuroflow
claude --plugin-dir ./neuroflow
```

Once installed, run `/neuroflow:new-project` in any project folder to get started.

---

## Contributing

neuroflow is intentionally small right now — and that's the point. It is designed to grow with the community.

If you work in neuroscience and have a workflow that Claude could help with, contributions are very welcome:

- **New skills** — domain knowledge for a modality, analysis method, or writing task
- **New commands** — multi-step pipelines for common research workflows
- **New agents** — autonomous subprocesses for literature review, data quality, statistics auditing, and more

See [`neuroflow:neuroflow-develop`](skills/neuroflow-develop/SKILL.md) for the development guide, or open an issue to discuss an idea before building.

---

## License

MIT © Stanislav Jiricek
