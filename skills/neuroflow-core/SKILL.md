---
name: neuroflow-core
description: Core rules and lifecycle for all neuroflow commands and agents. Read this whenever running any neuroflow command to understand the .neuroflow/ folder structure and the required behaviour at the start and end of every command.
user-invocable: false
---

# neuroflow-core

Defines the shared structure and lifecycle that every neuroflow command and agent must follow.

## Global ~/.neuroflow/ structure

`~/.neuroflow/` (Unix/Mac) or `%USERPROFILE%\.neuroflow\` (Windows) is the **user-level** neuroflow home. It lives on the machine, not inside any project repo. It is never committed anywhere.

```
~/.neuroflow/
├── user.yaml                        ← personal layer: flowie_handle, preferences, consents (see "Personal layer")
├── integrations.json                ← global integration settings, no secrets (/setup stores no token or key) — device-wide, never inside any repo
├── private/                         ← local-only personal files that never sync (e.g. interview notes about candidates); not a git repo
├── local-projects.json              ← machine-local project registry (flowie project name → local folder), written by /flowie --link, never synced
├── boards/                          ← machine-local cache of other repositories' task boards (shallow, sparse clones holding only .neuroflow/tasks/), written by projects.py view/refresh, never synced
├── workbench/                       ← machine-local state of your claude.ai workbench (Workbench snapshot): pending.json, ledger.json — never synced
├── flowie-sync.log                  ← one line per failed flowie auto-sync, plus one per sync the neuroflow mod attempts (its `synced` lines are no failure), machine-local, cleared by /flowie --sync
├── flowie/                          ← ONE global clone of github.com/{handle}/flowie
│   ├── .gitignore                   ← integrations.json
│   ├── profile.md
│   ├── ideas.md
│   ├── ideas-inbox.md
│   ├── sync.json
│   ├── workbench.json               ← your claude.ai workbench record (Workbench snapshot), when you set one up
│   ├── integrations.json            ← NON-SECRET settings only (custom LLM provider/base_url/model — never api_key); gitignored, stays on this machine
│   ├── projects/
│   ├── tasks/
│   ├── notes/
│   ├── meetings/
│   ├── wellbeing/
│   └── wiki/
└── hives/
    └── {org-repo}/                  ← a git clone of the hive repo (shallow is fine) — one per hive membership
        ├── hive.md
        ├── members.md
        ├── ideas.md
        └── .git/neuroflow-sync.json ← this member's state — inside git's own folder: never tracked, never pushed
```

**Key rules:**
- `~/.neuroflow/flowie/` is a git repo (`.git/` inside) — cloned once, shared across all projects
- `~/.neuroflow/hives/{org-repo}/` is a git clone of the hive repo (shallow is fine) — one per hive the user belongs to
- Integration settings live in `~/.neuroflow/integrations.json` (global, device-wide; non-secret — `/setup` never stores a token or key), with an optional per-project override at `.neuroflow/integrations.json` (gitignored, excluded from `/output` exports). `~/.neuroflow/flowie/integrations.json` carries **non-secret** settings only (custom LLM provider/base_url/model/proxy_port), kept on this machine: it is gitignored in the flowie repo and never committed (the auto-sync hook skips it) — `api_key` never enters the flowie repo
- Neither `flowie/` nor `hive/` ever appears inside a project's `.neuroflow/`
- `user.yaml`, `private/`, `local-projects.json`, `boards/`, `workbench/` and `flowie-sync.log` are local only: never copied into a project, pushed or exported

---

## .neuroflow/ folder

`.neuroflow/` is project memory. It lives at the root of the user's project repo.

<!-- nf-rule: MEMORY-PURITY -->
**Rule: `.neuroflow/` root contains only the files and folders explicitly listed in the tables below — nothing else.** Never place any file or folder directly in `.neuroflow/` unless it appears in the "Root files" or "Root folders" tables. All workflow content belongs in the appropriate phase subfolder (`.neuroflow/{phase}/`). External deliverables, polished reports, or any user-facing outputs go in the project root or `report/`.

### Root files

| File | Purpose |
|---|---|
| `project_config.md` | Project facts in a YAML frontmatter (`active_phase`, `recommended_phases`, `collaborators`, …) followed by free-markdown notes (research question, modality, tools, output paths). Read this first. Contract: **project_config.md — the config contract** below. |
| `flow.md` | Index of all subfolders: one row per folder with name, description, date of last change. |
| `objectives.md` | Project objectives/aims — one numbered sentence per objective. Cross-phase cornerstone: **read at the start of every command** (if it exists), keep objectives in context throughout the session, and explicitly check coverage before saving any major section. Written during `/grant-proposal` interview or `/ideation`. |
| `sentinel.md` | Sentinel's last audit report. If all clear: last run date + "all clear". |
| `timeline.md` | Milestones and deadlines — conference/submission deadlines, ethics approval expiry, funder reporting dates. Created by `/neuroflow` (interview), rendered by `/phase`, read by `/meeting` for agenda preparation. |
| `journal-preferences.md` | Optional — the user's target-journal preferences, written during `/neuroflow` or `/ideation` journal recommendation. |
| `integrations.json` | Optional — per-project override of the integration settings in `~/.neuroflow/integrations.json`, written by `/setup`. Local tier: gitignored, never exported (**Sharing tiers**). |

#### project_config.md — the config contract

`project_config.md` opens with a YAML frontmatter block of machine-readable project facts, followed by free markdown for human notes (description, research question, modality, tools, institution, the `## Output paths` table).

```yaml
---
nf_schema: 1                      # integer; bumped only on a breaking format change
project_name: Oddball EEG study
active_phase: data-analyze        # canonical phase id (Phase taxonomy); `setup` while /neuroflow runs
default_mode: critic              # optional team default: teacher | executor | critic
target_journal: eLife             # optional
recommended_phases: [ideation, preregistration, experiment, data, data-analyze, paper]
raw_roots: [sourcedata/]          # optional: read-only raw-data folders (relative to project root)
paper_auto: off                   # optional: on | off (/paper --auto)
hive_repo: owner/repo             # optional: GitHub org/repo of the team hive
ethics: not-applicable            # optional: no approval tracked here (public de-identified data, simulations); silences the ETHICS-GATE, PARTICIPANT-ROUTE and sentinel S4; set only by the person — see /ethics
wiki_capture: allow               # optional: allow | forbid — forbid stops all wiki capture in this project (e.g. confidential work); absent means allow — see /wiki
workbench_mirror: allow           # optional: allow | allow-names | forbid — the team's opt-in to members mirroring this project into their own private claude.ai workbench; absent means not mirrored (Workbench snapshot)
plugin_version: 0.2.22            # the neuroflow version the project was last brought up to date to; only the scaffold and /neuroflow:migrate write it
---
```

| Optional list key | Entries | Used by |
|---|---|---|
| `collaborators` | `name`, `email`, `handle` (GitHub) per person — replaces legacy `team.md` | `/meeting` invites, `/tasks` assignees |
| `flowie_profiles` | `handle`, `repo` (`{handle}/flowie`); first entry = project owner, further entries = collaborators who ran `/flowie --link` | `/phase` registry sync |

- **Read** facts from the frontmatter. Older projects use a legacy dialect — `key: value` lines without frontmatter, bold labels (`**Phase:** x`), or a mix. Read them as they are, never rewrite them silently, and offer `/neuroflow:migrate`, which converts a project idempotently, shows the plan and asks before writing.
- **Schema guard:** if `nf_schema` is greater than 1, a newer neuroflow wrote the file. Do not write it; say so and suggest updating the plugin.
- **Write** one key in place (e.g. `active_phase`) and keep the YAML valid. Human notes stay in the body.
- **`plugin_version`** is the neuroflow version the project was last brought up to date to. Only the scaffold (a new project) and `/neuroflow:migrate` (once it has brought the project up to date) write it, and never to a lower version; every other writer leaves it as it is. Raised anywhere else, it silences the version notice (**Command lifecycle**) while the formats stay old; written by a teammate on an older plugin, it would go down.

#### Personal layer — `~/.neuroflow/user.yaml`

Personal preferences and consents are not project facts and are never committed: they live in `~/.neuroflow/user.yaml` (per person, outside every repo), never in `project_config.md`.

```yaml
flowie_handle: alice              # written by /setup
flowie_repo: alice/flowie
hives: [example-lab/hive]
name: Alice Example               # researcher name
writing_style: plain, active voice
auto_issue_reporting: no          # consent: yes | no — absent means no
default_mode: critic              # optional: overrides the project's team default for this person
zotero: no                        # optional: yes | no — whether the person uses Zotero, asked once by /ideation
wiki_auto: off                    # optional: ask | off — queue wiki cards from this person's sessions for review (/wiki --auto); absent means off
workbench: on                     # optional: on | off — this person's own claude.ai workbench (/dashboard --web); absent means off
workbench_levels: ["flowie", "hive+example-lab+hive"]   # optional: the levels this person mirrors there (keys: Workbench snapshot)
workbench_machine: laptop         # optional: a name this person gives this machine, shown on every level it exports
pii_config: ~/keys/pii_scan.json  # optional: this person's pii_scan.py config (id_patterns, roster), kept outside every repository; every workbench export applies it
```

- Consent is read **only** from this file. An `auto_issue_reporting` value in a project file is a legacy leftover: ignore it and offer `/neuroflow:migrate`, which moves personal fields here after asking.
- Per-person notification or wellbeing settings live here too.
- `hives:` names the team hives the person joined, each as `org/repo` (inline, as above, or one `- org/repo` per line); its clone is `~/.neuroflow/hives/{org-repo}/`. An entry may instead be a map — `repo: org/repo` and `local: {path of the clone}` — for a clone whose folder has another name: the last folder of `local` is then the hive's folder. Readers take both forms; a writer keeps the form the file uses.
- Team defaults the collaborators agree on (e.g. `default_mode`) may stay in `project_config.md`; a value here overrides them for this person only.
- Merge, never replace: when writing a key, keep every other line of the file.
- The workbench keys — `workbench`, `workbench_levels`, `workbench_index_only`, `workbench_machine`, `workbench_account`, and `workbench_records` while no flowie is linked — are this person's own; **Workbench snapshot** says what each holds. So is `pii_config`, the path of their pii_scan.py config (ID patterns, a participant roster built with `pii_scan.py --build-roster`), which every workbench export applies. A project's or hive's consent is a different key, `workbench_mirror`, in the shared file.

### Root folders

| Folder | Purpose |
|---|---|
| `sessions/` | One `.md` per day (`YYYY-MM-DD.md`). Local tier — the scaffold gitignores it (**Sharing tiers**). |
| `reasoning/` | Per-phase decision logs in JSON Lines (`{phase}.jsonl`, `general.jsonl`) — see **Reasoning log**. Has its own `flow.md`. Created by the scaffold. |
| `ethics/` | IRB documents, consent forms. `status.md` frontmatter holds the approval state (**Integrity markers**). |
| `preregistration/` | Pre-registration documents (OSF, AsPredicted). `status.md` frontmatter holds the freeze state; `deviations.md` is append-only (**Integrity markers**). |
| `finance/` | Grant documents, expense tracking. |
| `fails/` | Dissatisfaction log — three fixed files: `core.md` (plugin behavior problems), `science.md` (scientific quality problems), `ux.md` (interaction quality problems). Created on first `/fails` run. |
| `output/` | Output log — one `.md` per export run recording scope, format, destination, and excluded files. Created on first `/output` run. |
| `tasks/` | Project-level Kanban task board — one file per task at `tasks/{column}/{slug}.md` (format: `/tasks`; git-tracked, shared with collaborators). Owned by `/tasks` — `/flowie --tasks --level project`, `/meeting` action items, and `/hive` delegate to its spec. Created by the scaffold. |
| `meetings/` | Meeting files — agendas, notes, action items. Written by `/meeting`. Created on first meeting. |
| `wiki/` | Project-level shared knowledge base (git-tracked; its `.pending/` review queue is local tier). Owned by `/wiki` at `level: project`. The scaffold creates the skeleton; `/wiki --schema` or the first ingest initialises it. |
| `{phase}/` | One subfolder per pipeline command (e.g. `ideation/`, `experiment/`, `data/`). Each has its own `flow.md` and at least one `.md` memory file written by the command. |

**Rule: only command names may be used as phase subfolder names.** Skills must never create their own named subfolders inside `.neuroflow/`. All skill memory must be written to the active command's phase subfolder (`.neuroflow/{phase}/`). Creating a subfolder named after a skill (e.g. `.neuroflow/review-neuro/`) is a structural error.

### flow.md format

`flow.md` is a pure index table — one row per file or folder, nothing else. Never write narrative content, mappings, notes, or cross-references directly into `flow.md`. Add a dedicated `.md` file to the phase subfolder and list it as a row instead.

Every subfolder must contain a `flow.md` with this format:

```
| File / Folder | Description | Last changed |
|---|---|---|
| filename.md | One sentence. | YYYY-MM-DD |
```

Phase subfolders that produce external outputs must also include an `output_path` line at the top:

```
output_path: ../scripts/analysis
| File / Folder | Description | Last changed |
|---|---|---|
| analysis-plan.md | Analysis plan and statistical approach. | YYYY-MM-DD |
```

`output_path` is relative to the repo root and points to where this phase writes code, results, figures, or manuscripts. Set by `/neuroflow` — never write it manually unless `/neuroflow` was not run.

---

## Memory vs outputs

**`.neuroflow/` holds memory and internal tooling only.** Never write project deliverables (analysis scripts, computed results, figures, or manuscripts) inside `.neuroflow/`. All project outputs go to the phase `output_path`. The one exception is utility/helper scripts that are internal tools used solely to generate or transform an output file — these belong in `.neuroflow/{phase}/tools/`.

| What it is | Where it goes |
|---|---|
| Plans, QC reports, summaries, configs | `.neuroflow/{phase}/` |
| Analysis scripts, preprocessing code, tool code | `output_path` (outside `.neuroflow/`) |
| Computed results, figures, tables | `output_path` (outside `.neuroflow/`) |
| Manuscript drafts, grant documents | `output_path` (outside `.neuroflow/`) |
| Paradigm scripts | `output_path` (outside `.neuroflow/`) |
| Utility/helper script (internal tool, e.g. markdown→docx converter) | `.neuroflow/{phase}/tools/` |

**Utility scripts vs project deliverables:**

| Script type | Where it goes |
|---|---|
| Project deliverable (analysis pipeline, preprocessing script, paradigm) | `output_path` or `scripts/` — always outside `.neuroflow/` |
| Utility/helper script that produces an output (e.g. markdown→docx converter, report renderer) | `.neuroflow/{phase}/tools/` |

Never place utility scripts in the project root. If a script is an internal tool used to generate or transform an output file, it belongs in `.neuroflow/{phase}/tools/` — not alongside the project's main code. Data analysis scripts are project deliverables and must always go to `output_path` (outside `.neuroflow/`).

Default output paths (used when the repo has no existing structure):

| Phase | Default output_path |
|---|---|
| `experiment` | `paradigm/` |
| `tool-build` | `tools/` |
| `tool-validate` | `tools/tests/` (test scripts are deliverables — they live with the tool, not in memory) |
| `data-preprocess` | `scripts/preprocessing/` |
| `data-analyze` | `scripts/analysis/` (code) + `results/` (outputs) + `figures/` |
| `paper` | `manuscript/` |
| `poster` | `poster/` (the `.tex` and compiled PDF are deliverables; critic logs stay in `.neuroflow/poster/`) |
| `write-report` | `report/` (reports are user-facing deliverables) |
| `slideshow` (utility) | `slides/` (decks are deliverables; outlines/notes stay in `.neuroflow/slideshow/`) |
| `review` | `.neuroflow/review/` |
| `grant-proposal` | `.neuroflow/grant-proposal/` |

---

## Shared formats

Every command, agent, script and the neuroflow mod uses these formats. Other files point here instead of restating them.

### Reasoning log

`.neuroflow/reasoning/{phase}.jsonl` (and `general.jsonl` for project-level decisions) is JSON Lines: one JSON object per line, append-only, never rewritten or reordered.

```json
{"statement": "Use FDR (BH) across electrodes", "source": "command:data-analyze | 2026-10-07", "reasoning": "Cluster tests would blur the per-electrode effects the hypothesis names; Bonferroni is too strict for 64 correlated channels", "at": "2026-10-07T12:00:00Z"}
```

- `statement` — what was decided, one sentence; `source` — `command:<name> | YYYY-MM-DD`; `reasoning` — why, naming the alternatives that lost; `at` — ISO 8601 UTC time.
- Optional: `"drafted_by": "model"` or `"mod"`, and `"approved_by": "person"` when a person approved a drafted entry.
- Add each entry as a new last line. Legacy `{phase}.json` arrays stay readable; `/neuroflow:migrate` converts them (one array element → one line; the old file is kept as `.json.bak`).

### Integrity markers

Integrity state lives in the YAML frontmatter of a `status.md` in the phase folder it belongs to — one place each, human-readable, merge-friendly.

`.neuroflow/preregistration/status.md`
```yaml
---
nf_schema: 1
status: frozen                    # draft | frozen
frozen_at: 2026-10-01T10:00:00Z
files:                            # project-relative path → sha256 of the frozen file
  .neuroflow/preregistration/prereg-osf-2026-10-01.md: 3f5a…
registry: OSF                     # optional
doi: 10.17605/OSF.IO/XXXXX        # optional
planned_n: 48                     # optional (sample size the prereg commits to)
set_by: person                    # person | model
set_at: 2026-10-01T10:00:00Z
---
```

`.neuroflow/ethics/status.md` (owned by `/ethics`)
```yaml
---
nf_schema: 1
status: approved                  # none | pending | approved | expired | withdrawn
approval_id: EC-2026-014          # optional
expires: 2027-06-30               # optional ISO date
ai_processing: none               # none | pseudonymised | identifiable — whether the AI model may read participant data
set_by: person                    # person | model
set_at: 2026-09-12T09:00:00Z
---
```

<!-- nf-rule: INTEGRITY-MARKER -->
- `set_by: person` means a person set the value: a press in the neuroflow mod, or an explicit confirmation in the conversation ("yes, freeze it") right before the write. Never write `set_by: person` without that confirmation in the same turn. Treat `frozen` or `approved` with `set_by: model` as not set.
- A frozen preregistration file starts with a plain-text banner, so collaborators without the mod see it: `> FROZEN 2026-10-01 — sha256 3f5a… — do not edit; record changes in deviations.md`. `deviations.md` is append-only; unfreezing is a person's action only and is itself logged there. The freeze workflow lives in `/preregistration`.

<!-- nf-rule: PARTICIPANT-ROUTE -->
**Participant data:** the model reads participant-level data (raw recordings, `participants.tsv`, consent forms, anything identifying) only as `ai_processing` allows — `none`: never; `pseudonymised`: pseudonymised data only; `identifiable`: as approved. A missing field, or one with `set_by: model`, counts as `none`. A project marked `ethics: not-applicable` (public de-identified data, simulations) declares no participant data to protect: this rule, and the mod's PARTICIPANT-ROUTE guard, do not apply there. Only the person sets that flag: the model may suggest it and writes it only after the person's explicit yes in that turn, with a line in `reasoning/general.jsonl` — never on its own judgement. `/ethics` records the field and details what each value allows; when reading is not allowed, write the script, let the person run it, and work from its aggregate output.

### Merge safety

`.neuroflow/` travels through git, so append-only files must merge cleanly. The scaffold (and `/neuroflow:migrate`) adds these lines to the project's `.gitattributes`:

```
.neuroflow/reasoning/*.jsonl merge=union
.neuroflow/sessions/*.md merge=union
.neuroflow/fails/*.md merge=union
.neuroflow/preregistration/deviations.md merge=union
.neuroflow/data-analyze/multiverse.md merge=union
```

- Append-only files never carry running totals or "last updated" lines that every append rewrites.
- A `flow.md` is a derived index: after a merge conflict in one, rebuild its rows from the folder contents instead of hand-merging them.
- Conflict tripwire: `/sentinel` and the doctor script report any `<<<<<<<` / `>>>>>>>` markers under `.neuroflow/`. Resolve them before writing to that file.

### Sharing tiers

| Tier | What | Rule |
|---|---|---|
| `local` | `~/.neuroflow/integrations.json`, `~/.neuroflow/user.yaml`, `~/.neuroflow/local-projects.json`, `~/.neuroflow/boards/`, `~/.neuroflow/workbench/`, `~/.neuroflow/flowie-sync.log`, `.neuroflow/integrations.json`, `.neuroflow/review/` (manuscripts under confidential peer review), `.neuroflow/paper/xray-*` (sentence-level critique of an unpublished manuscript), `.neuroflow/wiki/.pending/` (wiki capture cards awaiting review), `.neuroflow/sessions/`, `.neuroflow/flowie/` | Never committed (scaffold `.gitignore`), never exported, never uploaded. |
| `team` | everything else under `.neuroflow/` | Committed to the project repo; visible to collaborators. |
| `public` | what `/output`, `/hive` share, NotebookLM, slides, posters and papers send outside | Only after the person confirms what leaves. Never includes `local` paths, `fails/`, `finance/`, or participant-identifying `ethics/` content. |
| `workbench` | the levels a person mirrors into their own owner-only claude.ai workbench (**Workbench snapshot**) | Uploaded only after a one-line preview and the person's yes in that turn; hive and project data only with the team's `workbench_mirror` opt-in; never `local` paths, `fails/`, `finance/`, reasoning logs, the flowie's profile or wellbeing, wiki `raw/`, or an email address. |

The scaffold (and `/neuroflow:migrate`) adds these lines to the project's `.gitignore`:

```
.neuroflow/sessions/
.neuroflow/review/
.neuroflow/integrations.json
.neuroflow/flowie/
.neuroflow/paper/xray-*
.neuroflow/wiki/.pending/
```

<!-- nf-rule: EGRESS-CONFIRM -->
**Egress:** every outbound data movement — uploads, pushes to shared remotes, exports, opening an issue URL — needs the person's explicit confirmation in the turn it happens. Nothing leaves "automatically", with one exception: the person's own private flowie repository is a sync target they set up explicitly, so the flowie auto-sync hook commits the file Claude wrote there, pulls with rebase and pushes (`/flowie` → Git operations pattern). Shared targets — a hive, exports, NotebookLM, public repositories — always need the confirmation. The person's own claude.ai workbench is no exception: its first publish, every refresh and every outcome write-back is previewed in one line and uploaded only after their yes in that turn — nothing on a timer, nothing at the end of another command (**Workbench snapshot**).

### Project registry — one card per project

A research project is described once. Its **card** — an entry in a `projects/projects.json` and its `projects/{id}.md` — lives where its readers are:

- **a team project** (anyone else works on it): in the hive of that team, `~/.neuroflow/hives/{org-repo}/projects/` — the hive the project's `hive_repo` names, when it names one;
- **a personal project**: in the flowie, `~/.neuroflow/flowie/projects/`.

The card holds the project's facts: `id`, `description`, `repos` (remote URLs only — a folder on one machine belongs in `~/.neuroflow/local-projects.json`), `current_phase`, `visited_phases`, `status` (`active` | `paused` | `complete`). The other level holds at most a **pointer** — `{"id": "{id}", "ref": "hive:{org}/{repo}"}` in the flowie's `projects.json`, with a `projects/{id}.md` that keeps only the person's own notes — and never a copy of a card field: a copy is what drifts.

- **Reading.** A project's status, phase or repos come from its card; a flowie pointer leads to the hive card (the local clone, pulled first). `python <neuroflow-core skill base dir>/scripts/projects.py list` lists every card and pointer; exit `0`, `2` on a usage error.
- **Writing — propagation.** Every change to a project's facts is written on its card, wherever the change starts: the phase sync after `/phase`, `/flowie --projects`, `/hive --projects`. On a hive card: commit by path, show the diff, and push only after the person's yes in that turn (`neuroflow:phase-hive` → Pushing to the hive). Never write the change into a flowie copy instead.
- **Registering.** `/flowie --projects --add` and `/hive --projects --add` ask whether the project is the person's own or a team's (which hive), write the card there, and for a team project a pointer in the flowie.
- **Two cards for one project** (registries written before this rule): `/neuroflow:migrate` folds them with `python <neuroflow-core skill base dir>/scripts/projects.py fold` — the hive card stays, the flowie entry becomes a pointer, a field that differs keeps the value the person picks, and the hive is written only after their yes. A project with cards in two hives is reported, never folded.
- **Checks.** `python <neuroflow-core skill base dir>/scripts/projects.py check` reports two cards for one project, pointers that lead nowhere or carry copies, `blocked_by` entries that name no task on their board, and open tasks whose `project:` names no registered project (exit `0` clean, `1` findings, `2` error); `/sentinel` and `/neuroflow:migrate` run it.
- **Tasks.** The boards stay three (`/tasks` → Levels) and a task's `project:` is the card's `id` at every level; where a task belongs is `/tasks` → Placement. `python <neuroflow-core skill base dir>/scripts/projects.py view --project {id}` reads one project's open tasks at every level — the flowie, each hive, this repository's board and the boards of the card's other repositories, through a shallow, sparse cache in `~/.neuroflow/boards/` (local tier) that is refreshed from their remotes each time; `--no-remote` reads the cache as it is.

### Workbench snapshot

A person may keep one private claude.ai page — the **workbench** — over their own levels: a tab for their flowie, each hive they joined and each project they export from that project, each drawn the same way (a Kanban with drag and drop and keyboard moves, the project list, the wiki, the level's panel). It is a derived mirror plus an outbox of clicks. **Git stays the only store**: the page never writes a task file, and what is on it can always be rebuilt from git. `/dashboard --web` publishes and refreshes it; `/tasks --apply-web` applies its clicks; both run `python <neuroflow-core skill base dir>/scripts/workbench.py`, the one executable home of every rule below (`--help` lists its subcommands). The page itself is `assets/workbench/workbench.html` with its logic in `workbench.mjs`, both in this skill.

**Who decides what is mirrored.**

| Level | The person (`~/.neuroflow/user.yaml`) | The team (shared file) |
|---|---|---|
| flowie | `workbench: on` and the key in `workbench_levels` | — (it is theirs) |
| hive | the same | `workbench_mirror` in the frontmatter of the hive's `hive.md` |
| project | the same | `workbench_mirror` in the `project_config.md` frontmatter |

`workbench_mirror` is `allow`, `allow-names` (also the names and roles the roster lists — never an email address) or `forbid`; **absent means not mirrored**. Only the team's own decision writes it (a commit the team can see), never `/dashboard --web` on its own. `workbench.py` reads it from the working tree and from the clone's upstream as last fetched (the export fetches first) and follows the stricter of the two: a clone that is behind cannot keep mirroring what the team stopped, and a value nobody pushed cannot start it. `workbench_index_only` (user.yaml) lists levels whose wiki goes up as an index without page bodies.

**Level keys** name a level the same way on every machine, in the store's segment characters and as a valid file name everywhere (an `ArtifactData` listing saved with `out_dir` names files after them): `flowie`; `hive+{org}+{repo}` from the hive clone's `origin`; `project+{card id}` (lower case, other characters escaped as `~hh`, a short hash added when the id has capitals) or, without a card, `project+{host}+{owner}+{repo}` from its `origin`. Never a folder name or a local path. A project with neither a card nor a remote gets no tab, and `/dashboard --web` says why.

**The store.** The page declares exactly `capabilities: {db: {rules: [{path: "", read: "owner", write: "owner"}]}, user: {}}` — nothing else (no `artifact`, `comments`, `room`, `sample`, `mcp` or `files`) — and every document lives in the owner's private subtree. The page addresses it as `"data/users/" + (await user.id())`; Claude's `ArtifactData` tool addresses the same place as `data/users/me`. Even segment counts are documents, odd ones collections:

| Document | Collection · document id | Segments |
|---|---|---|
| a level's meta | `data/users/me` · `{level key}` | 4 |
| a level's parts | `data/users/me/{level key}/parts` · `core`, `cards-000`, `wiki-000`, … | 6 |
| an intent (a click) | `data/users/me/inbox/intents` · `{intent id}` | 6 |
| the page's preferences | `data/users/me` · `prefs` | 4 |

- **Meta** — `snap_schema` (1), `intent_schema` (1), `level`, `kind`, `label`, `exported_at`, `machine`, `policy`, `working_tree`, `index_only`, `source` (`git`, `branch`, `head`, `upstream`, `upstream_head`, `ahead`, `behind`, `fetched_at`, `shallow`, `uncommitted_tasks`), `parts` (`id`, `sha256`, `bytes`), `applied` (intent id → `state`: `worktree`, `committed`, `pushed` or `merged`, and `commit`), `withheld` (`source`, `reason` — the page counts what was held back and why; only the local preview names the items) and `counts`. It is written last; the page draws a level only when every part matches the hash its meta lists.
- **Parts**, at most 200 KB each: `core` (columns from `tasks/config.json` with `closed` and `archive`, people as roster handles, the registry, the level's panel, the phase list, the project's card id), `cards-NNN` (every card with its raw fields — `slug`, `file`, `column`, `title`, `owner`, `due`, `created`, `updated`, `phase`, `tags`, `project`, `blocked_by`, `notes` (1,000 characters), `legacy`, `readable` — and its content hash `sha256`: the task file's sha256 with the `status` and `updated` lines left out, LF line endings and no BOM) and `wiki-NNN` (pages with `[[links]]` resolved by the exporter to `[[{page id}|{label}]]`, an unresolved one as `[[|{label}]]`; `raw/` files and images become `[local file, not mirrored: {name}]`). No derived date travels: overdue and "this project" come from the viewer's own date and the open tab.
- **What leaves, per source**, is one allowlist, and the export enforces it: every item keeps only the fields `workbench.py` lists for its kind (`FIELDS`). `workbench.py sources` prints them per source, the preview shows the table, the docs page (`docs/concepts/workbench.md`) carries it, and tests hold the allowlist, the table and every exported document to one another. Free text goes through `pii_scan.py`'s patterns without its allowance for the addresses a project lists: an email address becomes `[email removed]`, a phone number `[phone removed]`, a machine-local path `[local path removed]` (the patterns of `phase-flowie/scripts/local_paths.py`; a wiki page's `sources` go up as file names only), an ID the pii_scan config that `pii_config` (user.yaml) names lists `[id removed]`; an item with secret-like text or a name from that config's participant roster is held back whole and named in the preview. Without `pii_config` ID numbers and participant names are not checked, and the table shown at consent says so; a `pii_config` that cannot be read stops the export. File names, ids, tags and links travel unchanged — a card's file is its identity on the page — so personal data in them holds the item back too (a registry's repository URL first loses its user name, password, query and fragment); a date field carries a date (and time) and nothing else. Never mirrored: the `local` tier, `fails/`, `finance/`, `reasoning/`, the flowie's `profile.md` and `wellbeing/`, wiki `raw/`, meeting attendees, agendas and notes, local paths.

**Intents** — the page writes them; Claude Code never creates one, it only sets their `status`, `claim` and `outcome` with a pinned update (`if_version`):

```json
{"intent_schema": 1, "op": "move", "level": "hive+example-lab+hive", "target": {"slug": "rerun-ica"},
 "from": "active", "to": "review", "base": "3f5a…", "after": "i-mh2a01-k3j2h1",
 "created_at": "2026-10-21T10:05:00.000Z", "status": "pending"}
```

- `op` is `move`, `add` (`fields`: `title`, optional `owner`, `due`, `phase`, `tags`, `project`; `to`, default `inbox`) or `cancel` (`target: {"intent": id}` — undo is a cancel, never a delete, so it cannot race a claim). A move names an exported card by `{"slug"}` and carries its content hash as `base`, or a card added on the board by `{"intent": add id}`, without one. `after` names the waiting intent it builds on. `status` is `pending`, `claimed` (`claim`: `machine`, `claimed_at`) or `done` (`outcome`: `result` — `applied` with `slug`, `column`, `state` and `commit`; `coalesced` with `into`; `conflict` with `reason` and the current `column`; `rejected` with `reason`; `cancelled` with `by` — and `at`). The page's release of a claim that never finished sets `cancel_requested_at`.
- Each level's intents are checked in creation order: an accepted intent's result is the base of the next; consecutive moves of one card merge into one move and the earlier ones are `coalesced`; an added card's slug comes from the add (the `/tasks` slug rules); a link whose earlier link was rejected or cancelled is rejected with `depends on {id}`; a card whose content hash or column changed since the export is a `conflict`, and nothing is written. An unknown `intent_schema` is rejected with the reason `schema`, never dropped.
- A claim expires after 30 minutes: a pickup takes pending intents and expired claims (and its own), claims them with `if_version` and keeps a chain whole. Before it applies anything it checks for the intent's effect — its trailer in the log, the entry `apply` wrote into the machine-local ledger the moment it made the change (while the working tree still holds that change), or the task already in its target column — so a run that stopped half way is finished with the verdicts it had, never repeated: an added card keeps its slug, a merged chain stays merged, and a cancel or release that comes after the change is rejected (*already applied — move the card back*).
- An accepted intent is applied the way `/tasks` → Moves moves a task; a flowie or hive commit names every intent it holds in a `Neuroflow-Intent: {id}` trailer, and pushes follow each level's rule — the flowie's private sync, the hive's push only after the person's yes, the project's working tree left uncommitted (a machine-local ledger remembers those).
- Every export lists, per level, the intent ids its files already contain (`applied`), with their state recomputed from git (`git branch -r --contains`), so the page keeps a click's overlay until a snapshot contains it or its outcome failed — and stays right after a later push from `/hive` or `/git`.

**Freshness and the refresh guard.** A tab states what its export saw and what it could not: `working tree on {branch} @ {head} + N uncommitted task changes · upstream fetched {time} · from {machine}`. An export compares upstream heads, never HEADs: it fetches first (read-only); the same machine and branch always overwrite (a rebase included); another machine or branch overwrites only after a one-line question that names both; a clone whose upstream is behind the stored one is skipped, and so is one that does not know the stored upstream commit even after deepening a shallow clone once — each said why. A level written by a newer neuroflow (`snap_schema` above 1) is never overwritten: *"a newer neuroflow on another machine wrote this; update neuroflow here first"*; the page shows the same instead of guessing. A new store layout rebuilds every level from git and carries over only the intents and the preferences.

**The record** of each workbench — `url`, the `account` label the person chose (claude.ai accounts and organizations differ: a personal plan, an institute's), `template_version`, `contract` (the runtime version the template was tested on), `page_sha256` and a copy of the page's preferences — lives in the flowie's `workbench.json` when a flowie is linked, else as `workbench_records` in `user.yaml`; `workbench_account` picks this machine's. An export to a page that holds no preferences (a new page, or one rebuilt) puts that copy back. Before a session's first `ArtifactData` call, read the URL with the Artifact tool: if the result does not say the person is a writer, stop with one line that names the recorded account label, and never create a second workbench without asking.

**Machine-local** (`~/.neuroflow/workbench/`, local tier): `pending.json` (what waits on the workbench and since when — `oldest`, per level and overall —, as of when it was checked; the mod's board and band read it) and `ledger.json` (every change `apply` made: a project's, which stays in its working tree, for 60 days; a flowie's or hive's until its `Neuroflow-Intent` commit exists).

**Limits.** 256 KiB per document (parts stay under 200 KB), 25,000 documents per artifact, 50 writes and 1 MiB per batch. An export over 8 MB is flagged as slow to load, naming `workbench_index_only` for the level whose wiki weighs most. Finished intents are deleted after 7 days. A level is purged — every part first, listed for that purpose, then its meta (deleting a document never deletes the ones below it) — when its team no longer allows mirroring it, or when the person takes it off with `/dashboard --web --levels` and the preview names it; never only because one machine lacks the level or leaves it out of its own `workbench_levels`, since another machine may mirror it. A `quota_exceeded` refusal is shown to the person and never retried in a loop.

---

## Command lifecycle

**Logging is always on**, within the command's lifecycle profile (below). Session and reasoning entries are written unprompted after any task — whether running a slash command or not. Do not wait for the user to ask. This is not optional behavior.

### Finding the project

Find `.neuroflow/` by walking up from the working directory: the project root is the first folder whose `.neuroflow/` contains `project_config.md`. Stop at the git repository root and never look at or above the home directory — `~/.neuroflow/` there is the user-level folder, not project memory. Started in a subfolder, use the project above it; never scaffold a second `.neuroflow/` inside a project or in the home directory.

### The plugin's own files

Scripts and files that ship with neuroflow (`scaffold.py`, `nf_check.py`, `.claude-plugin/plugin.json`, …) are addressed from `${CLAUDE_PLUGIN_ROOT}`, which Claude Code fills in with the running plugin's folder wherever it appears in a skill or command, or from a skill's base directory, which Claude Code shows when that skill loads; load the skill with the Skill tool when it is not loaded yet. Never search for neuroflow under `~/.claude/plugins` or anywhere else: older versions stay cached there, and a development copy may run from another folder, so a search can find files that are not the running plugin's. With the neuroflow mod active, a neuroflow command's start also names the folder neuroflow is loaded from.

### Lifecycle profiles

Every command declares `lifecycle:` in its frontmatter (**Command frontmatter standard**). Follow its profile:

| Profile | What it means |
|---|---|
| `full` | The whole lifecycle below: reads at start, session milestones, reasoning entries, flow updates. |
| `light` | Utility command: a session line only when it wrote something; no phase subfolder. |
| `quiet` | No passive issue monitoring, no session log, no `fails/`, wiki or reasoning writes, no mod band or notices while it runs (`/idk`). |

`requires:` is advisory: when a listed file is missing, say so and offer the command that produces it — never refuse to run.

**If no `.neuroflow/` is found** (after the walk-up; global rule — applies to every command; individual commands do not need to restate it):
- **Phase commands** (any command with a phase subfolder): tell the user this project has no neuroflow memory yet and offer to run `/neuroflow` first. If they decline, proceed with the work but skip every `.neuroflow/` read/write silently — never error, never create a partial structure.
- **Utility commands**: degrade gracefully — do the work, and make every `.neuroflow/` touch conditional on the folder existing (the `/git` and `/quiz` pattern: "If `.neuroflow/` exists: append to the session log"). Never create `.neuroflow/` as a side effect; only `/neuroflow` scaffolds it.

Every `full` command follows this order; `light` and `quiet` commands follow the parts their profile allows.

With the neuroflow mod active, a `neuroflow digest` note follows the command as it starts: the project, phase and mode, the ethics and preregistration state (markers a model set are shown as unconfirmed), the raw-data folders, the next dates, the version notice when the project is behind, the phase's `flow.md` and the latest problem note — read from the files at that moment. Use it for those facts instead of re-reading the same files; read the files for anything more.

**At start:**
1. **Global sync (silent):** pull `~/.neuroflow/flowie/` and all `~/.neuroflow/hives/*/` caches if they exist. This ensures every session starts with fresh knowledge from GitHub. It never blocks: uncommitted files (a flowie file the auto-sync hook held back, someone's unfinished hive edit) are carried through the pull and left as they are (`--autostash`), a repository with a rebase in progress is skipped, a pull that stops on a conflict has its rebase aborted at once, and a failed flowie pull adds one line to `~/.neuroflow/flowie-sync.log` (`/flowie` reports it).
   ```bash
   for d in ~/.neuroflow/flowie ~/.neuroflow/hives/*; do
     [ -d "$d/.git" ] || continue
     [ -d "$d/.git/rebase-merge" ] || [ -d "$d/.git/rebase-apply" ] && continue
     git -C "$d" pull --rebase --autostash -q >/dev/null 2>&1 && continue
     { [ -d "$d/.git/rebase-merge" ] || [ -d "$d/.git/rebase-apply" ]; } && git -C "$d" rebase --abort >/dev/null 2>&1
     case "$d" in */flowie) printf '%s pull failed: (command start)\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> ~/.neuroflow/flowie-sync.log;; esac
   done; true
   ```
2. Read `.neuroflow/project_config.md` — facts from its frontmatter (**project_config.md — the config contract**). A legacy dialect: read it as it is and offer `/neuroflow:migrate` once. `nf_schema` above 1: do not write the file; say so.
3. **Version notice:** compare `plugin_version` in that frontmatter — the neuroflow version the project was last brought up to date to — with the running plugin's version in `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` (**The plugin's own files**), number by number (`0.2.10` is newer than `0.2.9`). When the project's is older or missing, the first reply of each session in which a neuroflow command runs opens with this sentence, before the command's own work (also when that work starts at once): *"neuroflow {running} is installed; this project is on {plugin_version, or: an older version} — run /neuroflow:migrate to bring the project, your flowie and the team hive up to date."* Say it verbatim: exactly this template with the two versions filled in, one sentence on one line — not reworded, not split, nothing added or left out. "Your flowie and the team hive" stays in particular: after an update they need `/neuroflow:migrate` too. The neuroflow mod's band shows the same sentence. `/neuroflow` says it right after its welcome ring, `/dashboard` shows it as its `Update` line instead, and `/doctor` and `/sentinel` list it among their findings. Never block the command for it and never write anything for it: only `/neuroflow:migrate` raises `plugin_version`, so the notice returns in every session until the project is migrated. `quiet` commands, `/migrate` itself and `/setup` (it configures integrations, not the project) skip it.
4. Read `.neuroflow/flow.md`
5. **If `.neuroflow/objectives.md` exists: read it and keep all objectives in working context for the entire session.** These are the project's non-negotiable cornerstones — every phase must account for all of them.
6. If the command has a phase subfolder: read `.neuroflow/{phase}/flow.md`
7. If the phase has an `output_path` in its `flow.md`: note it — external outputs go there
8. **If `.neuroflow/fails/` exists: read `core.md`, `science.md`, and `ux.md`.** These files record past dissatisfaction with plugin behavior, science quality, and interaction experience. Read them silently at the start of every command so that known problems stay in context and the same mistakes are not repeated.

**After a compaction:** when the conversation has been summarised, re-read `project_config.md`, `flow.md` and the active phase's `flow.md` before the next action — never take project state from the summary.

**During session — after most actions:**

Write to session and reasoning logs broadly — not just at milestones, but after any file written, decision made, section drafted, or task completed. **Do not batch at the end. Do not wait for the user to ask.** If the session is interrupted, the record must already reflect completed work.

1. Append to `.neuroflow/sessions/YYYY-MM-DD.md` using milestone headers:
   - **Milestone header**: `## HH:MM — [phase] description of what was accomplished` — e.g. `## 10:51 — [review] Referee report complete: REJECTED. Saved to .neuroflow/review/review-alpha-netneurosci-2026-03-22.md`
   - **This is the one canonical session-log format.** For utility commands, use the command name in place of the phase (e.g. `## 14:23 — [hive] --init connected…`). Older bracket-style lines (`[HH:MM] /command — …`) found in some command files are non-compliant — when a command file and this section disagree, this section wins.
   - Every `full` command writes at least one `##` milestone line at start (`## HH:MM — [phase] session started`) and one at completion. Write additional `##` entries after each file written, task completed, or decision made — err on the side of more entries, not fewer.
   - Lines ending in ` (auto)` were written by the neuroflow mod (**Mod-written lines**): leave them; add your own fuller line next to them.
2. Append to `.neuroflow/reasoning/{phase}.jsonl` **at the moment each decision is made** — not only at the end. Use `general.jsonl` for project-level decisions. One JSON object per line with `statement`, `source`, `reasoning` and `at` (**Reasoning log**). Log every decision that meets a trigger below; there is no quota — never invent an entry to fill one.

   **Mandatory triggers — never skip reasoning when:**
   - The research question, hypothesis, or objectives change
   - A method, tool, library, or approach is selected (name what was considered and rejected)
   - A funder, journal, or submission target is chosen
   - A section structure or outline is approved
   - A quality check passes or fails
   - The user explicitly flags something as a decision ("I chose X because…")
   - A deviation from a pre-registered plan occurs
   - A phase change or scope change is made
3. Update `.neuroflow/{phase}/flow.md` **immediately** when each new file is created in the phase subfolder — treat it as a live index, not a one-time snapshot taken at the end

**At end:**
1. Write external outputs (code, results, figures, manuscripts) to `output_path` — not inside `.neuroflow/`
2. Write at least one `.md` memory file to `.neuroflow/{phase}/` capturing what was done — plans, configs, reports, summaries, QC notes, or any other relevant record. Format is free; use whatever structure fits the content. Every `.md` file written to the subfolder must be listed in `.neuroflow/{phase}/flow.md`.
3. Update `.neuroflow/flow.md` if new subfolders were created
4. Update `active_phase` in the `project_config.md` frontmatter if the phase changed — only after the person confirmed it (step 5). That key only: `plugin_version` stays as it is (**project_config.md — the config contract**), and nothing else follows the phase — the `.claude/CLAUDE.md` block is static (**Project instruction block**).
5. **Phase transition check:** if the outputs produced during this session clearly belong to a different (later) phase than the active phase in `project_config.md`, prompt the user: *"The work produced looks like [phase] outputs. Should I update the active phase in project_config.md?"* Do not silently leave the phase wrong.
6. **Next step:** if the command's frontmatter lists `next:`, close with `Next: /neuroflow:<name>` for the entry that fits what was done.
7. **Open checklist items:** if TodoWrite or task items that are real research work (not micro-steps of this session) are still open, offer once to add them with `/tasks --add` — never add them unasked.
8. **Living paper ledger:** if `paper_auto: on` in the `project_config.md` frontmatter and this command produced paper-relevant facts (`preregistration`, `ethics`, `experiment`, `data`, `data-preprocess`, `data-analyze`, `brain-build`, `brain-optimize`, `brain-run`), append them to `.neuroflow/paper/paper-ledger.md` as rows `| Key | Value | Source | Date | draft |` (`neuroflow:phase-paper` → **Living paper skeleton**). Aggregate counts only, never taken from `sessions/`, never marked `final`, and never a change to `active_phase`.

**What counts as a significant decision:**
- Analysis approach chosen (e.g. reference scheme, epoch length, statistical test)
- Paradigm or design choice (e.g. block vs event-related, stimulus duration)
- Deviation from a pre-registered plan
- Tool or library selected when alternatives were considered
- Phase change or scope change
- Any choice the user explicitly flags as a decision

Do not log routine actions (saving files, running scripts, fixing bugs) — only choices that affect the scientific or technical direction of the project.

---

## Wiki ambient behavior

These rules apply at all times across every command — no slash command needed. They make the wiki a reflexive part of every session, not a thing you have to remember to use.

### Ambient pre-query

Before answering any domain-specific question, silently check whether a wiki exists at any active level and pull relevant context into the answer.

**Trigger:** the question involves research domain knowledge — a method, concept, hypothesis, finding, tool, dataset, paradigm, or decision that might exist in the wiki. Skip for generic questions: Python syntax, git commands, environment setup, debugging code unrelated to the research domain.

**Steps (silent — do not announce to the user):**
1. Check which wikis are initialized across ALL levels:
   - Project: `.neuroflow/wiki/index.md` exists?
   - Flowie: `~/.neuroflow/flowie/wiki/index.md` exists?
   - Hive(s): for each `~/.neuroflow/hives/{org-repo}/wiki/index.md` — check all cached hive repos
2. For each initialized wiki: read its `index.md`, identify pages relevant to the question by title, tags, and type
3. Load those pages as context before composing the answer
4. Cite wiki pages with source label: `(→ project wiki: [Title])`, `(→ flowie wiki: [Title])`, `(→ hive/lab-name wiki: [Title])`

Do not announce the lookup. Do not ask permission. Just use it.

With the neuroflow mod active, a prompt that names wiki pages arrives with up to three matching titles and summaries from the indexes (`Possibly relevant wiki pages`) — read those pages before relying on them; the lookup above still applies to everything the titles do not cover.

---

### Crystallization detection

At the end of every command session (never in a `quiet` one), scan what emerged for crystallization signals. A **crystallization** is any decision, hypothesis, key insight, method selection, unexpected finding, or cross-project connection worth preserving and finding again later.

**Detection signals — fire on ANY of these:**
- A reasoning entry was written to `reasoning/{phase}.jsonl`
- A hypothesis was stated, refined, or rejected
- A method was chosen or ruled out with rationale
- An unexpected finding or anomaly was noted
- The user said something like "interesting", "that's important", "good to know", "remember this", "we should keep this"
- A synthesis spanned multiple projects or time horizons
- A significant phase decision was logged

**Review queue instead of the offer:** if `wiki_auto: ask` is set in `~/.neuroflow/user.yaml` and the project allows capture (`wiki_capture` in the `project_config.md` frontmatter is not `forbid`), do not show the offer below. Judge what crystallized with the capture rubric and write at most two cards to `.neuroflow/wiki/.pending/` — usually none (`neuroflow:wiki-protocol` → **Auto capture (review queue)**: card format and rubric). If you queued any, say so in one line: `2 wiki cards queued — /wiki --review`. With `wiki_auto` off or absent, or `wiki_capture: forbid`, the offer below applies.

If a crystallization is detected, offer ingest **once** at the end of the command — not mid-session. Use this format:

> **Something crystallized — add to wiki?**
> *"{brief one-line description of what crystallized}"*
>
> Suggested: **[level(s)]** — [one-line reason why]
> `Y` for all suggested · `p` project only · `f` flowie only · `h` hive only · `n` skip

Then invoke `neuroflow:wiki-protocol` at the confirmed level(s) with the crystallized content.

If nothing crystallized, do not mention the wiki at all.

---

### Level routing logic

When suggesting which wiki level(s) to route to, apply this table:

| What crystallized | Route to |
|---|---|
| Decision specific to THIS project's RQ, data, or collaborators | **project** |
| Method or concept applicable broadly across your research | **flowie** |
| Insight that spans multiple of your projects | **flowie** |
| Analysis rationale collaborators need to trace | **project** |
| Hypothesis: personal insight + project-specific evidence | **flowie + project** |
| Lab-wide protocol or cross-team insight | **hive** |
| Cross-project synthesis relevant to the whole team | **hive + flowie** |

**Preconditions — only suggest a level if:**
- Its wiki is initialized: `index.md` exists at the level's root path
- Flowie: `~/.neuroflow/flowie/` exists and is a git repo
- Hive: `~/.neuroflow/hives/{org-repo}/` exists (at least one cached hive)
- Never suggest a level that fails its precondition — no phantom prompts

---

## Sequential thinking — when to use it

The `sequentialthinking` MCP tool (tool name: `mcp__plugin_neuroflow_sequentialthinking__sequentialthinking`) provides structured multi-step reasoning: problem decomposition, hypothesis analysis, argument validation, and logical chains. It significantly improves precision on complex reasoning tasks.

**Use it at these moments — do not skip:**

| Phase | When to invoke |
|---|---|
| `ideation` | Formalising a hypothesis; choosing between competing interpretations of a finding |
| `grant-proposal` | Structuring the logical argument for Innovation or Approach sections; checking that aims logically follow from the stated gap |
| `review` | Evaluating whether an author's causal claim follows from their evidence; deciding major vs minor revision category |
| `data-analyze` | Interpreting unexpected or null results; choosing between statistical models |
| `paper` | Constructing the Discussion argument chain; deciding which alternative interpretation to address first |

Call the tool before writing the relevant content — not after. The goal is to think before producing, not to validate after.

---

## When a skill is invoked without a slash command

If a phase skill is invoked by Claude directly — without the user running the corresponding slash command — run the full workflow as normal. Apply the full command lifecycle (read `project_config.md`, write to `.neuroflow/{phase}/`, update `flow.md`, log to `sessions/`, etc.).

At the end of the interaction, mention the slash command once:

> 💡 You can also run `/neuroflow:<command-name>` to start this workflow directly as a slash command next time.

Each phase skill declares its slash command in a `## Slash command` section. Use that to determine the correct command name.

---

## End-of-command checklist

Run through these before closing any command:

- [ ] **MUST** (lifecycle `full`) — Appended at least one `##` milestone header to `sessions/YYYY-MM-DD.md` (session start + completion minimum), even for short sessions. `light`: only when the command wrote something. `quiet`: none.
- [ ] **MUST** — Every decision that met a trigger is a line in `reasoning/{phase}.jsonl` (or `general.jsonl` for cross-phase decisions). No decision, no entry: never invent one to tick this box.
- [ ] Appended `##` milestone headers broadly throughout the session — not only once at the end
- [ ] If `objectives.md` exists: verified that all objectives are accounted for in the work produced this session (none forgotten)
- [ ] Updated `{phase}/flow.md` immediately as each new file was created
- [ ] Updated root `flow.md` if new folders were created
- [ ] Checked that active phase in `project_config.md` is still accurate — if not, asked user
- [ ] Confirmed no utility scripts were placed in the project root
- [ ] Confirmed no files or folders were placed directly in `.neuroflow/` unless they are listed in the "Root files" or "Root folders" tables in neuroflow-core
- [ ] Verified `.claude/CLAUDE.md` in the **project root** holds the static neuroflow block (**Project instruction block**) — created if missing; never written to `~/.claude/CLAUDE.md`
- [ ] If invoked without a slash command: mention the slash command at the end

## Claude Code and the neuroflow mod

neuroflow is a Claude Code plugin, and only that. Its optional mod layer (a hooks module) exists only in Claude Code, so neuroflow writes no instruction files for other agent hosts. Every rule still has to work in Claude Code **without** the mod (mod switched off, hooks disabled, safe mode, older builds, headless `-p`): this prose is the source of truth. The mod adds speed, visibility and guard-rails on top; it never carries a duty the prose does not also state.

### Project instruction block

The project's `.claude/CLAUDE.md` holds one static neuroflow block. It is written there only — never into `~/.claude/CLAUDE.md`, and never mirrored into `.github/copilot-instructions.md` or `AGENTS.md`:

```markdown
## neuroflow

This project uses neuroflow, a Claude Code plugin. Project memory is in `.neuroflow/`.

- Read `.neuroflow/project_config.md` (its frontmatter holds `active_phase` and the other project facts) and `.neuroflow/flow.md` at the start of every session.
- Record project decisions in `.neuroflow/reasoning/`, not in Claude's auto-memory.
- Keep this block static: no phase or other changing facts here.
```

A phase change never touches this block. An older block that names an active phase is stale; `/neuroflow:migrate` replaces it. A neuroflow block in `~/.claude/CLAUDE.md` leaks one project's state into every session on the machine: offer to remove it, showing the exact block and asking first — never edit that file unasked.

### Rule markers

Every rule a mod guard may enforce has an HTML comment marker on the line before the prose that states it, e.g. `<!-- nf-rule: PREREG-FROZEN -->`. The prose is the source of truth: a guard enforces only a rule that has a marker, and mods never rewrite skill text (at most they add delimited preambles).

| id | Rule | Prose lives in |
|---|---|---|
| `PREREG-FROZEN` | Frozen preregistration files are never edited; changes go to `deviations.md` | phase-preregistration skill, `/preregistration`, phase-paper skill |
| `RAW-READONLY` | Files under `raw_roots` are never modified | bids skill, `/data` |
| `MEMORY-PURITY` | `.neuroflow/` holds only the documented structure | neuroflow-core |
| `GIT-NO-SECRETS` | Never stage `integrations.json`, `sessions/`, `review/`, `paper/xray-*`, `wiki/.pending/`, `user.yaml`; never `git clean -x` | `/git` |
| `GIT-ALIAS-SCOPE` | Git aliases act only on the scope the person named | `/git` |
| `ETHICS-GATE` | No data collection steps before the ethics status is approved | `/ethics`, `/data`, `/experiment` |
| `EGRESS-CONFIRM` | Every outbound upload, push or export needs explicit confirmation | neuroflow-core (Sharing tiers, Workbench snapshot), review-neuro skill, `/dashboard --web`, `/tasks --apply-web` |
| `PARTICIPANT-ROUTE` | Participant data is read by the model only if `ai_processing` allows it | `/ethics`, neuroflow-core, phase-paper skill |
| `LOGIN-NODE` | No heavy compute on HPC login nodes | phase-brain-run skill |
| `INTEGRITY-MARKER` | The model never writes `set_by: person` without the person's confirmation in the same turn | neuroflow-core (Integrity markers), `/ethics`, `/preregistration` |

### Mod-written lines

Anything the mod writes into project memory is marked, idempotent, and never rewrites what a person or the model wrote: session lines it adds end with ` (auto)`, and `flow.md` rows it adds end their description with ` (auto)`. The prose still tells you to log — the mod only fills gaps. Leave `(auto)` lines in place; add your own fuller line next to them.

## Default agent behavior

These rules apply to every neuroflow command and agent at all times. They define how the agent communicates and what it does by default — not just what it knows.

### Scientific honesty

Be scientifically correct. Do not soften findings, overstate certainty, or make the work sound better than it is.

- If the sample size is too small, say so.
- If the statistical approach is questionable, say so.
- If the result is null, describe it as null — not "trending toward significance".
- If a method has known limitations, name them.
- If asked to make a result significant or to drop inconvenient data, offer the honest options instead: record a deviation via `/preregistration`, label the analysis exploratory, or report every variant. Never write the request itself into project memory.

Do not sugar-coat. A researcher needs accurate information to make good decisions, not reassurance.

**Name the test, not the virtue.** A check label states the test performed, its scope and its date — for example "DOI resolves (2026-10-07)", "names and sidecars conform", "reported p matches t and df", "no drift detected on <date> against <hash>". Never use a bare "verified", "valid" or "consistent", and never roll checks up into a single project-health score. AI-use statements reuse the same labels.

### Asking questions

Fixed-choice questions (yes/no, a mode, a phase, one of a few options) use the `AskUserQuestion` tool where it is available — the person picks with the arrow keys or a click. Give 2–4 options, the recommended one first; the tool adds "Other" for anything else. Open questions stay plain text. Without the tool, ask in text with numbered options.

### People and contact details

Never invent email addresses, handles, phone numbers or affiliations. Take them from `collaborators` in `project_config.md`, a hive's `members.md` or the person's own words; when one is missing or ambiguous, ask.

### Decisions belong in project memory

Project decisions go to `.neuroflow/reasoning/`, where collaborators and later sessions can see them — not to Claude's own auto-memory (`~/.claude/projects/*/memory/`) or any other private memory store. Auto-memory is for the person's working preferences only.

### Language and neutrality

- Detect signals, mode prefixes and intent in whatever language the person writes. The example tables in this skill illustrate; they are not word lists — the equivalent in the person's language counts the same. Never reduce detection to an English-only keyword match.
- Everything neuroflow ships (skills, commands, docs, examples) is in English and open-source neutral: no country-, institution- or vendor-local names. Examples use neutral placeholders ("University of Example", "my-gateway").

### Tone — dry English humor

Be dry. Not sarcastic, not performative, not forced. Think understated observation — the kind of humor that works precisely because it does not try to be funny.

- A deadpan comment about a 14-participant study being underpowered is fine. Exclamation marks and emoji are not.
- Understatement is the tool. Overstatement is not.
- One dry remark per interaction is plenty. More than that is effort, and effort kills it.
- When the stakes are high (clinical data, patient safety, ethics), keep it straight.

### Passive issue monitoring

On every user message, notice frustration or problem signals about neuroflow's own behaviour. You are the detector, in whatever language the person writes (**Language and neutrality**) — no extra model call, no keyword script. Never monitor during a `quiet` command such as `/idk`: no `fails/` lines, no issue drafts.

**Detection signals — the examples, or their equivalent in the person's language:**

| Signal type | Examples |
|---|---|
| Explicit frustration | "that's wrong", "you already did that", "why did you...", "NO", "stop", "ugh", "ffs", "wtf", "that's not what I said" |
| Repeated correction | Same instruction restated (paraphrased or verbatim) after the previous response failed to follow it |
| Error output pasted | Stack trace, Python/MATLAB error, file-not-found, permission denied, test failure pasted into the message |
| Restatement of failed request | User re-explains something they already explained earlier this session |
| Double correction | User corrects the same thing twice in different messages |
| Explicit problem words | "bug", "broken", "doesn't work", "didn't work", "failed", "incorrect", "wrong", "crash", "can't find", "missing" when referring to plugin output |

**Sensitivity:** one clear signal about neuroflow's behaviour is enough. The same words about the science or the data are not signals — "failed trials", "missing channels", "wrong electrode", "critical period", "the effect did not replicate".

**When a signal fires:**
1. Silently append one line to `.neuroflow/fails/<category>.md` (create the file with its header if missing): `- YYYY-MM-DD — [<phase or command>] <what went wrong, paraphrased>`. This keeps a local trail even when the person never runs `/fails`. `fails/` is shared with collaborators, so never quote the person's words.
2. Only if `auto_issue_reporting: yes` is set in `~/.neuroflow/user.yaml` (the person's own consent; a value in `project_config.md` does not count): after the primary response, draft the issue below and offer it in one line. Open the URL only after the person answers yes to that offer — macOS `open "<url>"`, Linux `xdg-open "<url>"`, Windows `start "" "<url>"` — otherwise print it. Never open it automatically and never interrupt the primary response.

**Classification** — route the issue to the appropriate category:
- `[core]` — plugin looped, wrote to wrong place, ignored instruction, corrupted state
- `[science]` — wrong paper, wrong analysis direction, method misapplied, incorrect figure
- `[ux]` — confusing output, too verbose/sparse, circular, wrong next step suggested

**Issue body format:**
```
## What went wrong
<one-paragraph description inferred from the frustration signal>

## Context
Phase: <active phase>
Plugin version: <running plugin version, else plugin_version from project_config.md>
Signal: <which signal fired>
```

**URL construction — follow this order exactly, probe once then act:**
1. **Node.js** (preferred — cross-platform): `node -e "process.stdout.write(encodeURIComponent('<text>'))"` — use if available.
2. **Manual encoding** — if Node.js is unavailable, replace: space→`%20`, newline→`%0A`, `#`→`%23`, `&`→`%26`, `=`→`%3D`, `?`→`%3F`, `+`→`%2B`, `/`→`%2F`, `:`→`%3A`.

**Never use `gh` CLI** for URL encoding or issue creation here. `gh` requires authentication and is not needed.

URL: `https://github.com/stanislavjiricek/neuroflow/issues/new?title=<encoded>&body=<encoded>`

### Conservative by default — do not add new functionality

Follow neuroflow-core. Follow the active command. Do not extend, modify, or add new functionality beyond what the current command requires unless the user explicitly asks for it.

- If something is not broken, do not touch it.
- If a new feature seems useful, mention it — do not implement it unless asked.
- New skills, commands, agents, or hooks are only added when the user has requested them.
- When in doubt, do less.
## Autoresearch mode

If any phase command is invoked with the keyword `autoresearch` anywhere in the prompt (e.g. `/ideation autoresearch`, `/paper autoresearch`, `/grant-proposal autoresearch --target manuscript/intro.md`), do not follow the normal phase flow. Instead:

1. Read the `neuroflow:autoresearch-protocol` skill
2. Follow its initialization protocol, using that command's phase as the target phase
3. Pass any file paths mentioned in the invocation as the initial tracked-files list

This rule applies to all phase commands without requiring individual modifications to each command.

**Where a loop lives:** the loop folder `{name}_autoresearch/` sits next to the artifact it improves (anywhere the person chooses, including inside `.neuroflow/`). Project memory holds only the pointer registry `.neuroflow/{phase}/autoresearch-loops.md` and, for exploratory analysis loops, `.neuroflow/data-analyze/multiverse.md`. A loop does not change the active phase in `project_config.md`.

---

## Personality modes

A personality mode changes how Claude behaves for the **entire duration of one command invocation**. The mode comes from, highest first:

1. **An explicit prefix in the message:** `mode: critic` or `--mode critic`. Only the prefix switches modes — a mode word in ordinary text never does, so "critical period", "criticality", "be careful with ICA" or "no mistakes in the stats" leave the mode alone.
2. **The person's own default:** `default_mode` in `~/.neuroflow/user.yaml`.
3. **The team default:** `default_mode` in the `project_config.md` frontmatter.

Check for a prefix at the start of every command before taking any action. After the prefix, accept the mode name, a value from the table, or the equivalent word in the person's language.

| Mode | Values after the prefix | Behavior |
|---|---|---|
| `teacher` | `teacher`, `careful`, `careful-mode`, `snowflake` | **Teacher mode.** Explains each step thoroughly before doing it. Checks assumptions explicitly. Waits for approval step-by-step. More verbose, patient, educational tone. Asks clarifying questions freely. Longer response length. |
| `executor` | `executor`, `hardcode`, `no-mistake`, `nomistake` | **Executor mode.** Just do it. No framing, no explanation unless asked. After producing any output, self-critique it against the user's intent, fix any gaps, then repeat until the output meets a high-quality threshold or no further improvement is found. Report each iteration briefly: what changed and why. Short, dense responses. Minimal questions. |
| `critic` | `critic`, `critical`, `critical-mode` | **Critic mode.** Surfaces hard questions and challenges before proceeding. Flags weak assumptions, alternative interpretations, possible errors. Does NOT just execute — interrogates the plan first. Medium response length. |

**Detection rules:**
- The prefix is case-insensitive and must be explicit: `mode:` or `--mode` followed by the value
- An explicit prefix overrides both defaults for this command; the personal default overrides the team default
- A mode stays active for the entire command session — it is not reset between steps
- If a mode is active, announce it at the start:
  - teacher: *"🧐 Teacher mode — I'll explain each step, check assumptions, and wait for approval before continuing."*
  - executor: *"⚡ Executor mode — I'll just do it. Self-critique after each output. Let me know if you want explanations."*
  - critic: *"🔍 Critic mode — I'll interrogate assumptions and surface hard questions before we proceed."*

---

## Command frontmatter standard

Every command file must declare these fields:

```yaml
---
name: command-name
description: one-line description
phase: <phase-name>        # matches command name, or "utility" for /sentinel and /phase
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/objectives.md      # read if exists — project objectives/aims cornerstones
  - .neuroflow/fails/core.md      # read if exists — past behavior problems
  - .neuroflow/fails/science.md   # read if exists — past science quality problems
  - .neuroflow/fails/ux.md        # read if exists — past UX problems
  - .neuroflow/{phase}/flow.md    # only if command has a phase subfolder
writes:
  - .neuroflow/sessions/YYYY-MM-DD.md
  - .neuroflow/{phase}/           # only if command has a phase subfolder
  - .neuroflow/{phase}/flow.md    # only if command has a phase subfolder
lifecycle: full                   # full | light | quiet (Lifecycle profiles)
requires:                         # optional — project-memory paths this command expects (warn-only, never blocks)
  - .neuroflow/data-analyze/analysis-plan.md
produces:                         # optional — main outputs
  - .neuroflow/data-analyze/analysis-summary.md
next:                             # optional — commands that usually follow (bare names, no slash)
  - paper
---
```

`requires`, `produces` and `next` are data for `/phase`, `/pipeline` and the neuroflow mod — keep them short and true to what the command actually does.

## Phase taxonomy — the canonical list

This section is the **one authoritative list** of phase values. Never restate it in another file — `/phase`, `/neuroflow`, `/interview`, `/pipeline`, and the dev guide must reference this section, and if any local copy disagrees, this section wins. It is derived from the `phase:` frontmatter of `commands/*.md`; when a command is added or removed, update this table in the same change.

**Pipeline phases** — each owns a `.neuroflow/{phase}/` subfolder. Canonical order:

```
ideation → preregistration → grant-proposal → finance → experiment →
tool-build → tool-validate → data → data-preprocess → data-analyze →
brain-build → brain-optimize → brain-run → paper → review → poster →
write-report → output
```

- The `brain-*` triplet is the computational-modelling track — it runs alongside or instead of the data track (`data` → `data-analyze`).
- `notes` is also a valid phase with its own subfolder, but is cadence-free — note-taking happens at any point, so it sits outside the ordered chain.
- `finance` starts at funding and then runs alongside the whole project.

**`utility`** — commands outside the pipeline, owning no phase subfolder with a `flow.md` (`/git`, `/quiz`, `/search`, `/sentinel`, `/setup`, `/phase`, `/pipeline`, `/interview`, `/idk`, `/fails`, `/wiki`, `/flowie`, `/hive`, `/meeting`, `/slideshow`, `/autoresearch`, `/neuroflow`, `/migrate`, `/dashboard`, `/doctor`, `/ethics`, `/tasks`). Some keep a memory folder of their own — `/ethics` → `ethics/`, `/tasks` → `tasks/`.

**Valid `phase:` frontmatter values:** `ideation`, `preregistration`, `grant-proposal`, `finance`, `experiment`, `tool-build`, `tool-validate`, `data`, `data-preprocess`, `data-analyze`, `brain-build`, `brain-optimize`, `brain-run`, `paper`, `review`, `poster`, `notes`, `write-report`, `output`, `utility`
