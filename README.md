<div align="center">
  <img src="logo-full.svg" alt="neuroflow" width="80%" />
  <h1>neuroflow</h1>
  <p><strong>A complete research system for neuroscience teams.</strong></p>
  <p><a href="https://stanislavjiricek.github.io/neuroflow/">Website and documentation</a></p>
  <p>
    <a href="#whats-new">What's new</a> ·
    <a href="#why-neuroflow">Why</a> ·
    <a href="#commands">Commands</a> ·
    <a href="#skills">Skills</a> ·
    <a href="#agents">Agents</a> ·
    <a href="#hooks">Hooks</a> ·
    <a href="#the-neuroflow-mod">Mod</a> ·
    <a href="#project-memory">Project memory</a> ·
    <a href="#installation">Install</a> ·
    <a href="#contributing">Contribute</a>
  </p>
</div>

---

<a id="whats-new"></a>
## What's new in 0.2.23

- **Your tasks from every level** — with the mod, the [dashboard](commands/dashboard.md)'s tasks tab and the [`/neuroflow:tasks`](commands/tasks.md) pane show the project board, your flowie and every hive you joined (`v` switches the level); this project's tasks come first, and a move goes into the prompt as one `/tasks` command (new `--hive {org-repo}`). A bug that made the mod see no folders at all (so no task board, phases or loops) is fixed
- **`/neuroflow:migrate` no longer skips a level with unsynced files** — it lists them and offers to sync them first (flowie) or carries them along untouched (hive); [`/doctor`](commands/doctor.md) reports uncommitted flowie changes. The mod's wellbeing check-in and idea capture now sync your flowie before your next neuroflow command and log every attempt
- **Docs and notice fixes** — the docs search stays in view on every page, phone layouts fit, old skill addresses redirect; the update notice is said verbatim as one sentence, and the band offers `m` (migrate) whenever it shows it

## What's new in 0.2.22

- **A new site and one command after every update** — the [landing page](https://stanislavjiricek.github.io/neuroflow/) turns the research cycle as you scroll, and the [documentation](docs/overview.md) has no top bar: one index with search holds every phase, command, agent and skill, a [Memory & team](docs/concepts/memory.md) section explains the three levels (you, the project, the team), and [the mod page](docs/concepts/mods.md) shows the harness as it looks. After an update, the first neuroflow command names [`/neuroflow:migrate`](commands/migrate.md), which brings the project, your flowie and the team hive up to date ([upgrading](docs/upgrading.md)). Three skills that shared a command's name are renamed: `autoresearch-protocol`, `wiki-protocol`, `setup-guide`
- **The neuroflow mod** — an optional [Claude Code hooks module](docs/concepts/mods.md): dashboard and task-board panes drawn in code, freezing the preregistration on a key press, a quiet band and status line, an instant [`/doctor`](commands/doctor.md), capture without model turns, checks triggered by what the model did, an autoresearch driver, a decision drafter and guards for the rules the skills state. Everything works without it; a [design record](docs/concepts/design-record.md) says what became of all 270 ideas behind it
- **Research integrity and machine-readable memory** — an [autoresearch](skills/autoresearch-protocol/SKILL.md) integrity gate and caps, preregistration freezing with hashes, an ethics gate and AI data route, AI-use disclosure, citation, statistics and hidden-text checks; config, status and reasoning-log contracts; sharing tiers with confirmed egress; 40+ tested Python checks; Claude Code only

## What's new in 0.2.21

- **Consistency overhaul from a full plugin review** — both [hooks](hooks/hooks.json) rewritten against the real stdin-JSON contract (they were silently dead), one canonical credentials scheme (`~/.neuroflow/integrations.json` global + per-project override; flowie carries non-secrets only), one canonical [phase taxonomy](skills/neuroflow-core/SKILL.md) replacing four divergent copies, eight-area review everywhere, `/setup` renumbered, dead references purged, [custom gateway setup](skills/setup-guide/references/custom-gateway.md) rewritten for native Anthropic-compatible gateways (no proxy)
- **Lifecycle enforcement** — [`neuroflow-core`](skills/neuroflow-core/SKILL.md) gains the missing-`.neuroflow/` rule and one canonical session-log format; new PR-time CI ([`validate.yml`](.github/workflows/validate.yml) + [`validate_pr.py`](scripts/automation/validate_pr.py)); five previously prose-only sentinel-dev checks now run in CI; audit agents get `tools:` allowlists
- **Science-PM surface** — new [`/ethics`](commands/ethics.md) (protocol, versioned consent, approval expiry) and [`/tasks`](commands/tasks.md) (canonical 3-tier Kanban owner); [`/paper`](commands/paper.md) grows `--submit`, `--revise` (strict minimal-change rebuttal discipline), and `--abstract`; [`/output --archive`](commands/output.md) (OpenNeuro/OSF/Zenodo + DOI); DMP drafting in [`/grant-proposal`](commands/grant-proposal.md); `objectives.md`/`timeline.md` ownership; reproducibility manifests in the data phases; wikis are valid Obsidian vaults; optional Zotero-first literature search in [`/ideation`](commands/ideation.md)

## What's new in 0.2.20

- **autoresearch rebuilt around a per-loop wiki** — [`neuroflow:autoresearch`](skills/autoresearch-protocol/SKILL.md) is now a single managing agent (no worker/evaluator fan-out) whose brain is a scoped `wiki/`: it reads the wiki before every move and records every attempt — wins *and* failures — after. That's what lets an infinite single-agent loop compound instead of going in circles.
- **Loop lives next to the artifact** — folder named `{name}_autoresearch/` beside the tracked files (overridable), with a pointer registry in `.neuroflow/{phase}/autoresearch-loops.md`. Multiple loops per phase now work.
- **Configurable depth + human steering** — agent-decided branching, literature search when stuck, self vs fresh-eval, and a `report.md` with a non-blocking Q&A channel (answer in-session or via `answers.md`); the dashboard renders the report and open questions next to the trend charts.

## What's new in 0.2.19

- **New [`neuroflow:bids`](skills/bids/SKILL.md) skill** — comprehensive Brain Imaging Data Structure reference: full folder hierarchy for all modalities (MRI/EEG/MEG/iEEG/PET/DWI/NIRS/motion), entity ordering rules, JSON sidecar fields, derivatives structure, and tool guides for bids-validator, pybids, MNE-BIDS, fMRIPrep, and dcm2niix/HeuDiConv conversion pipelines
- **BIDS integrated into data phases** — [`phase-data`](skills/phase-data/SKILL.md), [`phase-data-preprocess`](skills/phase-data-preprocess/SKILL.md), and [`phase-data-analyze`](skills/phase-data-analyze/SKILL.md) now reference the BIDS skill; invoked automatically when structure, validation, or loading is relevant
- **`mind.js` updated** — `sk-bids` node added to the pipeline cluster, linked to `c-data`

## What's new in 0.2.18

- **Global `~/.neuroflow/` structure** — flowie and hive caches move from per-project `.neuroflow/flowie/` to a single global `~/.neuroflow/flowie/` (one clone per user); hive caches at `~/.neuroflow/hives/{org-repo}/`; `integrations.json` lives in flowie globally; `team.md` and `linked_flows.md` removed from project structure; collaborators now in `project_config.md`
- **Global auto-sync on session start** — [`neuroflow-core`](skills/neuroflow-core/SKILL.md) pulls `~/.neuroflow/flowie/` and all hive caches at the start of every command session; always start with fresh knowledge
- **Cross-wiki ambient search** — ambient pre-query now searches all initialized wikis in parallel (`~/.neuroflow/flowie/wiki/`, `~/.neuroflow/hives/*/wiki/`, `.neuroflow/wiki/`); answers cite source wiki by level
- **Wiki crystallization hook** — [`neuroflow-core`](skills/neuroflow-core/SKILL.md) detects decisions/hypotheses/insights at end of every command and offers wiki ingest with smart level routing; per-command wiki nudges removed from `/data-analyze`, `/paper`, `/notes`
- **Docs + consistency fixes** — missing docs mirrors created, dead agent rows removed, `mind.js` updated, version badge fixed

## What's new in 0.2.16

- **`flowie_profiles` list** — replaces the redundant `flowie_project` + `hive_member` scalar fields in `project_config.md` with a single extensible `flowie_profiles:` list; each entry has `handle` and `repo`; first entry = project owner, additional entries added when collaborators run `/flowie --link`; backward-compatible (one entry = old behavior)
- **Global user identity config** ([`/setup`](commands/setup.md)) — new Step 6 saves your GitHub username to `~/.neuroflow/user.yaml`; `/neuroflow` Step 1b reads it to pre-fill the flowie handle so you never have to enter it again on a new project
- **Sentinel migration guard** — sentinel now flags legacy `flowie_project:` and `hive_member:` scalar fields and suggests running `/neuroflow` to migrate

## What's new in 0.2.15

- **[`/meeting`](commands/meeting.md)** — first-class meeting command: schedule meetings from recurring templates, prepare agendas with active task context, send Google Calendar invites, and auto-create tasks from action items at project/flowie/hive level
- **3-tier task model** ([`/flowie --tasks --level`](commands/flowie.md)) — tasks now exist at three levels: personal flowie (private), project (git-tracked, shared with collaborators), and hive (team-wide); kanban rendering mandatory on all displays
- **`.neuroflow/flowie/` gitignored** — flowie is personal and excluded from shared project repos; each collaborator keeps their own private flowie; collaborator join flow documented in [`phase-hive`](skills/phase-hive/SKILL.md)

## What's new in 0.2.14

- **Personal wiki** ([`/flowie --wiki-*`](commands/flowie.md)) — Karpathy-style LLM-maintained knowledge base inside your flowie repo; ingest sources, query your accumulated knowledge, lint for orphan/stale pages, and build a compounding synthesis; every page is tagged to flowie projects; integrates with `/notes`, `/ideation`, `/data-analyze`, and `/paper` via closing prompts
- **New [`neuroflow:wiki`](skills/wiki-protocol/SKILL.md) skill** — full wiki behavior: page types and frontmatter schema, ingest/query/lint/add/schema workflows, project tagging (always prompted), ideas.md sync, profile.md evolution, fails integration for method pages, and sentinel health checks

## What's new in 0.2.13

- **[`/autoresearch`](commands/autoresearch.md)** — infinite improvement loop for any research artifact: point it at any file(s), and a single managing agent runs indefinitely (one focused change per iteration, keep or revert, never stops until interrupted), using a per-loop wiki as its memory; the loop folder lives next to the artifact; optional branching, literature search, and a human `report.md` with a non-blocking Q&A channel; live dashboard at `localhost:8765` rendering the report and trend charts; triggers via `/autoresearch` or any phase command with the word `autoresearch` in the prompt
- **Agent cleanup** — removed 16 unused phase agent files that were never spawned by commands; commands follow phase skills directly; the 8 agents that are actually spawned (paper-writer, paper-critic, poster-critic, literature-review, scholar, sentinel, sentinel-dev, flowie) remain unchanged

## What's new in 0.2.12

- **Notes → flowie sync** ([`/notes`](commands/notes.md)) — after every notes session, Claude offers to copy the formatted note to `.neuroflow/flowie/notes/` for GitHub sync (default: yes); a local `config.json` stores per-project defaults for type, speaker, and project relation
- **Daily wellbeing tracking** ([`/flowie --assess`](commands/flowie.md)) — opt-in daily self-assessment for anxiety, energy, and happiness on a 1–10 scale (5=neutral); stored in `flowie/wellbeing/`; Claude prompts on any sync operation if today's entry is missing; enabled via `/flowie --init` or `/flowie --assess`

## What's new in 0.2.11

- **Removed broken `pubmed-mcp-server`** — replaced by `paper-search-mcp-nodejs` (the biorxiv server), which already includes `search_pubmed` and requires no credentials; `PUBMED_EMAIL` is no longer needed

## What's new in 0.2.10

- **Global device config** ([`/setup`](commands/setup.md)) — credentials can now be saved to `~/.neuroflow/integrations.json` (global, shared by all projects on the machine) instead of per-project; per-project still takes precedence and overrides global; Step 0 of the wizard asks which scope to use
- **Windows support in setup** — [`/setup`](commands/setup.md), [`neuroflow:setup`](skills/setup-guide/SKILL.md), and the [custom gateway guide](skills/setup-guide/references/custom-gateway.md) now include Windows-specific paths and PowerShell env var syntax throughout
- **Proxy model-name fix** ([`proxy.mjs`](skills/setup-guide/scripts/gateway/proxy.mjs)) — the proxy now restores the original `claude-*` model name in every response chunk, preventing Claude Code's *"unexpected model"* error when using custom LLM providers; [`flowie`](agents/flowie.md) now enforces that `integrations.json` is gitignored in the flowie sync repo

## What's new in 0.2.8

- **Session logging overhaul** — removed the noisy `[tool]` PostToolUse hook; Claude now owns all session logging and writes entries broadly (most actions, not just milestones); `neuroflow-core` logging rules are now marked MUST and non-negotiable
- **flow.md purity rule** — `flow.md` is now explicitly a pure index table; narrative content, figure maps, and cross-references must go in dedicated `.md` files in the phase subfolder
- **mind.js consistency check** — `sentinel-dev` Check 11 audits that every skill, command, and agent has a node in `docs/javascripts/mind.js`; missing `humanizer` node added; `neuroflow-develop` release workflow now flags this as a blocking step
- **[`scholar`](agents/scholar.md) sequential search + batch downloads** — searches now run PubMed → bioRxiv → fallbacks one at a time (was simultaneous); paper downloads processed in batches of 2 to reduce concurrency pressure and make failures easier to diagnose

## What's new in 0.2.6

- **Scholar agent: download reporting fixes** — `.pdf`/`.txt` files now correctly marked `⏭️ already downloaded`; `.md`-only stubs re-attempt download unless `reason: unavailable`; `✅ downloaded` is gated on a confirmed `.pdf` or `.txt` write; download summary counter now labelled `✅ [n] downloaded (PDF/text)` with a new `⏭️ [n] unavailable (metadata cached)` bucket
- **Scholar agent: search coverage fixes** — Semantic Scholar 429 rate-limit triggers a 3 s wait + retry then falls back to CrossRef/arXiv with a visible warning; PubMed query-overlap detection auto-generates 2–3 diversified queries when < 15 unique results or > 80% overlap; arXiv keyword fallback added when bioRxiv returns 0 results; mandatory coverage summary table printed before results, with any ⚠️/❌ row also surfaced as an inline warning block

## What's new in 0.2.5

- **[`/poster`](commands/poster.md)** — generate a LaTeX conference poster from project memory; five templates (A0/A1 portrait, A0 landscape, 90×120 cm, 48×36 in); QR code support via the `qrcode` package; iterative `poster-critic` review loop (up to 3 cycles) before the `.tex` file is saved
- **New [`poster-critic`](agents/poster-critic.md) agent** — audits every poster draft across five areas (content accuracy, visual balance, scientific communication, QR code, LaTeX correctness); returns `[STATUS: APPROVED]` or `[STATUS: REJECTED]` with specific, actionable feedback; never rewrites content
- **New [`neuroflow:phase-poster`](skills/phase-poster/SKILL.md) skill** — full LaTeX template catalogue with embedded QR code blocks, template selection guide, content extraction logic, and compilation instructions

## What's new in 0.2.4

- **Sentinel Check 3b** — sentinel now validates that `.claude-plugin/marketplace.json` version matches `plugin.json`; the marketplace version was silently stuck at `0.1.0` with no existing check to catch it
- **Hardened release checklist** — both the former `neuroflow-developer` agent and [`neuroflow-develop/SKILL.md`](skills/neuroflow-develop/SKILL.md) now require `docs/changelog.md` entry, one-liner review, and `marketplace.json` bump on every release; `SKILL.md` synced to match `neuroflow-developer.md` (was missing `mkdocs.yml` and sentinel-dev steps)
- **Internal consistency fixes** — dead `neuroflow:scholar` skill ref in [`phase-paper`](skills/phase-paper/SKILL.md) corrected; [`/hive` docs page](docs/commands/hive.md) created; the former `neuroflow-developer` agent and `orchestrator` synced to full repo structure (22 phases, all 4 workflows, `scripts/automation/`)

## What's new in 0.2.3

- **PDF download resume and retry logic** — the `scholar` agent now checks which papers are already present in `.neuroflow/ideation/papers/` before downloading; interrupted runs are safely retried without duplicating work
- **Four-source fallback chain** — downloads now try Unpaywall → PubMed Central → bioRxiv direct → journal OA page in sequence; each source is attempted before moving to the next
- **Per-paper retry** — if all four sources fail, the agent waits 2 seconds and retries the full chain once more before marking a paper as unavailable
- **`⚠️ failed` vs `❌ unavailable` distinction** — transient network failures are now reported separately from confirmed no-OA-copy papers, with a named list of papers to retry and instructions to re-run the agent to resume
- **Removed `/paper-write` and `/paper-review`** — superseded by [`/paper`](commands/paper.md), which covers the full write→critique loop; nothing is lost
- **New [`/review`](commands/review.md) command** — for when YOU are the reviewer reading a colleague's paper; produces a structured referee report calibrated to the target journal by delegating to `neuroflow:review-neuro`
- **New `review` agent and [`neuroflow:phase-review`](skills/phase-review/SKILL.md) skill** — autonomous peer reviewer agent and phase orientation skill for the referee workflow

## What's new in 0.2.2

- **Unified [`/paper`](commands/paper.md) command** — combines paper-write and paper-review into a single command and phase; every section draft goes through a brutal `paper-writer` → `paper-critic` loop (up to 3 iterations per section) before anything is saved; nothing reaches disk without critic approval or explicit user acceptance
- **New [`paper-writer`](agents/paper-writer.md) and [`paper-critic`](agents/paper-critic.md) agents** — the writer drafts section-by-section from upstream project memory; the critic applies the full six-area `neuroflow:review-neuro` methodology to every draft with zero tolerance for overclaims, statistical errors, or underreported methods
- **New [`neuroflow:phase-paper`](skills/phase-paper/SKILL.md) skill** — unified phase guidance covering journal recommendation, the write→critique loop protocol, critic standards, and output paths for the paper phase

## What's new in 0.2.1

- **ASCII welcome logo in [`/neuroflow`](commands/neuroflow.md)** — the main entry command now greets with a full ASCII logo for "neuroflow", the current version number, and the tagline *agentic neuroscience research, from hypothesis to publication*, followed by one of the three witty one-liners

## What's new in 0.2.0

- **Auto-issue consent gate** — `auto-issue` now checks `auto_issue_reporting:` in `project_config.md` before filing any issue; issues are only sent if the user explicitly opted in during project setup; missing or `no` value silently suppresses all automatic filing
- **Consent question in [`/neuroflow`](commands/neuroflow.md)** — project setup now asks whether the user allows anonymous issue reporting to the developers and saves the answer as `auto_issue_reporting: yes/no` in `project_config.md`
- **Cognitive probe embedded on home page** — simple static self-assessment block replaces the separate probe page

## What's new in 0.1.9

- **Worker-critic agentic loop** — new `orchestrator` and `critic` agents coordinate up to 3 revision cycles for any phase output; the orchestrator routes to the correct phase worker, the critic returns `[STATUS: APPROVED]` or `[STATUS: REJECTED]` with specific actionable feedback, and the loop halts cleanly with a logged critique if approval is not reached
- **New [`neuroflow:worker-critic`](skills/worker-critic/SKILL.md) skill** — defines the full loop protocol, worker modes (Initial Draft / Revision), rubric construction, critic output format, and `critic-log.md` state tracking
- **Loop integrates with all 15 existing phase agents** — the orchestrator auto-selects the right worker for the active phase from `project_config.md`, covering 18 phases (preregistration, finance, and slideshow share workers with ideation, grant-proposal, and write-report respectively)

## What's new in 0.1.8

- **Target journal clarification in [`/neuroflow`](commands/neuroflow.md)** — on startup, if `paper-write` or `paper-review` is the active phase or in `recommended_phases` and no target journal is set, neuroflow asks whether the user wants a recommendation. If yes: searches PubMed and bioRxiv via the `scholar` agent, ranks 3–5 candidate journals by scope alignment, paper type, OA requirements, length, and prestige vs. speed, then writes the chosen journal to `project_config.md` (and `paper-write/flow.md` if it already exists).
- **Journal recommendation guidance in `neuroflow:phase-paper-write`** — new `## Journal recommendation` section: same search-and-rank workflow available when the skill is invoked directly via `/paper-write`, with explicit recency (past 3 years) and recurrence (≥3 of top 20 results) thresholds.
- **[`/flowie`](commands/flowie.md)** — personal research OS: link a private GitHub repository as a three-layer personal system — identity profile (stances, writing style, methodological preferences), a Kanban task board (`tasks/` with configurable columns, `--tasks --add/--move/--done/--archive`), and a project registry (`projects/` with ASCII phase timelines, `--projects --add`); supports `--init`, `--sync`, `--link`, `--view`, `--identify`, `--tasks`, and `--projects` modes; phase changes auto-sync to the project registry
- **[`neuroflow:phase-flowie`](skills/phase-flowie/SKILL.md)** — phase skill covering how to read and apply the flowie profile in every other phase, write rules for `~/.neuroflow/flowie/`, and a privacy-conscious GitHub sync protocol (always pull before push, diffs before applying, conflicts shown side by side)
- **[`flowie` agent](agents/flowie.md)** — autonomous personalization agent that reads the user's profile at session start, surfaces active tasks for the current project, and shapes all assistance to their documented intellectual fingerprint; never exposes profile data in external-facing outputs
- **New fixed quote** — added *"I will jump to version 1.0.0 once I manage to publish the first paper"* to the [homepage quote bubbles](https://stanislavjiricek.github.io/neuroflow/)
- **Two new fixed quotes added to the homepage hero** — "We will probably be the first ones to understand the brain." and "When I said we, I meant you as well, are you in?" appended as adjacent entries in the [`overrides/main.html`](overrides/main.html) quotes rotation
- **[`/output`](commands/output.md)** — renamed from `/export` to avoid conflict with Claude's built-in `/export` command (which exports conversations); functionality is identical; skill renamed to [`neuroflow:phase-output`](skills/phase-output/SKILL.md)
- **New quote** — added "Can you collect some brain data for me?" to the homepage quote carousel in [`overrides/main.html`](overrides/main.html)
- **Cognitive Development Probe** (since retired) — a self-contained interactive diagnostic: 7 neuroscience-inspired yes/no questions (prediction error, model update, uncertainty, decision monitoring, self-model, global integration, subjective experience); Q7 locked until Q1–Q6 are all YES; color-coded status indicators, "Cognitive Level" progress bar, reset button; includes a read-only **Claude's honest self-assessment** section where the model answers each question as of this version — no hedging, no performance
- **[`/grant-proposal`](commands/grant-proposal.md) dramatically improved** — auto-discovers ideation outputs, fetches funder calls from URLs, supports major international and national funders with built-in review criteria, and drafts section by section with word-count tracking and quality checklists
- **`grant-proposal` agent upgraded** — autonomous funder call parsing, neuroscience-aware Approach drafting (EEG/fMRI/iEEG/eye-tracking), and per-section confirmation loop
- **[`phase-grant-proposal` skill](skills/phase-grant-proposal/SKILL.md) expanded** — deep funder knowledge base, review criteria alignment table, common fatal weaknesses guide, and neuroscience-specific power analysis and preprocessing standards

## What's new in 0.1.7

- **`neuroflow-developer`** (since removed; the plugin targets Claude Code only) — superspecialized GitHub agent for developing and maintaining the neuroflow plugin; merges `neuroflow-core` lifecycle rules and `neuroflow-develop` guidance into one repo-aware agent; reads the live state of every skill, command, agent, and hook at the start of each session so it is always operating on what the repo actually contains

## What's new in 0.1.6

- **Neuroflow Mind** (since retired, with the redesigned site in 0.2.22) — interactive mind map visualization of the entire neuroflow universe; every command, skill, agent, and concept rendered as a force-directed graph with phase clustering; click any node to explore its connections and open its docs; colored receptor dots on each node surface reveal its domain tags (EEG, fMRI, brain-sim, stats, ML, writing, literature, memory, code, human); accessible from the homepage hero button
- **Visual phase map in [`/phase`](commands/phase.md)** — the phase command now renders a full phase map with four distinct markers: `●` current phase, `◉` visited (`.neuroflow/{phase}/` subfolder exists), `→` recommended by neuroflow after the interview, `○` not started; phases are grouped so active and visited appear first, followed by recommended, then the rest
- **Phase sequence suggestion in [`/neuroflow`](commands/neuroflow.md)** — after the initial interview (new Step 2b), neuroflow now derives and prints a recommended ordered phase sequence tailored to the project, and saves it as `recommended_phases` in `project_config.md`; `/phase` reads this field to render the `→` markers in the phase map
- **Phase outlook in [`/interview`](commands/interview.md)** — at the end of any interview session, neuroflow suggests which neuroflow phases are most relevant to where the user is heading, based on the session content and the existing project config

## What's new in 0.1.5

- **[`/git`](commands/git.md)** — context-aware git utility with smart shorthand aliases (`p`, `pl`, `ps`, `a`, `c`, `ac`, `acp`, `b`, `pr`); reads repo state to decide push vs pull, suggests commit messages, and can open PRs via `gh` CLI
- **[`/output`](commands/output.md)** — new utility command and [`neuroflow:phase-output`](skills/phase-output/SKILL.md) skill: export project memory or the whole project as a zip archive or folder copy; always excludes sessions and credentials; logs each export run to `.neuroflow/output/`
- **Slash command availability in all skills** — when any phase skill is invoked directly without its slash command, it now runs the full workflow and mentions the corresponding `/neuroflow:<command>` at the end; behavior defined in [`neuroflow:neuroflow-core`](skills/neuroflow-core/SKILL.md) and declared in each phase skill's `## Slash command` section
- **[`neuroflow:neuroflow-core`](skills/neuroflow-core/SKILL.md)** — added **Default agent behavior** section: scientific honesty (no sugar-coating), dry English humor, and conservative-by-default mode (follow neuroflow-core; only add new functionality when explicitly asked)
- **[`/neuroflow`](commands/neuroflow.md) greeting** — on start, neuroflow now greets with `Hi, neuroflow here (v0.1.5)` followed by a randomly chosen line (*let's do some magic today*, *let's go hack some stuff*, or *I heard HARKing is fun*)
- **15 phase agents** — `ideation`, `grant-proposal`, `experiment`, `tool-build`, `tool-validate`, `data`, `data-preprocess`, `data-analyze`, `notes`, `write-report`, `brain-build`, `brain-optimize`, `brain-run` — each agent is a specialist autonomous subprocess scoped to its phase, with a plan-first / confirm-before-executing discipline
- **[`/preregistration`](commands/preregistration.md)** — new command and [`neuroflow:phase-preregistration`](skills/phase-preregistration/SKILL.md) skill: draft OSF, AsPredicted, or registered-report pre-registrations; review for completeness; log deviations; link registered reports
- **[`/finance`](commands/finance.md)** — new command and [`neuroflow:phase-finance`](skills/phase-finance/SKILL.md) skill: budget planning, expense logging, funder-facing financial reports, and grant compliance checks
- **[`/pipeline`](commands/pipeline.md)** — define and run a multi-step research pipeline across any sequence of neuroflow phases; interactive by default (pauses for approval between steps), or pass `--executor` for brutal mode (runs straight through without stops); supports resuming from a saved plan and graceful error handling
- **Behavioral flags** — three prompt-level personality modes added to [`neuroflow:neuroflow-core`](skills/neuroflow-core/SKILL.md): `executor` (aggressive evaluation loop — reruns and self-critiques until high-quality threshold is met), `teacher` (clarify-first mode — asks targeted questions before each step, proceeds incrementally), and `critic` (interrogates assumptions, surfaces hard questions first). Include any mode keyword in a prompt and it activates for the full command session.

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

- Full research pipeline — commands from [`/neuroflow`](commands/neuroflow.md) through `/paper` and `/review`, each writing to `.neuroflow/` project memory
- [`neuroflow:neuroflow-core`](skills/neuroflow-core/SKILL.md) — shared lifecycle and `.neuroflow/` folder spec that every command and agent follows; commands now automatically append significant decisions to `.neuroflow/reasoning/{phase}.json`
- [`scholar`](agents/scholar.md), [`sentinel`](agents/sentinel.md), [`sentinel-dev`](agents/sentinel-dev.md) agents
- `sentinel` checks plugin version against `project_config.md` and flags when the plugin has been updated; both sentinels clear their report to "All clear" after fixing issues
- `project_config.md` now tracks `plugin_version` — kept in sync with `plugin.json` by `/neuroflow` and `/sentinel`
- MCP servers declared in `plugin.json`: PubMed, bioRxiv, Miro, Context7

---

## Why neuroflow

Most neuroscience software solves one problem at a time — a preprocessing library, a stats package, a reference manager. You still have to stitch everything together yourself, re-explain context at every step, and manually translate between tools and phases.

neuroflow is different. It is not a toolbox. It is the **agentic operating system for neuroscience research** — orchestrating every phase from the first hypothesis all the way to a manuscript draft.

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
| [`/setup`](commands/setup.md) | Integration wizard — Google Workspace CLI, optional Miro (you add it with `claude mcp add`, so no token ever enters the chat) and an Anthropic-compatible LLM gateway; stores non-secret settings in `~/.neuroflow/integrations.json` (or a per-project override) |
| [`/migrate`](commands/migrate.md) | After a plugin update, bring your project, your flowie and the team hive up to the current format — shows the plan, writes only after you agree, pushes to a hive only after your yes |

### Research pipeline

| Command | What it does |
|---|---|
| [`/ideation`](commands/ideation.md) | Brainstorm a research question, explore literature with the inline literature search (open-access only), formalize an idea, keep a standing-query watch list, or produce a project proposal |
| [`/preregistration`](commands/preregistration.md) | Pre-register study design and analysis plan on OSF or AsPredicted; review for completeness; **freeze** the plan (hashes, banner, append-only deviations); log deviations; link registered reports |
| [`/ethics`](commands/ethics.md) | Ethics/IRB workflow — protocol and amendments, versioned consent, approval status with expiry, whether the AI model may read participant data, and participant-erasure requests |
| [`/grant-proposal`](commands/grant-proposal.md) | Write a grant application — specific aims, significance, innovation, approach, budget, timeline, data management plan, and an AI-use statement |
| [`/finance`](commands/finance.md) | Manage the project budget, log expenses in a fixed ledger, produce financial reports, and check grant compliance |
| [`/experiment`](commands/experiment.md) | Paradigm design (PsychoPy) with a static audit, recording setup, counterbalancing, instrument and LSL configuration |
| [`/tool-build`](commands/tool-build.md) | Build a lab tool or software pipeline — real-time systems, acquisition, BCI, paradigm code |
| [`/tool-validate`](commands/tool-validate.md) | Verify a tool or paradigm — marker-to-photodiode timing, XDF and LSL stream checks |
| [`/data`](commands/data.md) | Data intake — locate data, check the ethics gate, validate BIDS structure, keep raw data read-only |
| [`/data-preprocess`](commands/data-preprocess.md) | Run a preprocessing pipeline — filtering, ICA, epoching, artifact rejection, a QC matrix |
| [`/data-analyze`](commands/data-analyze.md) | Run an analysis pipeline — ERPs, time-frequency, connectivity, decoding, GLM — with provenance records, an optional multiverse, and clean-room reruns |
| [`/paper`](commands/paper.md) | Unified manuscript writing and review — draft section by section in a write→critique loop; `--submit` checks citations, statistics and figures and drafts the AI-use statement; `--revise`, `--coauthor`, `--xray`, `--auto` |
| [`/review`](commands/review.md) | Peer review a colleague's paper — asks about the journal's AI policy first, keeps the manuscript confidential, scans for hidden instructions |
| [`/notes`](commands/notes.md) | Live note-taking — capture freeform input verbatim, then reformat it; `--idea` stashes an idea in one step |
| [`/write-report`](commands/write-report.md) | Generate a structured report from `.neuroflow/` contents for any phase or the whole project |

### Brain simulation

| Command | What it does |
|---|---|
| [`/brain-build`](commands/brain-build.md) | Assemble a computational brain model — neuron models, network topology, connectivity, simulation framework setup, smoke tests |
| [`/brain-optimize`](commands/brain-optimize.md) | Run a parameter search behind a smoke gate, or fit the model to experimental data |
| [`/brain-run`](commands/brain-run.md) | Run the model as a simulation — long runs registered in `runs.md`, SLURM/PBS job templates, never heavy compute on a login node |

### Utility

| Command | What it does |
|---|---|
| [`/dashboard`](commands/dashboard.md) | The project at a glance — phase map, deadlines, integrity state, task board counts, the running autoresearch loop (a live pane with the neuroflow mod) |
| [`/doctor`](commands/doctor.md) | Health check of the setup around a project — tools, backups, storage location, contracts, and whether the neuroflow mod is live |
| [`/git`](commands/git.md) | Context-aware git utility — smart push/pull, commit messages, branches, PRs with shorthand aliases whose scope is final; never commits local-only files (sessions, reviews, credentials) |
| [`/pipeline`](commands/pipeline.md) | Define and run a multi-step research pipeline — one step per invocation from a saved plan; interactive by default, or `--executor` for no questions |
| [`/interview`](commands/interview.md) | Interview preparation from either side — tailored questions, practice Q&A, readiness evaluation; candidate notes stay private |
| [`/phase`](commands/phase.md) | Show the phase map and switch phase (a picker you drive with the arrow keys or a click when the neuroflow mod is on) |
| [`/tasks`](commands/tasks.md) | Single entry point for the 3-tier Kanban task board (project / flowie / hive) — view, add, move, complete, archive |
| [`/sentinel`](commands/sentinel.md) | Full audit of `.neuroflow/` — deterministic checks (`nf_check.py`) first, then drift, broken references, preregistration vs progress |
| [`/slideshow`](commands/slideshow.md) | Build a presentation from selected areas of the project — pick phases, figures, and key findings, then get a structured slide deck ready to export |
| [`/poster`](commands/poster.md) | Generate a LaTeX conference poster from project memory — compiled and rendered between critic rounds |
| [`/quiz`](commands/quiz.md) | Neuroscience quiz — flashcards, pub quiz, or rapid-fire throw questions; covers any subfield or general neuroscience |
| [`/fails`](commands/fails.md) | Log dissatisfaction — record core behavior, science quality, or UX issues; opens a GitHub issue only after you confirm |
| [`/output`](commands/output.md) | Export or archive the project with a real exporter (local-only and sensitive files excluded), header de-identification and git-history audits, and a `--handoff` dossier |
| [`/idk`](commands/idk.md) | Personal support companion — decompress, break down overwhelming tasks, or just chat; nothing is logged |
| [`/search`](commands/search.md) | Lightweight scoped search — use `memory:` to search `.neuroflow/` or `project:` to search the codebase; uses `flow.md` as a fast index |
| [`/wiki`](commands/wiki.md) | Project-level shared knowledge base — LLM-maintained wiki at `.neuroflow/wiki/`, git-tracked and shared with collaborators; ingest, query, lint, and add workflows |
| [`/autoresearch`](commands/autoresearch.md) | Open-ended improvement loop for any research artifact — one managing agent makes one focused change per iteration and keeps or reverts it, with a per-loop wiki as memory; an integrity gate for analysis code (confirmatory or exploratory); never stops on its own judgement, always stops at the caps you set, when you stop it, or after repeated errors; bookkeeping by the tested `ar.py` script |
| [`/flowie`](commands/flowie.md) | Personal research OS — link a private GitHub repository as identity profile + Kanban task board + project registry with phase tracking; synced by path with pull-before-push |
| [`/hive`](commands/hive.md) | Team knowledge layer — connect your project to a shared GitHub org repo to sync team research directions, dataset errata, and a review checklist; every push confirmed |
| [`/meeting`](commands/meeting.md) | First-class meetings — recurring templates, agendas with task context, calendar invites after you confirm the recipients, live notes, and tasks from action items |

---

## Skills

Skills are invoked by Claude automatically when relevant, or triggered explicitly.

| Skill | What it does |
|---|---|
| [`neuroflow:neuroflow-core`](skills/neuroflow-core/SKILL.md) | Core rules and lifecycle for all commands and agents — `.neuroflow/` spec and contracts (config frontmatter, integrity status files, JSONL reasoning logs, sharing tiers, command lifecycle keys, rule markers), and behavioral modes (`teacher`, `executor`, `critic`) |
| [`neuroflow:review-neuro`](skills/review-neuro/SKILL.md) | Rigorous pre-submission peer review of a neuroscience manuscript, with a hidden-instruction scan |
| [`neuroflow:worker-critic`](skills/worker-critic/SKILL.md) | Worker-critic agentic loop protocol — orchestrator coordinates a worker agent and a critic agent across up to 3 revision cycles, resuming the same agents for revisions |
| [`neuroflow:autoresearch-protocol`](skills/autoresearch-protocol/SKILL.md) | Improvement-loop protocol — the single-agent loop, per-loop wiki, program.md config with caps, the integrity gate and multiverse ledger, `ar.py` bookkeeping, Q&A channel, and dashboard |
| [`neuroflow:neuroflow-develop`](skills/neuroflow-develop/SKILL.md) | Guide for developing and maintaining the neuroflow plugin, including the mod |
| [`neuroflow:skill-creator`](skills/skill-creator/SKILL.md) | Guide for creating new neuroflow skills |
| [`neuroflow:setup-guide`](skills/setup-guide/SKILL.md) | Configure integrations — Google Workspace, optional Miro, and Anthropic-compatible LLM gateways — without ever asking for a secret in chat |
| [`neuroflow:phase-git`](skills/phase-git/SKILL.md) | Phase guidance for /git — shorthand rules, alias scope, local-only files, smart push/pull, commit messages, branches, PRs |
| [`neuroflow:phase-ideation`](skills/phase-ideation/SKILL.md) | Phase guidance for /ideation — search protocol against the bundled literature server, open-access downloads, standing queries |
| [`neuroflow:phase-preregistration`](skills/phase-preregistration/SKILL.md) | Phase guidance for /preregistration — registry templates, completeness checks, freezing with hashes, deviation logging |
| [`neuroflow:phase-grant-proposal`](skills/phase-grant-proposal/SKILL.md) | Phase guidance for /grant-proposal |
| [`neuroflow:phase-finance`](skills/phase-finance/SKILL.md) | Phase guidance for /finance — budget planning, a fixed expense ledger (`ledger.py`), compliance checks |
| [`neuroflow:phase-experiment`](skills/phase-experiment/SKILL.md) | Phase guidance for /experiment — PsychoPy audit, counterbalancing ledger, preflight template |
| [`neuroflow:phase-tool-build`](skills/phase-tool-build/SKILL.md) | Phase guidance for /tool-build |
| [`neuroflow:phase-tool-validate`](skills/phase-tool-validate/SKILL.md) | Phase guidance for /tool-validate — timing, XDF and LSL checks |
| [`neuroflow:bids`](skills/bids/SKILL.md) | Brain Imaging Data Structure — folder hierarchy, entity ordering, required files per modality (checked against BIDS 1.11.2), sidecars, derivatives, bids-validator digests, pybids, MNE-BIDS, DataLad |
| [`neuroflow:phase-data`](skills/phase-data/SKILL.md) | Phase guidance for /data — ethics gate, read-only raw data, erasure sweep |
| [`neuroflow:phase-data-preprocess`](skills/phase-data-preprocess/SKILL.md) | Phase guidance for /data-preprocess — QC matrix, label-coded blinding, ICA decision records |
| [`neuroflow:phase-data-analyze`](skills/phase-data-analyze/SKILL.md) | Phase guidance for /data-analyze — provenance helper, notebooks, multiverse, clean-room reproduction |
| [`neuroflow:phase-paper`](skills/phase-paper/SKILL.md) | Phase guidance for /paper — write→critique loop, citation/statistics/revision checks, AI-use disclosure, living paper skeleton |
| [`neuroflow:phase-review`](skills/phase-review/SKILL.md) | Phase guidance for /review — referee orientation, confidentiality, delegation to review-neuro, output to .neuroflow/review/ |
| [`neuroflow:humanizer`](skills/humanizer/SKILL.md) | Style editing on request — word blacklist, rhythm, register; never a way to hide AI use, which is always disclosed |
| [`neuroflow:phase-notes`](skills/phase-notes/SKILL.md) | Phase guidance for /notes — live capture format, idea inbox |
| [`neuroflow:phase-write-report`](skills/phase-write-report/SKILL.md) | Phase guidance for /write-report |
| [`neuroflow:phase-quiz`](skills/phase-quiz/SKILL.md) | Phase guidance for /quiz — mode behaviour, question quality standards, mode-specific workflow |
| [`neuroflow:phase-fails`](skills/phase-fails/SKILL.md) | Phase guidance for /fails — categorisation, confirmed GitHub reporting, dissatisfaction capture rules |
| [`neuroflow:phase-output`](skills/phase-output/SKILL.md) | Phase guidance for /output — exporter, header and history audits, PII scan, handoff dossier |
| [`neuroflow:phase-brain-build`](skills/phase-brain-build/SKILL.md) | Phase guidance for /brain-build — neuron models, connectivity, simulation framework, smoke tests |
| [`neuroflow:phase-brain-optimize`](skills/phase-brain-optimize/SKILL.md) | Phase guidance for /brain-optimize — parameter sweeps with a smoke gate, data fitting, optimisation algorithms |
| [`neuroflow:phase-brain-run`](skills/phase-brain-run/SKILL.md) | Phase guidance for /brain-run — long runs, HPC job templates, run registry, output sanity checks |
| [`neuroflow:phase-search`](skills/phase-search/SKILL.md) | Phase guidance for /search — tag-based scoping, flow.md-first indexing strategy, compact summary format |
| [`neuroflow:phase-pipeline`](skills/phase-pipeline/SKILL.md) | Phase guidance for /pipeline — one step per invocation, interactive vs executor mode, pipeline plan format, resume logic |
| [`neuroflow:phase-flowie`](skills/phase-flowie/SKILL.md) | Phase guidance for /flowie — profile read and apply rules, write rules for `~/.neuroflow/flowie/`, one git pattern for sync |
| [`neuroflow:phase-meeting`](skills/phase-meeting/SKILL.md) | Phase guidance for /meeting — meeting file format, recurring templates, attendee resolution, calendar integration, and `meeting_close.py` |
| [`neuroflow:wiki-protocol`](skills/wiki-protocol/SKILL.md) | Knowledge base protocol — LLM-maintained wiki at three levels (personal/flowie, project, team/hive); ingest/query/lint/add workflows, branch-safe sync |
| [`neuroflow:phase-poster`](skills/phase-poster/SKILL.md) | LaTeX poster generation — five templates (A0/A1/A2, portrait/landscape, US size), QR code integration, compile-and-preview between critic rounds |
| [`neuroflow:notebooklm`](skills/notebooklm/SKILL.md) | Google NotebookLM — notebooks, sources (each upload confirmed), artifacts (podcast, video, slides, infographic, report, quiz, flashcards, mind map) and downloads |
| [`neuroflow:phase-hive`](skills/phase-hive/SKILL.md) | Team-level knowledge layer — a shared GitHub org repo for team directions, cross-project findings, dataset errata and recommended methods; all sharing is explicit |
| [`neuroflow:phase-slideshow`](skills/phase-slideshow/SKILL.md) | Phase guidance for /slideshow — audience calibration, slide count heuristics, Markdown/reveal.js and structured outline output formats |
| [`neuroflow:pupil-labs-neon-realtime`](skills/pupil-labs-neon-realtime/SKILL.md) | Connect to Pupil Labs Neon eye-tracking glasses and collect real-time data streams (video, gaze, IMU, events) via the Real-time API |

---

## Agents

Agents are autonomous subprocesses launched by commands when deeper, focused work is needed.

| Agent | What it does |
|---|---|
| [`scholar`](agents/scholar.md) | Searches PubMed and bioRxiv with CrossRef / Semantic Scholar / arXiv fallbacks through the bundled server, downloads open-access copies only (never Sci-Hub), labels each DOI with the check actually done, and ends with a report line the mod can check against the disk |
| [`sentinel`](agents/sentinel.md) | Project coherence guard — runs `nf_check.py` first, then audits `.neuroflow/` for drift, broken references, preregistration deviations, and personal data |
| [`sentinel-dev`](agents/sentinel-dev.md) | Plugin development coherence guard — runs the same checks CI runs (`validate_pr.py`), then the judgement checks |
| [`paper-writer`](agents/paper-writer.md) | Unified paper phase writer — drafts sections from upstream memory, cites only from the project library, returns open questions instead of waiting |
| [`paper-critic`](agents/paper-critic.md) | Unified paper phase critic — applies full eight-area review-neuro methodology to every draft; returns [STATUS: APPROVED] or [STATUS: REJECTED] with specific actionable feedback |
| [`poster-critic`](agents/poster-critic.md) | Conference poster critic — judges the rendered poster and its LaTeX source across content, layout, communication, QR code and LaTeX correctness; operates inside the /poster worker-critic loop |
| [`flowie`](agents/flowie.md) | Personal identity agent — reads the user's flowie profile, surfaces active tasks for the current project at session start, and applies research stances, writing style, and methodological preferences; never exposes profile data in external-facing outputs |
| [`literature-review`](agents/literature-review.md) | Literature review specialist — runs 12 sequential analytical lenses on a set of downloaded papers, checking each lens with a rubric critic pass and saving resumable checkpoints |
| [`autoresearch`](agents/autoresearch.md) | Autoresearch loop agent — the single managing agent for the improvement loop; one focused change per iteration, judged by itself, kept or reverted, with a per-loop wiki as memory; stops at its caps |

---

## Hooks

Hooks fire automatically on tool use events, for every Claude Code user.

| Hook | Trigger | What it does |
|---|---|---|
| Sci-Hub block | `PreToolUse` — the bundled literature server | Denies the server's Sci-Hub tools and any call with `platform: scihub` |
| ruff formatter | `PostToolUse` — Edit / Write | Auto-formats any `.py` file written during a session |
| flowie git-sync | `PostToolUse` — Edit / Write | Commits the file just written to `~/.neuroflow/flowie/` by path, pulls with rebase, and pushes to your private repo; failures go to `~/.neuroflow/flowie-sync.log` |
| PsychoPy audit | `PostToolUse` — Edit / Write | After an edit to a paradigm script or `.psyexp`, adds the static audit's warnings for the model to see |

> **Pre-session orientation:** `/neuroflow` writes one static block into the project's `.claude/CLAUDE.md` that points Claude at `.neuroflow/project_config.md`, where the active phase lives. It is never written to your global `~/.claude/CLAUDE.md`.

---

## The neuroflow mod

neuroflow also ships an optional **mod** — a Claude Code hooks module that runs inside Claude Code. It draws the project at
zero tokens (a dashboard pane, a phase picker, a task board, panes for the living paper, the paper X-ray and the wiki
review queue, a one-line band above the prompt that only speaks when something needs attention, a status line, a
footer label), answers `/neuroflow:doctor`, `/neuroflow:dashboard` and the status views instantly, captures notes and
ideas without model turns, gives each command a digest of the facts it reads first, checks new citations after
manuscript writes and scans documents from outside for hidden text, drives an autoresearch loop one iteration per turn
under its caps, drafts a missing decision for you to keep or drop, and enforces the rules the skills state — frozen
preregistrations, read-only raw data, local-only files, participant-data routes, HPC login nodes, git alias scope.

It is a layer, not the product: everything works without it. Settings (`runtime: off | observe | on`, default
`observe`; `guards: warn | enforce`; `band`; `citations`) live in Claude Code's plugin configuration. Read
[docs/concepts/mods.md](docs/concepts/mods.md) for what it does, when it does not load, its 30-rule charter, and the
doors guards cannot close; [docs/concepts/design-record.md](docs/concepts/design-record.md) for what became of every
idea behind it.

---

## Project memory

Every neuroflow command writes its output to `.neuroflow/` at the root of your project repo. This is the shared memory of your project — readable by every command and agent, across sessions.

```
.neuroflow/
├── project_config.md       ← frontmatter contract: nf_schema, active_phase, recommended_phases, raw_roots… — read by every command
├── flow.md                 ← index of all subfolders
├── objectives.md           ← project objectives
├── timeline.md             ← milestones and deadlines
├── sessions/               ← one .md per day (local only)
├── reasoning/              ← per-phase decision logs, JSON Lines (statement, source, reasoning)
├── tasks/                  ← Kanban board: tasks/{column}/{slug}.md
├── wiki/                   ← project wiki (an Obsidian vault)
├── ethics/                 ← protocols, consent, status.md (approval, expiry, ai_processing)
├── preregistration/        ← OSF / AsPredicted documents, status.md (frozen + hashes), deviations.md
├── finance/                ← grant documents, expense ledger
├── ideation/               ← research questions, proposals, literature, watch list
├── grant-proposal/         ← grant application drafts
├── experiment/             ← paradigm notes, recording setup docs
├── tool-build/             ← tool specs and build notes
├── tool-validate/          ← validation plans and results
├── data/                   ← data inventory and intake reports
├── data-preprocess/        ← preprocessing configs and QC reports
├── data-analyze/           ← analysis plans, summaries, multiverse ledger, run registry
├── paper/                  ← manuscript work, critic logs, living paper skeleton
├── review/                 ← referee work on others' manuscripts (local only)
├── notes/                  ← structured notes and the ideas inbox
├── meetings/               ← meeting files
├── write-report/           ← project reports
├── fails/                  ← dissatisfaction log: core.md, science.md, ux.md
└── output/                 ← output log: one .md per export run
```

---

## Installation

neuroflow is a Claude Code plugin. In Claude Code (v2.1.275 or later):

```
/plugin install neuroflow --marketplace stanislavjiricek/neuroflow
```

Or in two steps, from a terminal:

```bash
claude plugin marketplace add stanislavjiricek/neuroflow
claude plugin install neuroflow@neuroflow
```

or inside Claude Code:

```
/plugin marketplace add stanislavjiricek/neuroflow
/plugin install neuroflow@neuroflow
```

For local development:

```bash
git clone https://github.com/stanislavjiricek/neuroflow
claude --plugin-dir ./neuroflow
```

Once installed, run `/neuroflow:neuroflow` in any project folder to get started. After an update, run `/neuroflow:migrate` once per project ([upgrading](docs/upgrading.md)).

---

## Integrations

The bundled MCP servers start automatically via `npx`, pinned to tested versions, and need no credentials:

| Server | Package | What it is for |
|---|---|---|
| Literature (PubMed, bioRxiv, CrossRef, Semantic Scholar, arXiv…) | `paper-search-mcp-nodejs` | Search and open-access downloads (its Sci-Hub adapter is switched off) |
| Context7 | `@upstash/context7-mcp` | Current library documentation |
| Sequential thinking | `@modelcontextprotocol/server-sequential-thinking` | Step-by-step reasoning tool |

Optional integrations you add yourself — `/neuroflow:setup` walks you through each, and never asks for a secret in chat:

| Integration | How |
|---|---|
| Miro | `claude mcp add --scope user miro -e MIRO_ACCESS_TOKEN=<token> -- npx -y @k-jarzyna/mcp-miro`, typed in your own terminal — never with the `!` prefix, whose commands and output are recorded in the conversation |
| Google Workspace CLI (`gws`) | `npm install -g @googleworkspace/cli` (Node.js 18+), then `gws auth login` with an OAuth `client_secret.json` from Google Cloud Console |
| Anthropic-compatible LLM gateway | base URL and model aliases in `~/.neuroflow/integrations.json`; the key stays in a file you control — see the [custom gateway guide](skills/setup-guide/references/custom-gateway.md) |
| Zotero | an MCP server of your choice; `/ideation` searches your library first when it is there, and writes notes only when you opt in |

Non-secret settings live in **`~/.neuroflow/integrations.json`** (global) or **`.neuroflow/integrations.json`** (per-project override, gitignored). Re-run `/neuroflow:setup` any time; `/neuroflow:doctor` checks the rest of the setup.

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
