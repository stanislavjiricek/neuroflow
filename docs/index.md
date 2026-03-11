---
title: neuroflow
hide:
  - navigation
  - toc
---

<div class="hero" markdown>
<div id="nf-quotes"></div>
<div class="hero-inner" markdown>
<div class="hero-text" markdown>

**Hi, I'm neuroflow** — a Claude Code plugin and full neuroscience cycle AI assistant.
From first hypothesis to manuscript draft, guided by AI at every step.

[Get started :octicons-arrow-right-24:](quickstart.md){ .md-button .md-button--primary }
[Browse commands :octicons-terminal-24:](commands/index.md){ .md-button }

<p class="hero-community">🌱 <em>Did I fail you? :') I'm in pre-release and open to the community</em> — <a href="https://github.com/stanislavjiricek/neuroflow/issues/new">🐛 open an issue</a> or <a href="https://github.com/stanislavjiricek/neuroflow/pulls">🔀 improve me with a PR</a></p>

</div>
</div>
</div>

---

## Why neuroflow?

Most neuroscience software solves **one problem at a time** — a preprocessing library, a stats package, a reference manager. You still have to stitch everything together yourself, re-explain context at every step, and manually translate between tools and phases.

**neuroflow is different.** It is a Claude Code plugin that brings **agentic workflows** into neuroscience research — from the first hypothesis all the way to a manuscript draft. Claude works alongside you, guided by skills and agents that understand neuroscience domain conventions.

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
<span class="feature-icon">🔗</span>
### End-to-end pipeline
One tool covers the entire research lifecycle — ideation, experiment design, data, analysis, and writing — with no context lost between steps.
</div>

<div class="feature-card" markdown>
<span class="feature-icon">🧠</span>
### Neuroscience-aware AI
Domain-specific skills for EEG, iEEG, fMRI, eye tracking, ECG, and other physiological signals, from cognitive to clinical research.
</div>

<div class="feature-card" markdown>
<span class="feature-icon">💾</span>
### Persistent project memory
All reasoning logs, session notes, and context live in `.neuroflow/` — Claude reads it at the start of every session so you never repeat yourself.
</div>

<div class="feature-card" markdown>
<span class="feature-icon">📊</span>
### Built-in stats auditing
Analysis commands include automated statistical checks to keep your results reproducible and defensible.
</div>

</div>

!!! tip "Who is this for?"
    Neuroscientists working with EEG, iEEG, fMRI, eye tracking, ECG, or other physiological signals — from cognitive and clinical to preclinical research.

---

## The research pipeline

<div class="pipeline-wrap" markdown>
<div class="pipeline" markdown>
<span class="pipeline-step">/ideation</span>
<span class="pipeline-arrow">→</span>
<span class="pipeline-step">/experiment</span>
<span class="pipeline-arrow">→</span>
<span class="pipeline-step">/data</span>
<span class="pipeline-arrow">→</span>
<span class="pipeline-step">/data-preprocess</span>
<span class="pipeline-arrow">→</span>
<span class="pipeline-step">/data-analyze</span>
<span class="pipeline-arrow">→</span>
<span class="pipeline-step">/paper-write</span>
<span class="pipeline-arrow">→</span>
<span class="pipeline-step">/paper-review</span>
</div>
<p class="pipeline-caption">Each command picks up where the last one left off. All context is stored in <code>.neuroflow/</code> — shared project memory that Claude reads at the start of every session.</p>
</div>

---

## Commands at a glance

<div class="command-grid" markdown>

<div class="command-card" markdown>
<span class="command-icon">🚀</span>
### /neuroflow:neuroflow
Main entry point. Scans your project, interviews you, and creates `.neuroflow/` project memory.
[Learn more →](commands/neuroflow.md)
</div>

<div class="command-card" markdown>
<span class="command-icon">💡</span>
### /neuroflow:ideation
Brainstorm research questions, search PubMed and bioRxiv via the scholar agent, and formalize a project proposal.
[Learn more →](commands/ideation.md)
</div>

<div class="command-card" markdown>
<span class="command-icon">📝</span>
### /neuroflow:grant-proposal
Write a full grant application — specific aims, significance, innovation, approach, budget, and timeline.
[Learn more →](commands/grant-proposal.md)
</div>

<div class="command-card" markdown>
<span class="command-icon">🧪</span>
### /neuroflow:experiment
Design a PsychoPy paradigm, define recording parameters, and configure LSL hardware integration.
[Learn more →](commands/experiment.md)
</div>

<div class="command-card" markdown>
<span class="command-icon">📁</span>
### /neuroflow:data
Locate, inventory, validate BIDS structure, and convert raw data formats.
[Learn more →](commands/data.md)
</div>

<div class="command-card" markdown>
<span class="command-icon">🔬</span>
### /neuroflow:data-preprocess
Build and run a preprocessing pipeline — filtering, ICA, epoching, artifact rejection, QC.
[Learn more →](commands/data-preprocess.md)
</div>

<div class="command-card" markdown>
<span class="command-icon">📊</span>
### /neuroflow:data-analyze
ERPs, time-frequency, connectivity, decoding, GLM — with built-in stats auditing.
[Learn more →](commands/data-analyze.md)
</div>

<div class="command-card" markdown>
<span class="command-icon">📄</span>
### /neuroflow:paper-write
Generate a full manuscript draft from your analysis results and figures.
[Learn more →](commands/paper-write.md)
</div>

<div class="command-card" markdown>
<span class="command-icon">🔍</span>
### /neuroflow:paper-review
Pre-submission peer review — scientific logic, methods, statistics, writing quality, and figures.
[Learn more →](commands/paper-review.md)
</div>

</div>

---

## Quick install

```bash
claude plugin marketplace add stanislavjiricek/neuroflow
claude plugin install neuroflow@neuroflow
```

Then open any project folder and run:

```
/neuroflow:neuroflow
```

→ [Full installation guide](installation.md)

---

## How it works

<div class="how-it-works" markdown>

```
.neuroflow/
├── project_config.md    ← active phase, research question, modality, tools
├── flow.md              ← index of all subfolders
├── reasoning/           ← structured per-phase decision logs (JSON)
├── sessions/            ← daily session logs (git-ignored)
├── ideation/            ← research questions, literature reviews, proposals
├── grant-proposal/      ← grant application drafts
├── experiment/          ← paradigm scripts, recording setup
├── tool-build/          ← tool specs and implementation notes
├── tool-validate/       ← validation plans and test results
├── data/                ← data inventory and intake reports
├── data-preprocess/     ← preprocessing configs and QC reports
├── data-analyze/        ← analysis plans and result summaries
├── paper-write/         ← manuscript drafts
├── paper-review/        ← review reports
├── notes/               ← session and meeting notes
└── write-report/        ← generated project reports
```

</div>

Every command reads `.neuroflow/` at the start and writes its output there. This shared memory means Claude always knows what phase you're in, what you've decided, and what's been done — across sessions and across commands.

→ [Learn about project memory](concepts/project-memory.md)

