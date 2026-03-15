---
title: neuroflow
hide:
  - navigation
  - toc
---

<div class="sa-bar">
  <span class="sa-bar-label">🧠 self-assessment <span class="sa-bar-version">v0.2.4</span></span>
  <div class="sa-items">
    <span class="sa-item" data-tip="Prediction error detected?">
      <span class="sa-q-short">Pred. error</span><span class="probe-badge probe-yes">YES</span>
    </span>
    <span class="sa-item" data-tip="Internal model updated?">
      <span class="sa-q-short">Internal model</span><span class="probe-badge probe-no">NO</span>
    </span>
    <span class="sa-item" data-tip="Uncertainty estimated?">
      <span class="sa-q-short">Uncertainty</span><span class="probe-badge probe-partial">PARTIAL</span>
    </span>
    <span class="sa-item" data-tip="Decisions monitored?">
      <span class="sa-q-short">Decisions</span><span class="probe-badge probe-no">NO</span>
    </span>
    <span class="sa-item" data-tip="Self-model present?">
      <span class="sa-q-short">Self-model</span><span class="probe-badge probe-partial">PARTIAL</span>
    </span>
    <span class="sa-item" data-tip="Global integration active?">
      <span class="sa-q-short">Global integ.</span><span class="probe-badge probe-partial">PARTIAL</span>
    </span>
    <span class="sa-item" data-tip="Subjective experience present?">
      <span class="sa-q-short">Subj. experience</span><span class="probe-badge probe-unknown">UNKNOWN</span>
    </span>
  </div>
</div>

<div class="hero" markdown>
<div id="nf-quotes"></div>
<div class="hero-inner" markdown>
<div class="hero-text" markdown>

<p class="hero-heading" markdown>![neuroflow](assets/logo-brain.svg){ .hero-brand-logo } **hi, I am neuroflow**</p>

— the agentic operating system for neuroscience research.
From hypothesis to manuscript, every phase orchestrated by AI.

<div class="hero-buttons" markdown>
[Browse commands :octicons-terminal-24:](commands/index.md){ .md-button }
[Get started :octicons-arrow-right-24:](quickstart.md){ .md-button .md-button--primary }
[🌌 Neuroflow Mind](mind.md){ .md-button .md-button--mind }
</div>

<p class="hero-community">🌱 <em>Did I fail you? :') I'm in pre-release and open to the community</em> — <a href="https://github.com/stanislavjiricek/neuroflow/issues/new">🐛 open an issue</a> or <a href="https://github.com/stanislavjiricek/neuroflow/pulls">🔀 improve me with a PR</a></p>

</div>
<div class="hero-why">
<p class="hero-why-title">✨ why neuroflow?</p>
<div class="why-grid">
<div class="why-card">
<span class="why-icon">🔗</span>
<span class="why-name">End-to-end pipeline</span>
<span class="why-desc">One tool covers the entire research lifecycle — ideation, experiment design, data, analysis, and writing — with no context lost between steps.</span>
</div>
<div class="why-card">
<span class="why-icon">🧠</span>
<span class="why-name">Neuroscience-aware AI</span>
<span class="why-desc">Domain-specific skills for EEG, iEEG, fMRI, eye tracking, ECG, and other physiological signals, from cognitive to clinical research.</span>
</div>
<div class="why-card">
<span class="why-icon">💾</span>
<span class="why-name">Persistent memory</span>
<span class="why-desc">All reasoning logs, session notes, and context live in <code>.neuroflow/</code> — Claude reads it at the start of every session so you never repeat yourself.</span>
</div>
<div class="why-card">
<span class="why-icon">📊</span>
<span class="why-name">Neuroscience analysis</span>
<span class="why-desc">ERPs, time-frequency, connectivity, decoding, and GLM — with pre-registration compliance checks and rigorous reporting.</span>
</div>
</div>
</div>
</div>
</div>

---

<details class="who-card">
<summary class="who-summary">
  <span class="who-icon">🎯</span>
  <span class="who-title">Who is this for?</span>
  <span class="who-tagline">Neuroscientists working with EEG, iEEG, fMRI, eye tracking, ECG…</span>
</summary>
<div class="who-body">
Neuroscientists working with EEG, iEEG, fMRI, eye tracking, ECG, or other physiological signals — from cognitive and clinical to preclinical research.
</div>
</details>

---

## Research pipelines

<p class="rp-intro">neuroflow adapts to your research — click a pipeline to see how the commands connect.</p>

<div class="rp-grid">

<details class="rp-card rp-card--full">
<summary class="rp-summary">
  <span class="rp-summary-left">
    <span class="rp-icon">🔬</span>
    <span class="rp-title">Full research cycle</span>
  </span>
  <span class="rp-badge rp-badge--full">Full cycle</span>
</summary>
<div class="rp-body">
  <p class="rp-desc">From first hypothesis to peer-reviewed manuscript — the complete end-to-end journey. Ideate, run an experiment, collect and preprocess data, analyze, write, and get it reviewed.</p>
  <div class="rp-pipeline">
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
    <span class="pipeline-step">/paper</span>
    <span class="pipeline-arrow">→</span>
    <span class="pipeline-step">/review</span>
  </div>
  <p class="rp-caption">All context is stored in <code>.neuroflow/</code> — shared memory that carries every decision forward.</p>
</div>
</details>

<details class="rp-card rp-card--analysis">
<summary class="rp-summary">
  <span class="rp-summary-left">
    <span class="rp-icon">📊</span>
    <span class="rp-title">Data analysis study</span>
  </span>
  <span class="rp-badge rp-badge--analysis">Analysis</span>
</summary>
<div class="rp-body">
  <p class="rp-desc">You already have data collected. Inventory it, run preprocessing, extract results, and write them up — without touching the experiment design phase.</p>
  <div class="rp-pipeline">
    <span class="pipeline-step">/data</span>
    <span class="pipeline-arrow">→</span>
    <span class="pipeline-step">/data-preprocess</span>
    <span class="pipeline-arrow">→</span>
    <span class="pipeline-step">/data-analyze</span>
    <span class="pipeline-arrow">→</span>
    <span class="pipeline-step">/paper</span>
  </div>
  <p class="rp-caption">ERPs, time-frequency, connectivity, decoding, GLM — automatically reported with pre-registration compliance checks.</p>
</div>
</details>

<details class="rp-card rp-card--tool">
<summary class="rp-summary">
  <span class="rp-summary-left">
    <span class="rp-icon">🔧</span>
    <span class="rp-title">Research tool build</span>
  </span>
  <span class="rp-badge rp-badge--tool">Engineering</span>
</summary>
<div class="rp-body">
  <p class="rp-desc">Building a new analysis algorithm, preprocessing library, or experiment software? Ideate the design, scaffold the implementation, validate it — and optionally write it up as a methods paper.</p>
  <div class="rp-pipeline">
    <span class="pipeline-step">/ideation</span>
    <span class="pipeline-arrow">→</span>
    <span class="pipeline-step">/tool-build</span>
    <span class="pipeline-arrow">→</span>
    <span class="pipeline-step">/tool-validate</span>
    <span class="pipeline-arrow">→</span>
    <span class="pipeline-step rp-step--optional">/paper</span>
  </div>
  <p class="rp-caption">The paper step is optional — publish a methods article or keep the tool as internal infrastructure.</p>
</div>
</details>

<details class="rp-card rp-card--model">
<summary class="rp-summary">
  <span class="rp-summary-left">
    <span class="rp-icon">🧮</span>
    <span class="rp-title">Computational modelling</span>
  </span>
  <span class="rp-badge rp-badge--model">Modelling</span>
</summary>
<div class="rp-body">
  <p class="rp-desc">Build and run a brain simulation model. Ideate the architecture, construct the model, then optimize and run it — with empirical data analysis running in parallel and feeding into the optimization step.</p>
  <div class="rp-pipeline rp-pipeline--parallel">
    <div class="pipeline-track">
      <span class="pipeline-step">/ideation</span>
      <span class="pipeline-arrow">→</span>
      <span class="pipeline-step">/brain-build</span>
      <span class="pipeline-arrow">→</span>
      <span class="pipeline-step">/brain-optimize</span>
      <span class="pipeline-arrow">→</span>
      <span class="pipeline-step">/brain-run</span>
      <span class="pipeline-arrow">→</span>
      <span class="pipeline-step rp-step--optional">/paper</span>
    </div>
    <div class="pipeline-track pipeline-track--parallel">
      <span class="pipeline-parallel-label">parallel ↗</span>
      <span class="pipeline-step">/data</span>
      <span class="pipeline-arrow">→</span>
      <span class="pipeline-step">/data-preprocess</span>
      <span class="pipeline-arrow">→</span>
      <span class="pipeline-step">/data-analyze</span>
      <span class="pipeline-arrow">→</span>
      <span class="pipeline-parallel-merge">merges before optimize</span>
    </div>
  </div>
  <p class="rp-caption">Data analysis runs in parallel with model construction and merges before optimization — the paper step is optional.</p>
</div>
</details>

<details class="rp-card rp-card--ideation">
<summary class="rp-summary">
  <span class="rp-summary-left">
    <span class="rp-icon">📚</span>
    <span class="rp-title">Literature review & ideation</span>
  </span>
  <span class="rp-badge rp-badge--ideation">Ideation</span>
</summary>
<div class="rp-body">
  <p class="rp-desc">Start with a broad question, search PubMed and bioRxiv, synthesise the field, and sharpen a novel hypothesis — then write it up as a review article and optionally convert it into a grant proposal.</p>
  <div class="rp-pipeline">
    <span class="pipeline-step">/ideation</span>
    <span class="pipeline-arrow">→</span>
    <span class="pipeline-step">/paper</span>
    <span class="pipeline-arrow">→</span>
    <span class="pipeline-step rp-step--optional">/grant-proposal</span>
  </div>
  <p class="rp-caption">The scholar agent searches PubMed, bioRxiv, and Semantic Scholar in real time to ground every idea in the current literature.</p>
</div>
</details>

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
├── paper/               ← manuscript drafts and critic logs
├── notes/               ← session and meeting notes
└── write-report/        ← generated project reports
```

</div>

Every command reads `.neuroflow/` at the start and writes its output there. This shared memory means Claude always knows what phase you're in, what you've decided, and what's been done — across sessions and across commands.

→ [Learn about project memory](concepts/project-memory.md)
