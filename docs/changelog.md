---
title: Changelog
---

# Changelog

---

## 0.2.15

- **[`/meeting`](commands/meeting.md)** — first-class meeting command with recurring templates, Google Calendar invites, agenda preparation from project context, and action-item-to-task conversion at project/flowie/hive level
- **3-tier task model** — tasks at personal (flowie), project (shared), and hive (team) levels; `--level` flag on `/flowie --tasks`; mandatory ASCII kanban rendering on all displays
- **Collaboration model** — `.neuroflow/flowie/` gitignored from project repos; `.neuroflow/tasks/` git-tracked and shared; collaborator join flow added to `phase-hive`; `collaborators:` list in `project_config.md` for meeting invite resolution

---

## 0.2.14

- **Personal wiki** ([`/flowie --wiki-*`](commands/flowie.md)) — Karpathy-style LLM-maintained knowledge base inside your flowie repo; ingest sources, query accumulated knowledge, lint for orphans/contradictions/stale pages; every page is tagged to flowie projects; closing prompts in `/notes`, `/ideation`, `/data-analyze`, and `/paper`
- **New [`neuroflow:wiki`](skills/wiki/SKILL.md) skill** — page types/frontmatter schema, ingest/query/lint/add/schema workflows, project tagging (always prompted), ideas.md and profile.md sync, fails integration for method pages, sentinel Check 12 for wiki health

---

## 0.2.13

- **`/autoresearch`** — infinite worker-evaluator loop for any research artifact; per-phase criteria auto-loaded; live dashboard at localhost:8765; triggers via `/autoresearch` or any phase command + `autoresearch` keyword
- **Agent cleanup** — removed 16 unused phase agent files; 8 confirmed-spawned agents remain; orchestrator protocol merged into worker-critic skill

---

## 0.2.12

- **Notes → flowie sync** ([`/notes`](commands/notes.md)) — after every notes session, Claude offers to copy the formatted note to `.neuroflow/flowie/notes/` for GitHub sync (default: yes); a local `config.json` stores per-project defaults for type, speaker, and project relation
- **Daily wellbeing tracking** ([`/flowie --assess`](commands/flowie.md)) — opt-in daily self-assessment for anxiety, energy, and happiness on a 1–10 scale (5=neutral); stored in `flowie/wellbeing/`; Claude prompts on any sync operation if today's entry is missing; enabled via `/flowie --init` or `/flowie --assess`

---

## 0.2.11

- **Removed broken `pubmed-mcp-server`** — `pubmed-mcp-server@1.0.0` on npm has an empty `dist/index.js` (TypeScript was never compiled before publishing); removed from `plugin.json`; PubMed search is now handled by `paper-search-mcp-nodejs` (the biorxiv server) which already includes `search_pubmed` and requires no credentials; `PUBMED_EMAIL` is no longer needed and has been removed from the setup wizard, skills, commands, and docs

---

## 0.2.10

- **Global device config** ([`/setup`](commands/setup.md)) — credentials can now be saved once to `~/.neuroflow/integrations.json` (global, all projects) or per-project; per-project takes precedence; Step 0 of the wizard asks which scope to use; per-project config still gitignored as before
- **Windows support** — [`/setup`](commands/setup.md), [`neuroflow:setup`](skills/setup/SKILL.md), and the [e-INFRA reference](skills/setup/references/einfra-cc.md) now cover Windows paths (`%USERPROFILE%`), PowerShell env var syntax, and `where gws` detection throughout
- **Proxy model-name fix** ([`proxy.mjs`](skills/setup/scripts/proxy.mjs)) — proxy now patches `model` field in every response chunk back to the original `claude-*` name, preventing Claude Code's *"unexpected model"* error when using custom LLM providers via Mode B
- **`integrations.json` gitignore in flowie** — [`flowie`](agents/flowie.md) agent now requires `integrations.json` to be gitignored in the flowie sync repo; warns before any push if it is missing; added to plugin `.gitignore` as well

---

## 0.2.9

- **New [`neuroflow:setup`](skills/setup/SKILL.md) skill** — agent-facing knowledge for all neuroflow integrations (PubMed, Miro, Google Workspace, custom LLM providers); mirrors the `/setup` wizard logic so agents can guide credential setup without running the command
- **New e-INFRA CC integration** — [`einfra-cc` reference](skills/setup/references/einfra-cc.md) documents the Czech e-INFRA CZ free LLM API for Claude Code; covers direct mode, proxy mode (with `proxy.mjs` script), available models table, and full terminal workflow; available to Czech academic researchers via Metacentrum membership only
- **`/setup` Step 5** — new optional custom LLM provider wizard; saves non-secret settings to `integrations.json` and optionally to the linked flowie profile for cross-machine sync; e-INFRA is documented as the Czech-specific example
- **Sequential search pipeline** — the `scholar` agent now searches PubMed first, then bioRxiv, then fallbacks one at a time; was previously firing all sources simultaneously; reduces API contention and makes individual source failures easier to diagnose
- **Batch-2 downloads** — paper downloads are now processed in batches of 2 rather than all at once; limits concurrent network requests and improves reliability on slow or rate-limited connections
- **Ideation workflow note** — `/ideation` command and `neuroflow:phase-ideation` skill now document the sequential search approach in their workflow guidance
- **Personal research OS** — `flowie` upgraded from identity layer to full cross-project personal OS: private GitHub repo now holds a Kanban task board (`tasks/`) and a project registry (`projects/`) alongside the existing `profile.md` and `ideas.md`
- **Kanban board** — `/flowie --tasks` renders an ASCII Kanban view; `--tasks --add` runs a mini interview (title → project suggestion from registry → phase, due); `--tasks --move`, `--tasks --done`, `--tasks --archive` for column management; 7 configurable columns in `tasks/config.json`
- **Project registry** — `/flowie --projects` lists all registered projects with ASCII phase timelines; `--projects --add` registers a new project with description and GitHub repo list; stored in `projects/projects.json` + per-project `projects/{name}.md`
- **Phase auto-sync** — whenever `/phase` switches the active phase, if the project has a `flowie_project` binding it silently updates `projects.json` + `{name}.md` in the flowie repo and pushes
- **Auto-sync hook** — any write to `.neuroflow/flowie/**` triggers `git add -A && commit && push` silently (PostToolUse hook)
- **Path rename** — local path changed from `.neuroflow/.flowie/` to `.neuroflow/flowie/`; `flowie_profile:` field in `project_config.md` renamed to `flowie_project:`
- **Sentinel checks** — `sentinel` gains Check 11 (flowie structure validation); `sentinel-dev` gains Check 12 (stale path / field name scan)

---

## 0.2.8

- **Session logging overhaul** — removed the noisy `[tool]` PostToolUse hook; Claude now owns all session logging and writes entries broadly after most actions; `neuroflow-core` logging rules are marked MUST and non-negotiable; `flow.md` purity rule added (pure index table only, no narrative content)
- **mind.js consistency check** — `sentinel-dev` Check 11 audits that every skill, command, and agent has a node in `mind.js`; missing `humanizer` node added; `neuroflow-develop` release workflow now marks the mind.js update step as blocking

---

## 0.2.7

- **Grant-proposal overhaul** — interview-first workflow (10-question conversational interview, objectives saved to `.neuroflow/objectives.md`); inspiration map from previous grants (cross-reference table saved to `.neuroflow/grant-proposal/inspiration-map-[date].md`); optional panel research (WebFetch + WebSearch, panel profiles saved to `.neuroflow/grant-proposal/panels/`); objectives tracked as cornerstones throughout the session; `sequentialthinking` MCP invoked before Innovation and Approach sections
- **Humanizer replaces stop-slop** — new `neuroflow:humanizer` skill: AI word blacklist, structural pattern removal, rhythm checks, register calibration, voice preservation; applied across `/grant-proposal`, `/paper`, `/poster`, `/write-report`; `stop-slop` skill removed
- **Memory quality improvements** — sessions use `##` milestone headers (commands) + `- HH:MM [tool]` audit lines (hook); reasoning mandate raised to 3–5 decisions/session with mandatory trigger list; `objectives.md` added as a root file read at the start of every command; `@modelcontextprotocol/server-sequential-thinking` MCP server added; review output moved from `reviews/` to `.neuroflow/review/`

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
- **`/pipeline`** — define and run a multi-step research pipeline across any sequence of neuroflow phases; interactive by default (pauses for approval between steps), or pass `--executor` for brutal mode; supports resuming from a saved plan; new `neuroflow:phase-pipeline` skill
- **`/search`** — lightweight scoped search using `memory:` (searches `.neuroflow/`) or `project:` (searches the codebase); uses `flow.md` as a fast index; read-only; new `neuroflow:phase-search` skill
- **Slash command availability in all skills** — when any phase skill is invoked directly without its slash command, it now runs the full workflow and mentions the corresponding `/neuroflow:<command>` at the end; behavior defined in `neuroflow:neuroflow-core`
- **15 phase agents** — `ideation`, `grant-proposal`, `experiment`, `tool-build`, `tool-validate`, `data`, `data-preprocess`, `data-analyze`, `paper-write`, `paper-review`, `notes`, `write-report`, `brain-build`, `brain-optimize`, `brain-run` — each agent is a specialist autonomous subprocess scoped to its phase, with a plan-first / confirm-before-executing discipline
- **`neuroflow:neuroflow-core`** — added **Default agent behavior** section: scientific honesty (no sugar-coating), dry English humor, and conservative-by-default mode
- **`/neuroflow` greeting** — on start, neuroflow greets with `Hi, neuroflow here (v0.1.5)` followed by a randomly chosen line
- **Behavioral flags** — three prompt-level personality modes added to `neuroflow:neuroflow-core`: `executor` (aggressive evaluation loop — reruns and self-critiques until high-quality threshold is met), `teacher` (clarify-first mode — asks targeted questions before each step, proceeds incrementally), and `critic` (interrogates assumptions, surfaces hard questions first)

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
