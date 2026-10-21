---
title: Changelog
---

# Changelog

Every neuroflow release, newest first. The README on GitHub shows only the newest one.

## 0.2.30

From a live check of the mod in Claude Code 2.1.306, in a plain console and inside tmux at 80×24:

- A pane that does not hold the keys names only the way back: running its command again (`… gives it the keys`); it no longer says ^X Tab reaches it after the band, because ^X Tab moves the keys between the prompt and the band but not into an open pane
- The [mods](concepts/mods.md) page and the live check say so; for the dashboard, `d` on the band (after ^X Tab) also gives it the keys

## 0.2.29

Fixes from a live check of the mod in a terminal (Claude Code 2.1.306):

- Claude Code's question dialog hands the keys to the prompt when it closes, so after *Not now* the next key of a pane went into the prompt; the board, the dashboard, the phase picker and the wiki, X-ray and living-paper panes now take the keys back after a no
- The mod's status line text no longer starts with `neuroflow:`, which Claude Code already prints before a plugin's status entry
- The [mods](concepts/mods.md) page and the live check say what the check saw: a letter that is no key of a pane gives the keys back to the prompt and lands there

## 0.2.28

Fixes from a review of 0.2.27's mod views:

- Wide text fits: `cells`, `fit` and `pad` count East Asian wide characters and emoji as two cells, and a label cut to its column keeps a blank cell before its value (the loop tab, the X-ray, wiki and living-paper panes)
- The task board's footer says what `⚠` means; the phase picker and the typeahead give each phase the same mark and word (`◉ current`, `→ next`, `→ recommended`, `● visited · next`, `○ not started`), and the workbench page marks recommended phases `→`
- [`/phase`](commands/phase.md) and meeting agendas mark dates like the dashboard (`⚠` within three days or overdue, `▸` within 14 days, `·` later); the glyph legend gains `▸`
- The typeahead: `--level hive` without `--hive` uses your only hive's board, and `/neuroflow:migrate` is no longer offered `--hive`
- The dashboard's integrity tab names what the model may read in words; the text form of every tab is tested on what the pane draws; the docs' figures draw symbols one cell wide, and the layout and live-check pages state the widths the views use ([mods](concepts/mods.md))

## 0.2.27

The mod from the keyboard, its new look, and the claude.ai workbench:

- The neuroflow mod is usable from the keyboard alone, for example over SSH: the dashboard, the task boards, the phase picker and the wiki, X-ray and living-paper panes open holding the keys, and one key registry (`hooks/mod/lib/keys.ts`) gives every key one meaning — digits pick a tab or a level, `h` `j` `k` `l` move, Enter acts, `q` closes, Esc gives the keys back to the prompt; the band keeps its letters and teaches `^X Tab`
- Typing never acts: a pane that holds the keys ignores the keys typed right after it opens, and keeping or dropping a drafted decision, migrating, syncing, a meeting action, a board move, a phase switch from the picker or a review decision is confirmed with a question whose safe answer comes first
- The views in the new look: the `◌` mark, a phase flow line in the glyph legend (`◉` current, `●` visited, `→` recommended, `○` not started), a dates ruler with week ticks, rounded board columns with pages past five cards and a list layout for narrow docks, a `now` tab with every band item, theme colours only; [`/dashboard`](commands/dashboard.md), [`/tasks`](commands/tasks.md) and [`/phase`](commands/phase.md) describe the keys, and the mod's figures are redrawn ([mods](concepts/mods.md))
- Typeahead for phases, dashboard tabs, hives, levels and card names after a neuroflow command
- The claude.ai workbench ([workbench](concepts/workbench.md)): one private page per person with a tab for the flowie, each hive and each project; `/dashboard --web` exports an allowlisted snapshot after a preview and a yes (hive and project data only with the team's `workbench_mirror` opt-in), and `/tasks --apply-web` checks the moves and new tasks queued on the page against git, applies them with the `/tasks` rules and commits them with a `Neuroflow-Intent` trailer; a mod guard asks before ArtifactData writes anywhere else and never lets Claude create an intent

## 0.2.26

A new front page and one look:

- The ring replaces the old logos everywhere: the site logo and favicon, link previews (a 1280×640 card), the README lockups and the plugin icon all come from one generator, `scripts/automation/brand_assets.py`. The old `logo.png` and the brain SVGs are gone, so every installed version is 5.5 MB lighter, and [`/neuroflow`](commands/neuroflow.md) greets with a ring of nineteen dots instead of the ASCII logo
- The 4:33 intro video plays on the landing page and on the [Overview](overview.md#intro-video); the docs deploy fetches it from the `intro-video` release, so it never enters git or a plugin install
- The README shows only the newest release, with links to the website, the documentation and this changelog, which now holds every release (0.1.7 to 0.2.3 backfilled). `validate_pr.py` V12 fails on a second What's new section, and V10 checks the whole README: links, images, anchors and the pages its site links point to
- The docs now hold what only the README said: the flowie hook's hold-back of machine-local paths and its `--autostash` pulls, the Google Workspace CLI install, and the mod's paper, X-ray and wiki-review panes; `research_radar.py` reads this changelog
- The plugin and marketplace descriptions open with "Your team's shared memory, inside Claude Code"; `plugin.json` names an icon and the documentation site

## 0.2.25

Fixes from a final review of 0.2.24:

- `projects.py fold` never puts a machine-local folder on the team's card: such entries of the flowie card come back as `local_repos`, and `/neuroflow:migrate` 5.7 writes them into `~/.neuroflow/local-projects.json` before folding; it skips the fold when the flowie or every hive did not pull cleanly. Anything in `repos` that is no remote URL counts as a local folder (`$HOME/…`, `../…`, a relative path), and the local rows of a flowie note's `Repos` table are listed too
- Sentinel S9 shows the registry findings in the session only; `.neuroflow/sentinel.md`, which is committed with the project, gets one count line — the messages name private flowie projects, task files and folders
- `/flowie --sync` resolves an autostash conflict with the person (both versions shown, nothing with conflict markers committed, the autostash entry dropped after); the auto-sync hook and the mod skip while git marks a file as conflicted and log `autostash conflict` when their own pull leaves one
- `/neuroflow:migrate` moves only this member's own values out of a tracked hive `sync.json` (the keys that differ from the committed copy)
- `projects.py`: a `repos` string is one repository everywhere; a task's `project:` may name a card of another level; a repository key part never ends in a dot; the cache's git keeps a person's own ssh setup (`GIT_SSH`, `GIT_SSH_COMMAND`, `core.sshCommand`)
- `/flowie` never stages a file git marks as conflicted, and `--sync` resolves such files before it pulls; the hook's log names them
- `/phase` step 7 runs for `--sync` too (without repeating a timeline row); `/tasks --project` shows the script's problems; the mod reads `name`-keyed cards and `repos` strings like the script

## 0.2.24

**One project, one card ([#256](https://github.com/stanislavjiricek/neuroflow/issues/256))**

- A project is described once: a team project's card (status, phase, description, repositories) lives in its hive, a personal project's in the flowie, and the other level keeps only a pointer (`{"id", "ref": "hive:{org}/{repo}"}`) with the person's notes — neuroflow-core → Project registry
- Changes go to the card wherever they start: `/phase` offers to record a new phase on a team project's hive card and pushes after the person's yes; `/flowie --projects --add` asks whose project it is and registers a team project in its hive with a pointer in the flowie
- `/tasks` gains Placement — a task goes on the narrowest board everyone who must see it can read (flowie, hive, or the repository's board), and `--add` proposes it — and `--project {id}`, which shows one project's open tasks from every board, including the boards of its other repositories, read through a shallow, sparse cache in `~/.neuroflow/boards/` that is refreshed each time
- New `skills/neuroflow-core/scripts/projects.py` (`list`, `check`, `view`, `refresh`, `fold`): `/neuroflow:migrate` folds two cards of one project into one (the person picks each differing value; the hive is written only after their yes), and `/sentinel` reports two cards, pointers that lead nowhere or copy card fields, `blocked_by` entries that name no task, and open tasks whose project is not registered
- With the mod, the tasks tab and the board pane name the project by its card id at every level and show the boards of its other repositories, read-only, from that cache (refreshed in the background when the boards open)

**Fixes**

- [#252](https://github.com/stanislavjiricek/neuroflow/issues/252): the mod's flowie sync skipped every sync as "git hooks or LFS", because Claude Code runs git with `-c core.hooksPath=<null device>`; only the repository's, the person's and the system's config count now (the last value wins), only real hook names in `.git/hooks`, and the log line names what fired
- [#253](https://github.com/stanislavjiricek/neuroflow/issues/253): the wellbeing band asks only once it knows today's entry is not already on the flowie remote — a background fetch as a session starts in a neuroflow project, never holding the first prompt and never touching the work tree; offline, or with git hooks or LFS in the flowie, it asks as before
- [#251](https://github.com/stanislavjiricek/neuroflow/issues/251): machine-local paths stay off the flowie remote — `skills/phase-flowie/scripts/local_paths.py` finds them (system and web paths, link targets and examples are not paths; a line marked `nf: local-path-ok` is kept), the auto-sync hook holds such a file back and logs it, the `/flowie` Sync step checks before staging and offers to move each path into `~/.neuroflow/local-projects.json`, and `/neuroflow:migrate` reports the ones already in the flowie; every flowie pull runs with `--autostash`, so a held-back file never stops a later sync
- [#254](https://github.com/stanislavjiricek/neuroflow/issues/254): a hive member's sync state is `.git/neuroflow-sync.json` in the clone, which git can never track or publish; `/neuroflow:migrate` moves an untracked `sync.json` there, heals a tracked one an older neuroflow wrote into (its values move out, the file goes back to its committed text), and still reports a tracked one as the team's call
- [#255](https://github.com/stanislavjiricek/neuroflow/issues/255): the X-ray pane lists the open findings red first, 64 at a time (8 on mobile), and `n` / `p` move between pages; above 64 the engine refused the whole pane

## 0.2.23

- Tasks at every level in the mod: the dashboard's tasks tab sums up the project board, your flowie and each hive you joined (this project's share where a level links it), and the bare `/neuroflow:tasks` pane switches between their boards with `v`, this project's cards first and marked; a move fills the prompt with one `/tasks` command, which gains `--hive {org-repo}`. Read-only: the mod never pulls or moves task files
- Fix: the mod read every folder as a file (the engine lists folders as `kind: 'dir'`), so in real sessions it found no task board, visited phases, loop registries or hive wikis
- `/neuroflow:migrate` brings a level with uncommitted changes along instead of leaving it out: for your flowie it offers to sync them first, for a hive it pulls with `--autostash` and leaves them as they are; a planned change to a file with local edits is named in the plan and included only with your yes. `migrate.py --json` lists each level's `uncommitted` paths
- `/doctor` reports uncommitted changes in your flowie and lists the version check
- The mod's flowie syncs (the wellbeing check-in on the band, `idea: …`) are queued and run before your next neuroflow command or when a turn ends, never from the band's own field; every attempt is logged in `~/.neuroflow/flowie-sync.log`, and a sync that did not go through stays on the band
- The version notice is said verbatim, as one sentence; `/setup` skips it with the mod too, and the band offers `m` whenever it shows the notice
- Site: the search field stays at the top of the index on every page (`/` focuses it), content tabs and command titles fit on phones, no empty bands while filtering, the landing fits the smallest phones, About agents links each agent, and the old addresses of the renamed skills redirect
- CI runs Claude Code on Node 22; the upgrade notes say neuroflow 0.2.22 and later need Claude Code 2.1.271 or later

## 0.2.22

**Site, docs and upgrading**

- A one-screen landing page: scrolling turns the cycle of nineteen phases, then a memory chapter (you, the project, the team) and the next study
- Documentation without a top bar or tabs: one index on the left with search across every page (it filters the index and lists matching sections), sections for the phases, memory and team, commands, the harness, agents, skills and reference; the page outline on the right; light and dark colours from the system setting
- New pages: [Overview](overview.md), [Three levels](concepts/memory.md) and [Upgrading](upgrading.md); [the mod page](concepts/mods.md) shows the harness as Claude Code draws it; the mind map and the self-assessment bar are gone, with their checks
- The upgrade path: the first neuroflow command after an update says which version the project is on and names `/neuroflow:migrate`, which brings the project, your flowie and the team hive up to date and records the version (`plugin_version` is written only there and by the scaffold, and never goes down) — legacy task files move to the current format with `git mv`, machine-local files stay out of git, a file it cannot decode is reported and never rewritten, and a hive is written and pushed only after your yes, with everything that would leave shown first ([Upgrading](upgrading.md)); with the mod, the same line waits in the band and in the dashboard
- Skill renames, so no skill hides behind a command of the same name: `autoresearch-protocol`, `wiki-protocol`, `setup-guide`; internal skills leave the slash menu
- Fixes: neuroflow commands use the running plugin's folder (`${CLAUDE_PLUGIN_ROOT}`) and never a cached copy; `doctor.py`, `nf_check.py`, `scaffold.py` and `migrate.py` no longer fail on Windows pipes with a legacy code page; the handoff dossier lists open tasks by owner; the mod's guards no longer flag read-only `/git` steps, a `.gitignore` that ignores `.neuroflow/` as a whole, paths that merely contain a raw folder's name, or a new recording moved into it; a command typed without the `neuroflow:` prefix gets the same notes from the mod; `/doctor` reports the flowie's unpushed commits and sync failures; `nf_check` flags a `wiki_auto` key left in the shared config; the wiki-card judge never raises a skipped card again

**The neuroflow mod** (optional Claude Code hooks module — see [The neuroflow mod](concepts/mods.md))

- Views drawn by code at zero tokens: a dashboard pane (phase map, deadlines, integrity, tasks, autoresearch loop with a quality sparkline and open questions), a phase picker for `/neuroflow:phase`, a task board for `/neuroflow:tasks`, a one-line band above the prompt that speaks only when something needs attention (deadlines, expired approvals, meetings with prepare/notes/close keys, an opt-in wellbeing check-in), an exception-only status line, a footer label, and one stable identity section in the system prompt
- `/neuroflow:doctor` answered instantly when the mod is live; bookkeeping gaps (missing session lines, flow.md rows) filled and marked `(auto)`; a decision drafter that proposes one reasoning entry after a command that logged none, written only after a keep press
- Zero-turn capture: `idea: …` and `/notes --idea` go straight to the inbox; live note capture writes each message verbatim without reaching the model
- An autoresearch driver: `/autoresearch drive {name}` runs one iteration per turn and checks the caps with `ar.py status` between turns, with a visible stop control
- Guards with an observe → warn → ask → deny ladder: frozen preregistrations, read-only raw data, local-only files and `git clean -x`, git alias scope, participant data the ethics record keeps from the model, heavy compute on HPC login nodes, model-forged integrity markers, uploads to outside services
- Integrity in the dashboard: freeze, verify and unfreeze the preregistration on a key press and an explicit yes (the same `freeze.py` calls, recorded as the person's action); frozen files re-hashed at start, with a change on the status line
- Checks triggered by what the model did: new DOIs in a manuscript, grant, poster or report looked up after the turn (`cite_check.py --max-age`), the manuscript's notices re-checked weekly, and documents from outside scanned for hidden text when read
- Context without bloat: a capped digest of a command's integrity facts as it starts, wiki pages a prompt names attached as data, a capped digest of a linked flowie profile, the current and next phase marked in the slash menu; a `quiet` command such as `/idk` silences the mod's own UI
- Panes for the person's ideas: the living paper (`/paper --auto status`, `y` to sync), the paper X-ray (`/paper --xray view`: accept or reject findings by key; `--xray check` runs the scripts only) and the auto-wiki review queue (cards drafted after a logged decision, accepted into the normal `/wiki --add` flow or skipped)
- A 30-rule charter, settings (`runtime`, `guards`, `band`, `citations`), the list of doors guards cannot close, a capability allowlist checked in CI (`hooks/mod/policy.json`), a weekly canary on the newest Claude Code release, and a [design record](concepts/design-record.md) of all 270 ideas behind the mod

**Research integrity**

- Autoresearch: an integrity gate for loops that touch analysis code (confirmatory on blind inputs with outcome-blind criteria, or exploratory with forked scripts and a multiverse ledger); caps and stop conditions (`max_iterations`, `max_wall_clock`, `max_cost`, `max_consecutive_errors`); `ar.py` transaction bookkeeping with tests
- `/preregistration` Freeze mode (hashes via `freeze.py`, banner, append-only deviations, `planned_n`, a machine-readable parameters block); `/data` and `/experiment` check the ethics status before data collection; `/ethics` records whether the AI model may read participant data and handles erasure requests
- `/paper --submit` drafts an AI-use statement from evidence plus an acknowledgements line and runs citation (`cite_check.py`: DOI resolves, retraction notices), statistics (`statcheck.py`) and figure checks; `--revise` audits every change against reviewer comments; `--coauthor` round-trips Word comments; `--xray` gives a per-sentence analysis; `--auto` keeps a living paper skeleton
- `/review` asks about the journal's AI policy first, keeps manuscripts local, and scans for hidden instructions (`hidden_text_scan.py`); the humanizer is style editing on request, never a way to hide AI use

**Project memory contracts**

- `project_config.md` frontmatter with `nf_schema`; integrity status files with `set_by`; reasoning logs as JSON Lines; union-merge lines and a conflict tripwire; sharing tiers with confirmed egress; command `lifecycle` / `requires` / `produces` / `next` keys; rule markers
- New `/neuroflow:migrate` (with `migrate.py`) for older projects, an idempotent `scaffold.py`, personal preferences and consents in `~/.neuroflow/user.yaml`, and a read-only project checker `nf_check.py` used by `/sentinel`

**Science scripts** (portable Python, each with unit tests)

- Data and analysis: `nf_provenance.py`, `qc_table.py`, `multiverse.py`, `cleanroom.py`, `blind_labels.py`, `bids_digest.py`, `erasure_sweep.py`
- Experiments and tools: `psychopy_audit.py`, `allocation.py`, `timing_check.py`, `xdf_check.py`, `lsl_check.py`
- Modelling and HPC: `smoke_test.py`, `sweep_run.py`, `runs.py`, SLURM and PBS job templates, a long-run convention
- Sharing: `export.py`, `header_scan.py`, `history_audit.py`, `handoff.py`, `pii_scan.py`; collaboration: `meeting_close.py`, `ledger.py`; health: `doctor.py`

**Literature and collaboration**

- Search protocol and scholar rewritten against the bundled server's current tools; open-access downloads only, Sci-Hub blocked by a hook and in the server; DOI labels name the check done; a standing-query watch list
- One task format at every level; `/meeting --notes` and `--close`; flowie sync by path with pull before push and a failure log; hive dataset errata, review checklist and `--doctor`

**Platform**

- neuroflow targets Claude Code only: one static project instruction block in `.claude/CLAUDE.md` (never the global file); Copilot and other-host files removed
- Provider-neutral custom gateway guide; Miro moved out of the manifest and added by the user with `claude mcp add`; MCP servers pinned
- One implementation per repository check (`repo_checks.py`, V1–V15) for CI and sentinel-dev; `bump_version.py`; fixed YAML frontmatter of two critic agents whose fields were silently dropped
- New commands: `/dashboard`, `/doctor`, `/migrate`

## 0.2.21

- **Consistency overhaul from a full plugin review** — hooks rewritten against the real stdin-JSON contract (both were silently dead); one canonical credentials scheme (global `~/.neuroflow/integrations.json` + per-project override, flowie non-secrets only); one canonical phase taxonomy in `neuroflow-core` replacing four divergent copies; eight-area review methodology everywhere; `/setup` step numbering fixed; dead references purged (`linked_flows.md`, ghost agents, `/export`, `--share`); custom gateway guide rewritten for native Anthropic-compatible gateways (no proxy needed)
- **Lifecycle enforcement** — missing-`.neuroflow/` global rule + one canonical session-log format in core; new PR-time CI (`validate.yml` + `validate_pr.py`: JSON validity, frontmatter schema, phase values against the canonical taxonomy, docs pages, version-bump gate); sentinel-dev checks 2/5/7/10/12 implemented in `sentinel_check.py`; mind-map check aligned to the concept-map design; audit agents (`paper-critic`, `poster-critic`, `sentinel`, `sentinel-dev`, `literature-review`) get `tools:` allowlists
- **Science-PM surface** — new `/ethics` and `/tasks` commands; `/paper --submit` / `--revise` (strict minimal-change rebuttal discipline) / `--abstract`; `/output --archive` with de-identification checklist and DOI recording; DMP drafting in `/grant-proposal`; `objectives.md`/`timeline.md` created by `/neuroflow` and rendered by `/phase`; reproducibility manifests in data phases; deliverables moved out of `.neuroflow/` (poster/slides/tests/reports); wikis guaranteed Obsidian-vault-compatible; optional Zotero-first literature search in `/ideation`

## 0.2.20

- **autoresearch rebuilt around a per-loop wiki** — a single managing agent (no worker/evaluator subagent fan-out) runs the loop and uses a scoped `wiki/` as its brain: reads it before every move, records every attempt (wins *and* failures) after. Lets an infinite single-agent loop compound instead of re-treading dead ends.
- **Loop folder moves next to the artifact** — named `{name}_autoresearch/`, located beside the tracked files (overridable); a pointer registry in `.neuroflow/{phase}/autoresearch-loops.md` keeps project memory aware. Multiple loops per phase now supported.
- **New capabilities, all configurable** — agent-decided branching, literature search when stuck, self vs fresh-eval, a human `report.md` with a non-blocking stacked Q&A channel (answer via session or `answers.md`), and a dashboard that now renders the report + open questions alongside the trend charts.

## 0.2.19

- **New `neuroflow:bids` skill** — comprehensive BIDS reference covering all modalities (MRI/EEG/MEG/iEEG/PET/DWI/NIRS/motion), entity ordering, JSON sidecar fields, derivatives structure, bids-validator, pybids, MNE-BIDS, fMRIPrep, dcm2niix/HeuDiConv conversion examples
- **BIDS integrated into data phases** — `phase-data`, `phase-data-preprocess`, `phase-data-analyze` now reference `neuroflow:bids`; `mind.js` updated with `sk-bids` node

## 0.2.18

- **`/wiki` docs page** — `docs/commands/wiki.md` now tracked and reachable via mkdocs nav under Team Integration

## 0.2.17

- **Global `~/.neuroflow/` structure** — flowie and hive caches move to global `~/.neuroflow/flowie/` and `~/.neuroflow/hive/{org-repo}/`; `integrations.json` global; `team.md` and `linked_flows.md` removed; collaborators in `project_config.md`
- **Global auto-sync on session start** — neuroflow-core pulls flowie + all hive caches at session start
- **Cross-wiki ambient search** — ambient pre-query searches all wikis (flowie, all hive caches, project); answers cite source level
- **Wiki crystallization hook** — neuroflow-core detects insights at command end, offers smart-routed wiki ingest; per-command wiki nudges removed
- **Docs mirrors created** — `/wiki`, `neuroflow:wiki`, `neuroflow:setup`, `neuroflow:phase-meeting`, `autoresearch` agent docs pages added
- **Dead agent rows removed** — 16 stale phase agent rows removed from README; `mind.js` updated with `sk-flowie`, `sk-hive`, `sk-slideshow`, `ag-scholar`

## 0.2.16

- **`flowie_profiles` list** — replaces `flowie_project` + `hive_member` scalars in `project_config.md` with a single `flowie_profiles:` list (`handle` + `repo` per entry); first entry = project owner; additional entries added by collaborators via `/flowie --link`; backward-compatible
- **Global user identity config** — `/setup` Step 6 writes `~/.neuroflow/user.yaml` with `flowie_handle`, `flowie_repo`, and `hives`; `/neuroflow` Step 1b reads it to pre-fill the GitHub username on new projects
- **Sentinel migration guard** — flags legacy `flowie_project:` and `hive_member:` scalar fields; suggests `/neuroflow` to migrate

## 0.2.15

- **[`/meeting`](commands/meeting.md)** — first-class meeting command with recurring templates, Google Calendar invites, agenda preparation from project context, and action-item-to-task conversion at project/flowie/hive level
- **3-tier task model** — tasks at personal (flowie), project (shared), and hive (team) levels; `--level` flag on `/flowie --tasks`; mandatory ASCII kanban rendering on all displays
- **Collaboration model** — `.neuroflow/flowie/` gitignored from project repos; `.neuroflow/tasks/` git-tracked and shared; collaborator join flow added to `phase-hive`; `collaborators:` list in `project_config.md` for meeting invite resolution

## 0.2.14

- **Personal wiki** ([`/flowie --wiki-*`](commands/flowie.md)) — Karpathy-style LLM-maintained knowledge base inside your flowie repo; ingest sources, query accumulated knowledge, lint for orphans/contradictions/stale pages; every page is tagged to flowie projects; closing prompts in `/notes`, `/ideation`, `/data-analyze`, and `/paper`
- **New [`neuroflow:wiki`](skills/wiki-protocol/SKILL.md) skill** — page types/frontmatter schema, ingest/query/lint/add/schema workflows, project tagging (always prompted), ideas.md and profile.md sync, fails integration for method pages, sentinel Check 12 for wiki health

## 0.2.13

- **`/autoresearch`** — infinite worker-evaluator loop for any research artifact; per-phase criteria auto-loaded; live dashboard at localhost:8765; triggers via `/autoresearch` or any phase command + `autoresearch` keyword
- **Agent cleanup** — removed 16 unused phase agent files; 8 confirmed-spawned agents remain; orchestrator protocol merged into worker-critic skill

## 0.2.12

- **Notes → flowie sync** ([`/notes`](commands/notes.md)) — after every notes session, Claude offers to copy the formatted note to `.neuroflow/flowie/notes/` for GitHub sync (default: yes); a local `config.json` stores per-project defaults for type, speaker, and project relation
- **Daily wellbeing tracking** ([`/flowie --assess`](commands/flowie.md)) — opt-in daily self-assessment for anxiety, energy, and happiness on a 1–10 scale (5=neutral); stored in `flowie/wellbeing/`; Claude prompts on any sync operation if today's entry is missing; enabled via `/flowie --init` or `/flowie --assess`

## 0.2.11

- **Removed broken `pubmed-mcp-server`** — `pubmed-mcp-server@1.0.0` on npm has an empty `dist/index.js` (TypeScript was never compiled before publishing); removed from `plugin.json`; PubMed search is now handled by `paper-search-mcp-nodejs` (the biorxiv server) which already includes `search_pubmed` and requires no credentials; `PUBMED_EMAIL` is no longer needed and has been removed from the setup wizard, skills, commands, and docs

## 0.2.10

- **Global device config** ([`/setup`](commands/setup.md)) — credentials can now be saved once to `~/.neuroflow/integrations.json` (global, all projects) or per-project; per-project takes precedence; Step 0 of the wizard asks which scope to use; per-project config still gitignored as before
- **Windows support** — [`/setup`](commands/setup.md), [`neuroflow:setup`](skills/setup-guide/SKILL.md), and the [custom gateway guide](skills/setup-guide/references/custom-gateway.md) now cover Windows paths (`%USERPROFILE%`), PowerShell env var syntax, and `where gws` detection throughout
- **Proxy model-name fix** ([`proxy.mjs`](skills/setup-guide/scripts/gateway/proxy.mjs)) — proxy now patches `model` field in every response chunk back to the original `claude-*` name, preventing Claude Code's *"unexpected model"* error when using custom LLM providers via Mode B
- **`integrations.json` gitignore in flowie** — [`flowie`](agents/flowie.md) agent now requires `integrations.json` to be gitignored in the flowie sync repo; warns before any push if it is missing; added to plugin `.gitignore` as well

## 0.2.9

- **New [`neuroflow:setup`](skills/setup-guide/SKILL.md) skill** — agent-facing knowledge for all neuroflow integrations (PubMed, Miro, Google Workspace, custom LLM providers); mirrors the `/setup` wizard logic so agents can guide credential setup without running the command
- **Custom LLM gateway integration** — a [gateway guide](skills/setup-guide/references/custom-gateway.md) documents connecting Claude Code to an Anthropic-compatible gateway; covers direct mode, proxy mode (with the `proxy.mjs` script), model aliases, and the full terminal workflow
- **`/setup` Step 5** — new optional custom LLM provider wizard; saves non-secret settings to `integrations.json` and optionally to the linked flowie profile for cross-machine sync; an Anthropic-compatible gateway is documented as the example
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

## 0.2.8

- **Session logging overhaul** — removed the noisy `[tool]` PostToolUse hook; Claude now owns all session logging and writes entries broadly after most actions; `neuroflow-core` logging rules are marked MUST and non-negotiable; `flow.md` purity rule added (pure index table only, no narrative content)
- **mind.js consistency check** — `sentinel-dev` Check 11 audits that every skill, command, and agent has a node in `mind.js`; missing `humanizer` node added; `neuroflow-develop` release workflow now marks the mind.js update step as blocking

## 0.2.7

- **Grant-proposal overhaul** — interview-first workflow (10-question conversational interview, objectives saved to `.neuroflow/objectives.md`); inspiration map from previous grants (cross-reference table saved to `.neuroflow/grant-proposal/inspiration-map-[date].md`); optional panel research (WebFetch + WebSearch, panel profiles saved to `.neuroflow/grant-proposal/panels/`); objectives tracked as cornerstones throughout the session; `sequentialthinking` MCP invoked before Innovation and Approach sections
- **Humanizer replaces stop-slop** — new `neuroflow:humanizer` skill: AI word blacklist, structural pattern removal, rhythm checks, register calibration, voice preservation; applied across `/grant-proposal`, `/paper`, `/poster`, `/write-report`; `stop-slop` skill removed
- **Memory quality improvements** — sessions use `##` milestone headers (commands) + `- HH:MM [tool]` audit lines (hook); reasoning mandate raised to 3–5 decisions/session with mandatory trigger list; `objectives.md` added as a root file read at the start of every command; `@modelcontextprotocol/server-sequential-thinking` MCP server added; review output moved from `reviews/` to `.neuroflow/review/`

## 0.2.6

- **Scholar agent: download reporting fixes** — `.pdf`/`.txt` now correctly marked `⏭️ already downloaded`; `.md`-only stubs re-attempt download unless `reason: unavailable`; `✅ downloaded` gated on confirmed `.pdf`/`.txt` write; summary counter labelled `✅ [n] downloaded (PDF/text)` + new `⏭️ [n] unavailable (metadata cached)` bucket
- **Scholar agent: search coverage fixes** — Semantic Scholar 429 rate-limit → 3 s wait + retry → falls back to CrossRef/arXiv with inline warning; PubMed query-overlap detection auto-generates 2–3 diversified queries when < 15 unique results or > 80% overlap; arXiv keyword fallback added when bioRxiv returns 0 results; mandatory per-source coverage summary table printed before results; any ⚠️/❌ row also surfaces as an inline warning block

## 0.2.5

- **`/poster`** — generate a LaTeX conference poster from project memory; five templates (A0/A1 portrait, A0 landscape, 90×120 cm, 48×36 in); QR code via `qrcode` package; iterative `poster-critic` review loop (up to 3 cycles) before `.tex` is saved
- **New `poster-critic` agent** — five-area poster auditor (content, layout, scientific communication, QR code, LaTeX correctness); returns `[STATUS: APPROVED]`/`[STATUS: REJECTED]` with specific fixes; never rewrites content
- **New `neuroflow:phase-poster` skill** — full LaTeX template catalogue, template selection guide, content extraction from `.neuroflow/`, QR code blocks, compilation instructions

## 0.2.4

- **Sentinel Check 3b** — sentinel now validates that `.claude-plugin/marketplace.json` version matches `plugin.json`; marketplace version was silently stuck at `0.1.0`
- **Hardened release checklist** — both dev agents now require `docs/changelog.md` entry, one-liner review, and `marketplace.json` bump on every release; `neuroflow-develop/SKILL.md` synced to match `neuroflow-developer.md` (was missing `mkdocs.yml` and sentinel-dev steps)
- **Internal consistency fixes** — dead `neuroflow:scholar` ref in `phase-paper` fixed; `/hive` docs page created; `neuroflow-developer.md` and `orchestrator` synced to full repo structure (22 phases, all 4 workflows)

## 0.2.3

- **Scholar downloads resume and retry** — the [`scholar`](agents/scholar.md) agent skips papers already in `.neuroflow/ideation/papers/`, so an interrupted run can be repeated without duplicate work; each download tries Unpaywall → PubMed Central → bioRxiv → the journal's open-access page in turn, and the whole chain once more after 2 seconds; a transient failure (`⚠️ failed`, listed by name to retry) is reported apart from a paper with no open-access copy (`❌ unavailable`)
- **`/paper-write` and `/paper-review` removed** — superseded by [`/paper`](commands/paper.md), which covers the full write→critique loop
- **New [`/review`](commands/review.md)** — for when you referee a colleague's paper: a structured referee report calibrated to the target journal, delegating to `neuroflow:review-neuro`; with a `review` agent (since removed) and the [`neuroflow:phase-review`](skills/phase-review/SKILL.md) skill

## 0.2.2

- **Unified [`/paper`](commands/paper.md)** — writing and reviewing a manuscript in one command and phase: every section draft goes through a `paper-writer` → `paper-critic` loop (up to 3 iterations per section) and reaches disk only with the critic's approval or the user's explicit acceptance
- **New [`paper-writer`](agents/paper-writer.md) and [`paper-critic`](agents/paper-critic.md) agents** — the writer drafts section by section from upstream project memory; the critic applies the full six-area `neuroflow:review-neuro` methodology to every draft, with zero tolerance for overclaims, statistical errors and underreported methods
- **New [`neuroflow:phase-paper`](skills/phase-paper/SKILL.md) skill** — journal recommendation, the write→critique loop protocol, critic standards and output paths for the paper phase

## 0.2.1

- **ASCII welcome logo in [`/neuroflow`](commands/neuroflow.md)** — the entry command greets with an ASCII logo of "neuroflow", the current version and the tagline *agentic neuroscience research, from hypothesis to publication*, followed by one of three one-liners

## 0.2.0

- **Consent before issue reports** — project setup in [`/neuroflow`](commands/neuroflow.md) asks whether anonymous issue reports to the developers are allowed and saves the answer as `auto_issue_reporting: yes/no` in `project_config.md`; `auto-issue` files issues only when the answer was yes, and a missing or `no` value suppresses all automatic filing
- **Cognitive probe on the home page** (since retired) — a simple static self-assessment block replaced the separate probe page

## 0.1.9

- **Worker-critic loop** — new `orchestrator` and `critic` agents (both since removed; the protocol lives on in the skill below) ran up to 3 revision cycles on any phase output: the orchestrator picked the worker for the active phase from `project_config.md` among the 15 phase agents of the time (18 phases covered), and the critic returned `[STATUS: APPROVED]` or `[STATUS: REJECTED]` with specific, actionable feedback; without approval the loop stopped cleanly with a logged critique
- **New [`neuroflow:worker-critic`](skills/worker-critic/SKILL.md) skill** — the loop protocol: worker modes (initial draft, revision), rubric construction, the critic's output format and `critic-log.md` state tracking

## 0.1.8

- **New [`/slideshow`](commands/slideshow.md)** — build a structured slide deck from selected project phases, figures and key findings, with the [`neuroflow:phase-slideshow`](skills/phase-slideshow/SKILL.md) skill: audience calibration, slide-count heuristics, and Markdown/reveal.js and outline formats
- **New [`/flowie`](commands/flowie.md)** — a personal identity layer: link a private GitHub repository that holds your research profile (stances, writing style, methodological preferences, key beliefs), which Claude reads to personalise every phase (`--init`, `--sync`, `--link`, `--view`, `--identify`); with the [`neuroflow:phase-flowie`](skills/phase-flowie/SKILL.md) skill (how to read and apply the profile, write rules, a sync protocol that always pulls before it pushes and shows conflicts side by side) and the [`flowie`](agents/flowie.md) agent, which reads the profile at session start and never exposes it in external-facing outputs
- **Target journal in [`/neuroflow`](commands/neuroflow.md)** — when `paper-write` or `paper-review` is the active or a recommended phase and no target journal is set, neuroflow offers a recommendation: a `scholar` search of PubMed and bioRxiv, 3–5 candidate journals ranked by scope, paper type, open-access requirements, length and prestige versus speed, and the chosen journal saved to `project_config.md`; the same workflow in the `neuroflow:phase-paper-write` skill (since replaced by `neuroflow:phase-paper`), with recency (past 3 years) and recurrence (≥3 of the top 20 results) thresholds
- **[`/output`](commands/output.md)** — `/export` renamed, because Claude Code's built-in `/export` exports conversations; the behaviour is unchanged and the skill is renamed to [`neuroflow:phase-output`](skills/phase-output/SKILL.md)
- **[`/grant-proposal`](commands/grant-proposal.md) rebuilt** — discovers ideation outputs, fetches funder calls from URLs, knows the review criteria of major international and national funders, and drafts section by section with word-count tracking and quality checklists; the `grant-proposal` agent (since removed) parsed funder calls and drafted a neuroscience-aware Approach (EEG, fMRI, iEEG, eye tracking) with a confirmation after each section; the [`neuroflow:phase-grant-proposal`](skills/phase-grant-proposal/SKILL.md) skill gains a funder knowledge base, a review-criteria alignment table, a guide to common fatal weaknesses, and power-analysis and preprocessing standards
- **`auto-issue` skill** (since removed; neuroflow-core took over its passive issue monitoring in 0.2.4) — passive frustration detection that filed a GitHub issue when the user expressed dissatisfaction, without being invoked
- **Cognitive Development Probe** (since retired) — an interactive page of seven neuroscience-inspired yes/no questions (prediction error, model update, uncertainty, decision monitoring, self-model, global integration, subjective experience), the last one locked until the first six were yes, with status colours, a "Cognitive Level" progress bar and a read-only section in which the model answered each question about itself
- **Homepage quotes** (since retired with the redesigned site in 0.2.22) — four new quotes in the hero rotation (`overrides/main.html`): *I will jump to version 1.0.0 once I manage to publish the first paper*, *We will probably be the first ones to understand the brain.*, *When I said we, I meant you as well, are you in?* and *Can you collect some brain data for me?*

## 0.1.7

- **`neuroflow-developer` agent** (since removed; the plugin targets Claude Code only) — a GitHub agent for developing and maintaining the plugin: it merged the `neuroflow-core` lifecycle rules and the `neuroflow-develop` guidance into one repo-aware agent and read the live state of every skill, command, agent and hook at the start of each session

## 0.1.6

- **Neuroflow Mind** (since retired with the redesigned site in 0.2.22) — an interactive mind map of every command, skill, agent and concept as a force-directed graph with phase clusters; a click on a node showed its connections and opened its docs, and coloured dots on each node showed its domain tags (EEG, fMRI, brain-sim, stats, ML, writing, literature, memory, code, human); reached from the homepage hero
- **Visual phase map in [`/phase`](commands/phase.md)** — four markers: `◉` current phase, `●` visited (its `.neuroflow/{phase}/` folder exists), `→` recommended after the interview, `○` not started; active and visited phases come first, then the recommended ones, then the rest
- **Phase sequence in [`/neuroflow`](commands/neuroflow.md)** — after the interview (new Step 2b) neuroflow suggests an ordered sequence of phases for the project and saves it as `recommended_phases` in `project_config.md`, which `/phase` reads for its `→` markers
- **Phase outlook in [`/interview`](commands/interview.md)** — at the end of an interview session, neuroflow suggests the phases most relevant to where the user is heading, from the session and the project config
- **Version bump** — website and header badge updated to v0.1.6
- **Mind map back button** — the back-to-docs link on the mind map page is now a full-width prominent button, easy to spot and reach
- **Fails-folder awareness in core** — `neuroflow:neuroflow-core` now instructs every command to read `.neuroflow/fails/` at start (if it exists), so past logged dissatisfaction is always in context
- **Removed AI-slop feature claims** — the "Built-in stats auditing" feature card removed from the homepage; the `/data-analyze` command page and skill are unchanged

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

## 0.1.4

- **`/quiz`** — neuroscience quiz command with three modes: flashcards (saveable A4 printable layout), pub quiz (with neuroscience-themed house rules), and rapid-fire throw questions (default)
- **`/fails`** — log dissatisfaction (core behavior, science quality, or interaction UX) to `.neuroflow/fails/`, with optional one-click GitHub issue reporting; new `neuroflow:phase-fails` skill
- **`/idk`** — personal support companion for when you're burned out, overwhelmed, or need to think out loud; breaks down impossible task lists and lets you decompress mid-research
- **`/interview`** — interview preparation from either side of the table; generates tailored questions grounded in your research context, runs practice Q&A, and optionally evaluates readiness
- **Brain simulation commands** — `/brain-build`, `/brain-optimize`, and `/brain-run` for assembling, fitting, and running computational brain models (NEURON, Brian2, NetPyNE, NEST, tvb-library); three new phase skills: `neuroflow:phase-brain-build`, `neuroflow:phase-brain-optimize`, `neuroflow:phase-brain-run`
- **`neuroflow:phase-quiz`** — phase skill for `/quiz` covering mode behaviour, question quality standards, and mode-specific workflow

## 0.1.3

- **`/start` renamed to `/neuroflow`** — the main entry point is now `/neuroflow` (run as `/neuroflow:neuroflow`); all command references and documentation updated
- **Behavioral improvements** — end-of-command lifecycle hardened based on real-session feedback: continuous session logging at each milestone, live `flow.md` updates on every file write, phase transition prompts when outputs outpace the active phase, utility scripts routed to `.neuroflow/{phase}/tools/` instead of the project root, explicit `.claude/CLAUDE.md` creation in the project root, `decisions.md` removed from scaffold (superseded by `reasoning/general.json`), `.neuroflow/` now explicitly restricted to workflow state only

## 0.1.2

- **12 phase skills** — `neuroflow:phase-ideation` through `neuroflow:phase-write-report`, each loaded automatically by its corresponding command to orient agent approach, relevant skills, and workflow hints

## 0.1.1

- **Full research pipeline** — 15 commands from `/neuroflow` through `/paper-review`, each writing to `.neuroflow/` project memory
- **`neuroflow:neuroflow-core`** — shared lifecycle and `.neuroflow/` folder spec that every command and agent follows; commands now automatically append significant decisions to `.neuroflow/reasoning/{phase}.json`
- **`scholar`**, **`sentinel`**, **`sentinel-dev`** agents
- `sentinel` checks plugin version against `project_config.md` and flags when the plugin has been updated; both sentinels clear their report to "All clear" after fixing issues
- `project_config.md` now tracks `plugin_version` — kept in sync with `plugin.json` by `/neuroflow` and `/sentinel`
- MCP servers declared in `plugin.json`: PubMed, bioRxiv, Miro, Context7

## 0.1.0

- Initial release
