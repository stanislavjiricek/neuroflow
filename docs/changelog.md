---
title: Changelog
---

# Changelog

---

## 0.2.6

- **Scholar agent: download reporting fixes** — `.pdf`/`.txt` now correctly marked `⏭️ already downloaded`; `.md`-only stubs re-attempt download unless `reason: unavailable`; `✅ downloaded` gated on confirmed `.pdf`/`.txt` write; summary counter labelled `✅ [n] downloaded (PDF/text)` + new `⏭️ [n] unavailable (metadata cached)` bucket
- **Scholar agent: search coverage fixes** — Semantic Scholar 429 rate-limit → 3 s wait + retry → falls back to CrossRef/arXiv with inline warning; PubMed query-overlap detection auto-generates 2–3 diversified queries when < 15 unique results or > 80% overlap; arXiv keyword fallback added when bioRxiv returns 0 results; mandatory per-source coverage summary table printed before results; any ⚠️/❌ row also surfaces as an inline warning block

---

## 0.2.5

- **`/poster`** — generate a LaTeX conference poster from project memory; five templates (A0/A1 portrait, A0 landscape, 90×120 cm, 48×36 in); QR code via `qrcode` package; iterative `poster-critic` review loop (up to 3 cycles) before `.tex` is saved
- **New `poster-critic` agent** — five-area poster auditor (content, layout, scientific communication, QR code, LaTeX correctness); returns `[STATUS: APPROVED]`/`[STATUS: REJECTED]` with specific fixes; never rewrites content
- **New `neuroflow:phase-poster` skill** — full LaTeX template catalogue, template selection guide, content extraction from `.neuroflow/`, QR code blocks, compilation instructions

---

## 0.2.4

- **Sentinel Check 3b** — sentinel now validates that `.claude-plugin/marketplace.json` version matches `plugin.json`; marketplace version was silently stuck at `0.1.0`
- **Hardened release checklist** — both dev agents now require `docs/changelog.md` entry, one-liner review, and `marketplace.json` bump on every release; `neuroflow-develop/SKILL.md` synced to match `neuroflow-developer.md` (was missing `mkdocs.yml` and sentinel-dev steps)
- **Internal consistency fixes** — dead `neuroflow:scholar` ref in `phase-paper` fixed; `/hive` docs page created; `neuroflow-developer.md` and `orchestrator` synced to full repo structure (22 phases, all 4 workflows)

---

## 0.1.6

- **Version bump** — website and header badge updated to v0.1.6
- **Mind map back button** — the back-to-docs link on the mind map page is now a full-width prominent button, easy to spot and reach
- **Fails-folder awareness in core** — `neuroflow:neuroflow-core` now instructs every command to read `.neuroflow/fails/` at start (if it exists), so past logged dissatisfaction is always in context
- **Removed AI-slop feature claims** — the "Built-in stats auditing" feature card removed from the homepage; the `/data-analyze` command page and skill are unchanged

---

## 0.1.5

- **`/git`** — context-aware git utility with smart shorthand aliases (`p`, `pl`, `ps`, `a`, `c`, `ac`, `acp`, `b`, `pr`); reads repo state to decide push vs pull, suggests commit messages, and can open PRs via `gh` CLI; new `neuroflow:phase-git` skill
- **`/export`** — export project memory or the whole project as a zip archive or folder copy; always excludes sessions and credentials; logs each export run to `.neuroflow/export/`; new `neuroflow:phase-export` skill
- **`/preregistration`** — draft OSF, AsPredicted, or registered-report pre-registrations; review for completeness; log deviations; link registered reports; new `neuroflow:phase-preregistration` skill
- **`/finance`** — budget planning, expense logging, funder-facing financial reports, and grant compliance checks; new `neuroflow:phase-finance` skill
- **`/pipeline`** — define and run a multi-step research pipeline across any sequence of neuroflow phases; interactive by default (pauses for approval between steps), or pass `--nomistake` for brutal mode; supports resuming from a saved plan; new `neuroflow:phase-pipeline` skill
- **`/search`** — lightweight scoped search using `memory:` (searches `.neuroflow/`) or `project:` (searches the codebase); uses `flow.md` as a fast index; read-only; new `neuroflow:phase-search` skill
- **Slash command availability in all skills** — when any phase skill is invoked directly without its slash command, it now runs the full workflow and mentions the corresponding `/neuroflow:<command>` at the end; behavior defined in `neuroflow:neuroflow-core`
- **15 phase agents** — `ideation`, `grant-proposal`, `experiment`, `tool-build`, `tool-validate`, `data`, `data-preprocess`, `data-analyze`, `paper-write`, `paper-review`, `notes`, `write-report`, `brain-build`, `brain-optimize`, `brain-run` — each agent is a specialist autonomous subprocess scoped to its phase, with a plan-first / confirm-before-executing discipline
- **`neuroflow:neuroflow-core`** — added **Default agent behavior** section: scientific honesty (no sugar-coating), dry English humor, and conservative-by-default mode
- **`/neuroflow` greeting** — on start, neuroflow greets with `Hi, neuroflow here (v0.1.5)` followed by a randomly chosen line
- **Behavioral flags** — two prompt-level flags added to `neuroflow:neuroflow-core`: `nomistake` (aggressive evaluation loop — reruns and self-critiques until high-quality threshold is met) and `snowflake` (clarify-first mode — asks targeted questions before each step, proceeds incrementally)

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
