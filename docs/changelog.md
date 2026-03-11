---
title: Changelog
---

# Changelog

---

## 0.1.4

- **`/quiz`** — neuroscience quiz command with three modes: flashcards (saveable A4 printable layout), pub quiz (with neuroscience-themed house rules), and rapid-fire throw questions (default)
- **`/fails`** — log dissatisfaction (core behavior, science quality, or interaction UX) to `.neuroflow/fails/`, with optional one-click GitHub issue reporting; new `neuroflow:phase-fails` skill
- **`/idk`** — personal support companion for when you're burned out, overwhelmed, or need to think out loud; breaks down impossible task lists and lets you decompress mid-research
- **`/interview`** — interview preparation from either side of the table; generates tailored questions grounded in your research context, runs practice Q&A, and optionally evaluates readiness
- **Brain simulation commands** — `/brain-build`, `/brain-optimize`, and `/brain-run` for assembling, fitting, and running computational brain models (NEURON, Brian2, NetPyNE, NEST, tvb-library); three new phase skills: `neuroflow:phase-brain-build`, `neuroflow:phase-brain-optimize`, `neuroflow:phase-brain-run`
- **`neuroflow:phase-quiz`** — phase skill for `/quiz` covering mode behaviour, question quality standards, and mode-specific workflow

---

## 0.1.3

- **`/start` renamed to `/neuroflow`** — the main entry point is now `/neuroflow` (run as `/neuroflow:neuroflow`); all command references and documentation updated
- **Behavioral improvements** — end-of-command lifecycle hardened based on real-session feedback: continuous session logging at each milestone, live `flow.md` updates on every file write, phase transition prompts when outputs outpace the active phase, utility scripts routed to `.neuroflow/{phase}/tools/` instead of the project root, explicit `.claude/CLAUDE.md` creation in the project root, `decisions.md` removed from scaffold (superseded by `reasoning/general.json`), `.neuroflow/` now explicitly restricted to workflow state only

---

## 0.1.2

- **12 phase skills** — `neuroflow:phase-ideation` through `neuroflow:phase-write-report`, each loaded automatically by its corresponding command to orient agent approach, relevant skills, and workflow hints

---

## 0.1.1

- **Full research pipeline** — 15 commands from `/neuroflow` through `/paper-review`, each writing to `.neuroflow/` project memory
- **`neuroflow:neuroflow-core`** — shared lifecycle and `.neuroflow/` folder spec that every command and agent follows; commands now automatically append significant decisions to `.neuroflow/reasoning/{phase}.json`
- **`scholar`**, **`sentinel`**, **`sentinel-dev`** agents
- `sentinel` checks plugin version against `project_config.md` and flags when the plugin has been updated; both sentinels clear their report to "All clear" after fixing issues
- `project_config.md` now tracks `plugin_version` — kept in sync with `plugin.json` by `/neuroflow` and `/sentinel`
- MCP servers declared in `plugin.json`: PubMed, bioRxiv, Miro, Context7

---

## 0.1.0

- Initial release
