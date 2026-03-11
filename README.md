<div align="center">
  <img src="logo.png" alt="neuroflow" width="80%" />
  <h1>neuroflow</h1>
  <p><strong>A Claude Code plugin for agentic neuroscience research.</strong></p>
  <p>
    <a href="#whats-new">What's new</a> ·
    <a href="#why-neuroflow">Why</a> ·
    <a href="#commands">Commands</a> ·
    <a href="#skills">Skills</a> ·
    <a href="#agents">Agents</a> ·
    <a href="#hooks">Hooks</a> ·
    <a href="#project-memory">Project memory</a> ·
    <a href="#installation">Install</a> ·
    <a href="#contributing">Contribute</a>
  </p>
</div>

---

## What's new in 0.1.5

- **[`/export`](commands/export.md)** — new utility command and [`neuroflow:phase-export`](skills/phase-export/SKILL.md) skill: export project memory or the whole project as a zip archive or folder copy; always excludes sessions and credentials; logs each export run to `.neuroflow/export/`

## What's new in 0.1.4

- **[`/quiz`](commands/quiz.md)** — neuroscience quiz command with three modes: flashcards (saveable A4 printable layout), pub quiz (with neuroscience-themed house rules), and rapid-fire throw questions (default)
- **[`/fails`](commands/fails.md)** — new utility command and [`neuroflow:phase-fails`](skills/phase-fails/SKILL.md) skill: log dissatisfaction (core behavior, science quality, or interaction UX) to `.neuroflow/fails/`, with optional one-click GitHub issue reporting
- **[`/idk`](commands/idk.md)** — a small easter egg: a personal support companion for when you're burned out, overwhelmed by deadlines, or just need to think out loud; breaks down impossible task lists and lets you decompress mid-research
- **[`/interview`](commands/interview.md)** — interview preparation from either side of the table; generates tailored questions grounded in your research context, runs practice Q&A, and optionally evaluates your readiness
- **Brain simulation commands** — [`/brain-build`](commands/brain-build.md), [`/brain-optimize`](commands/brain-optimize.md), and [`/brain-run`](commands/brain-run.md) for assembling, fitting, and running computational brain models (NEURON, Brian2, NetPyNE, NEST, tvb-library)

## What's new in 0.1.3

- **`/start` renamed to [`/neuroflow`](commands/neuroflow.md)** — the main entry point is now `/neuroflow:neuroflow`; all commands, docs, and agents updated
- **Behavioral improvements** — lifecycle hardened based on real-session feedback: continuous session logging, live [`flow.md`](skills/neuroflow-core/SKILL.md) updates, phase transition prompts, utility scripts routed to `.neuroflow/{phase}/tools/`, local `.claude/CLAUDE.md` creation enforced in project root

## What's new in 0.1.2

- 12 phase skills — [`neuroflow:phase-ideation`](skills/phase-ideation/SKILL.md) through [`neuroflow:phase-write-report`](skills/phase-write-report/SKILL.md) — each loaded automatically by its corresponding command to orient agent approach, relevant skills, and workflow hints

## What's new in 0.1.1

- Full research pipeline — 15 commands from [`/neuroflow`](commands/neuroflow.md) through [`/paper-review`](commands/paper-review.md), each writing to `.neuroflow/` project memory
- [`neuroflow:neuroflow-core`](skills/neuroflow-core/SKILL.md) — shared lifecycle and `.neuroflow/` folder spec that every command and agent follows; commands now automatically append significant decisions to `.neuroflow/reasoning/{phase}.json`
- [`scholar`](agents/scholar.md), [`sentinel`](agents/sentinel.md), [`sentinel-dev`](agents/sentinel-dev.md) agents
- `sentinel` checks plugin version against `project_config.md` and flags when the plugin has been updated; both sentinels clear their report to "All clear" after fixing issues
- `project_config.md` now tracks `plugin_version` — kept in sync with `plugin.json` by `/neuroflow` and `/sentinel`
- MCP servers declared in `plugin.json`: PubMed, bioRxiv, Miro, Context7

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

Run `/neuroflow:<command>` in any project folder. Start with `/neuroflow:neuroflow`.

### Entry point

| Command | What it does |
|---|---|
| [`/neuroflow`](commands/neuroflow.md) | Main entry point — if `.neuroflow/` exists, shows current phase and status; if not, interviews the user and creates the project memory structure |
| [`/setup`](commands/setup.md) | Interactive credential wizard — configure PubMed email and Miro access token; saves to `.neuroflow/integrations.json` |

### Research pipeline

| Command | What it does |
|---|---|
| [`/ideation`](commands/ideation.md) | Brainstorm a research question, explore literature via scholar, formalize an idea, or produce a project proposal |
| [`/grant-proposal`](commands/grant-proposal.md) | Write a grant application — specific aims, significance, innovation, approach, budget, timeline |
| [`/experiment`](commands/experiment.md) | Paradigm design (PsychoPy), recording setup, instrument and LSL configuration |
| [`/tool-build`](commands/tool-build.md) | Build a lab tool or software pipeline — real-time systems, acquisition, BCI, paradigm code |
| [`/tool-validate`](commands/tool-validate.md) | Create a testing pipeline to verify a tool or paradigm works correctly |
| [`/data`](commands/data.md) | Data intake — locate data, validate BIDS structure, run conversion scripts |
| [`/data-preprocess`](commands/data-preprocess.md) | Run a preprocessing pipeline — filtering, ICA, epoching, artifact rejection, QC |
| [`/data-analyze`](commands/data-analyze.md) | Run an analysis pipeline — ERPs, time-frequency, connectivity, decoding, GLM |
| [`/paper-write`](commands/paper-write.md) | Generate a manuscript draft from results and figures |
| [`/paper-review`](commands/paper-review.md) | Pre-submission peer review — logic, methods, statistics, writing, figures |
| [`/notes`](commands/notes.md) | Live note-taking — capture freeform input, then reformat into a clean structured document |
| [`/write-report`](commands/write-report.md) | Generate a structured report from `.neuroflow/` contents for any phase or the whole project |

### Brain simulation

| Command | What it does |
|---|---|
| [`/brain-build`](commands/brain-build.md) | Assemble a computational brain model — neuron models, network topology, connectivity, simulation framework setup |
| [`/brain-optimize`](commands/brain-optimize.md) | Run a parameter search or fit the model to experimental data |
| [`/brain-run`](commands/brain-run.md) | Run the model as a simulation — configure run parameters, launch, and collect outputs |

### Utility

| Command | What it does |
|---|---|
| [`/interview`](commands/interview.md) | Interview preparation from either side — generate tailored questions grounded in your research context, run practice Q&A, and optionally evaluate readiness |
| [`/phase`](commands/phase.md) | Show current phase and all phases worked on; optionally switch phase |
| [`/sentinel`](commands/sentinel.md) | Full audit of `.neuroflow/` — drift detection, broken references, preregistration vs progress |
| [`/quiz`](commands/quiz.md) | Neuroscience quiz — flashcards, pub quiz, or rapid-fire throw questions; covers any subfield or general neuroscience |
| [`/fails`](commands/fails.md) | Log dissatisfaction — record core behavior, science quality, or UX issues; optionally opens a GitHub issue report |
| [`/export`](commands/export.md) | Export project memory or the whole project — pack as a zip archive or copy to a folder for sharing, archiving, or handoff |
| [`/idk`](commands/idk.md) | Personal support companion — decompress, break down overwhelming tasks, or just chat |

---

## Skills

Skills are invoked by Claude automatically when relevant, or triggered explicitly.

| Skill | What it does |
|---|---|
| [`neuroflow:neuroflow-core`](skills/neuroflow-core/SKILL.md) | Core rules and lifecycle for all commands and agents — `.neuroflow/` folder spec, `flow.md` format, command lifecycle (including auto-write to `reasoning/{phase}.json`), frontmatter standard |
| [`neuroflow:review-neuro`](skills/review-neuro/SKILL.md) | Rigorous pre-submission peer review of a neuroscience manuscript |
| [`neuroflow:neuroflow-develop`](skills/neuroflow-develop/SKILL.md) | Guide for developing and maintaining the neuroflow plugin |
| [`neuroflow:skill-creator`](skills/skill-creator/SKILL.md) | Guide for creating new neuroflow skills |
| [`neuroflow:phase-ideation`](skills/phase-ideation/SKILL.md) | Phase guidance for /ideation — approach, relevant skills, workflow hints |
| [`neuroflow:phase-grant-proposal`](skills/phase-grant-proposal/SKILL.md) | Phase guidance for /grant-proposal |
| [`neuroflow:phase-experiment`](skills/phase-experiment/SKILL.md) | Phase guidance for /experiment |
| [`neuroflow:phase-tool-build`](skills/phase-tool-build/SKILL.md) | Phase guidance for /tool-build |
| [`neuroflow:phase-tool-validate`](skills/phase-tool-validate/SKILL.md) | Phase guidance for /tool-validate |
| [`neuroflow:phase-data`](skills/phase-data/SKILL.md) | Phase guidance for /data |
| [`neuroflow:phase-data-preprocess`](skills/phase-data-preprocess/SKILL.md) | Phase guidance for /data-preprocess |
| [`neuroflow:phase-data-analyze`](skills/phase-data-analyze/SKILL.md) | Phase guidance for /data-analyze |
| [`neuroflow:phase-paper-write`](skills/phase-paper-write/SKILL.md) | Phase guidance for /paper-write |
| [`neuroflow:phase-paper-review`](skills/phase-paper-review/SKILL.md) | Phase guidance for /paper-review — delegates review to neuroflow:review-neuro |
| [`neuroflow:phase-notes`](skills/phase-notes/SKILL.md) | Phase guidance for /notes |
| [`neuroflow:phase-write-report`](skills/phase-write-report/SKILL.md) | Phase guidance for /write-report |
| [`neuroflow:phase-quiz`](skills/phase-quiz/SKILL.md) | Phase guidance for /quiz — mode behaviour, question quality standards, mode-specific workflow |
| [`neuroflow:phase-fails`](skills/phase-fails/SKILL.md) | Phase guidance for /fails — categorisation approach, GitHub reporting, and dissatisfaction capture rules |
| [`neuroflow:phase-export`](skills/phase-export/SKILL.md) | Phase guidance for /export — scope selection, safe exclusions, file naming, and output format guidance |
| [`neuroflow:phase-brain-build`](skills/phase-brain-build/SKILL.md) | Phase guidance for /brain-build — neuron models, connectivity, simulation framework |
| [`neuroflow:phase-brain-optimize`](skills/phase-brain-optimize/SKILL.md) | Phase guidance for /brain-optimize — parameter sweeps, data fitting, optimisation algorithms |
| [`neuroflow:phase-brain-run`](skills/phase-brain-run/SKILL.md) | Phase guidance for /brain-run — run configuration, simulation launch, output sanity checks |

---

## Agents

Agents are autonomous subprocesses launched by commands when deeper, focused work is needed.

| Agent | What it does |
|---|---|
| [`scholar`](agents/scholar.md) | Searches PubMed and bioRxiv simultaneously, returns a clean paper list with ⚠️ preprint and 🔒 paywall markers, supports follow-up synthesis and saving |
| [`sentinel`](agents/sentinel.md) | Project coherence guard — audits `.neuroflow/` for drift, broken references, preregistration deviations, and plugin version sync; clears report after fixes |
| [`sentinel-dev`](agents/sentinel-dev.md) | Plugin development coherence guard — checks folder names vs frontmatter, README tables, version sync, dead references, command frontmatter completeness |

---

## Hooks

Hooks fire automatically on tool use events.

| Hook | Trigger | What it does |
|---|---|---|
| ruff formatter | `PostToolUse` — Edit / Write | Auto-formats any `.py` file written during a session |
| session logger | `PostToolUse` — Write / Edit / Bash | Appends a timestamped entry to today's `.neuroflow/sessions/YYYY-MM-DD.md` (only fires if `.neuroflow/` exists in the working directory) |

> **Pre-session orientation** is handled via `.claude/CLAUDE.md` injection — `/neuroflow` writes a neuroflow block there so Claude always knows the active phase and where to find project context.

---

## Project memory

Every neuroflow command writes its output to `.neuroflow/` at the root of your project repo. This is the shared memory of your project — readable by every command and agent, across sessions.

```
.neuroflow/
├── project_config.md       ← current phase, research question, tools, plugin_version — read by every command
├── flow.md                 ← index of all subfolders
├── sentinel.md             ← sentinel audit report
├── linked_flows.md         ← paths to other .neuroflow/ folders (optional)
├── team.md                 ← project members and roles (optional)
├── timeline.md             ← milestones and deadlines (optional)
├── sessions/               ← one .md per day — add to .gitignore
├── reasoning/              ← structured per-phase decision logs (JSON: statement, source, reasoning)
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
├── paper-write/            ← manuscript drafts
├── paper-review/           ← review reports
├── notes/                  ← structured notes from meetings and talks
└── write-report/           ← project reports
└── fails/                  ← dissatisfaction log: core.md, science.md, ux.md
└── export/                 ← export log: one .md per export run
```

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

Once installed, run `/neuroflow:neuroflow` in any project folder to get started.

---

## MCP server credentials

neuroflow uses four MCP servers that Claude Code launches automatically via `npx`. Two require credentials:

| Server | Package | Credentials needed |
|---|---|---|
| PubMed | `pubmed-mcp-server` | `PUBMED_EMAIL` — any email (required by NCBI for API access) |
| bioRxiv | `paper-search-mcp-nodejs` | none |
| Miro | `@k-jarzyna/mcp-miro` | `MIRO_ACCESS_TOKEN` — personal access token from Miro |
| Context7 | `@upstash/context7-mcp` | none |

### Setup wizard

Run `/neuroflow:setup` (or answer **Y** when prompted during `/neuroflow:neuroflow`) to enter a guided wizard:

1. **PubMed** — enter your email address. Validated for `@` format. Skippable.
2. **Miro** — paste a personal access token from your [Miro developer settings](https://miro.com/app/settings/user-profile/apps). Skippable.

Credentials are saved to **`.neuroflow/integrations.json`** in your project folder. This file is excluded from git (see `.gitignore`) so it is never committed.

### Activating credentials

After running `/setup`, export the env vars in your shell before starting Claude Code:

```bash
export PUBMED_EMAIL="you@example.com"
export MIRO_ACCESS_TOKEN="eyJ..."
```

Add these to your shell profile (`~/.zshrc`, `~/.bashrc`) so they load automatically on every session.

Alternatively, you can set the env vars directly without running the wizard — the plugin will use whichever values are present in the environment.

### What is automatic vs manual

| Step | Automatic | Manual |
|---|---|---|
| MCP server processes started | ✅ Claude Code launches them via `npx` | — |
| PubMed email entry | ✅ Prompted by `/setup` wizard | — |
| Miro token entry | ✅ Prompted by `/setup` wizard | ⚠️ You must create the token in the Miro browser UI first |
| Miro OAuth browser login | ❌ Not implemented (by design — browser OAuth from a terminal subprocess is not feasible without a redirect server) | Use a personal access token instead |
| Env var export | ❌ Not automatic | Run `export …` or add to shell profile |

### Reminder behavior

- If you skip setup and later run `/neuroflow:ideation` → **Explore literature**, the plugin will detect that `PUBMED_EMAIL` is missing and offer to run `/neuroflow:setup` before searching.
- If you mention Miro during ideation and `MIRO_ACCESS_TOKEN` is missing, the same reminder appears.
- You can always re-run `/neuroflow:setup` to add or update credentials.

---

## Contributing

neuroflow is intentionally small right now — and that's the point. It is designed to grow with the community.

If you work in neuroscience and have a workflow that Claude could help with, contributions are very welcome:

- **New skills** — domain knowledge for a modality, analysis method, or writing task
- **New commands** — multi-step pipelines for common research workflows
- **New agents** — autonomous subprocesses for focused tasks

See [`neuroflow:neuroflow-develop`](skills/neuroflow-develop/SKILL.md) for the development guide, or open an issue to discuss an idea before building.

---

## License

MIT © Stanislav Jiricek
