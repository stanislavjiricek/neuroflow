---
name: phase-hive
description: Team-level knowledge layer for neuroflow. Connects a researcher's personal neuroflow project to a shared GitHub organisation repo for team identity, research directions, projects registry, knowledge base, meetings, tasks, and cross-project ideas. Never automatically copies personal project data — all sharing is explicit.
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/hive/hive.md
  - .neuroflow/hive/members.md
  - .neuroflow/hive/sync.json
writes:
  - .neuroflow/hive/
  - .neuroflow/hive/hive.md
  - .neuroflow/hive/members.md
  - .neuroflow/hive/sync.json
---

# phase-hive — Team research layer

Hive is the **team-level counterpart to flowie**. Where flowie is the personal research OS (private, per-researcher), Hive is the shared lab OS (visible to all team members).

**Privacy rule (enforced absolutely):** Nothing from a personal `.neuroflow/` project is ever automatically sent to Hive. Every share is an explicit, intentional action. The Hive is a shared workspace, not a surveillance layer.

---

## Hive repo structure (GitHub org private repo)

```
{org}/{hive-repo}/
├── hive.md          ← team identity, norms, and active research directions
├── members.md       ← team roster: name, email, github, role
├── ideas.md         ← cross-project team hypotheses and open questions
├── sync.json        ← sync metadata: last pull per member, last push timestamps
├── projects/        ← lab project registry (same structure as flowie/projects/)
│   ├── projects.json
│   └── {id}.md
├── tasks/           ← team Kanban board (same structure as project tasks)
│   ├── inbox/
│   ├── ready/
│   ├── active/
│   ├── review/
│   ├── meeting/
│   ├── done/
│   └── archive/
├── meetings/        ← team meeting files (created by /meeting --level hive)
│   └── config.json
└── wiki/            ← team knowledge base (same structure as flowie wiki)
    ├── index.md
    ├── log.md
    ├── schema.md
    ├── raw/
    └── pages/
```

### File formats

**`hive.md`** — team identity, norms, and directions (replaces old `hive.md` + `directions.md`):
```markdown
# {Team name}

{Team description — what the lab studies, approach, values}

## Norms
{collaboration norms, code standards, data policies}

## Active research directions
{Directions as bullet list or ## subsections — maintained by PI/leads}
```

**`members.md`** — team roster with contacts for meeting invitations:
```markdown
# Team Members

| name | email | github | role |
|------|-------|--------|------|
| {name} | {email} | {handle} | {PI/researcher/student} |
```

**`ideas.md`** — lab-wide cross-project hypotheses (analogous to flowie/ideas.md but team-level):
```markdown
# Team Ideas

Open hypotheses, cross-project questions, and speculative directions the lab is exploring.

---
```

**`projects/projects.json`** — machine index of all lab projects (same schema as flowie projects):
```json
{ "projects": [ { "id": "...", "description": "...", "current_phase": "...", "status": "..." } ] }
```

---

## Local hive state (per-project)

```
.neuroflow/hive/
├── hive.md          ← local copy of team identity + directions
├── members.md       ← local copy of team roster
└── sync.json        ← hive_repo URL, last_pull, last_push, member_handle
```

---

## Command modes

### `--init`
Connect the current neuroflow project to a Hive repo for the first time.

1. **Check flowie profile first:** if `.neuroflow/flowie/profile.md` exists and contains a `hives:` list, show it as a picker before asking freeform:
   ```
   Your flowie profile lists these hives:
     [1] acme-neuroscience/hive-lab
     [2] another-org/hive-research
     [3] Enter a different repo
   ```
   If the user picks one, pre-fill the org/repo. Otherwise ask freeform.

2. Ask for the GitHub org and repo name: `{org}/{hive-repo}`
2. Ask for the researcher's GitHub handle (used as `member_handle` in sync.json)
3. Check if the hive repo already exists (via `gh` CLI or GitHub API)

**If joining an existing hive repo:**
- Clone or fetch to read `hive.md`, `members.md`, and `sync.json`
- Create `.neuroflow/hive/` with local copies + initial sync.json
- Update `.neuroflow/flow.md` + `project_config.md`
- Show team identity from `hive.md` and members from `members.md`

**If creating a new hive repo:**
- Scaffold full structure (all folders and files from the structure above)
- Ask: *"Team name and description?"*
- Ask: *"Active research directions? (one per line)"* → write to `## Active research directions` in `hive.md`
- Ask: *"Add team members? (name, email, GitHub handle, role — one per line, Enter to skip)"* → write to `members.md`
- Push to GitHub: `gh repo create {org}/{hive-repo} --private`

### `--sync`
Pull latest state and show a digest of what changed since last pull.

1. Record current state: `git -C (local hive cache) log --oneline` or note last_pull timestamp
2. Fetch `hive.md`, `members.md`, `ideas.md`, and `sync.json` from hive repo
3. Update local `.neuroflow/hive/` copies
4. Update `sync.json` with `last_pull: [timestamp]`
5. **Digest:** compare old and new versions and print a structured change summary:
   ```
   Hive sync — 2026-04-20 10:00
   ─────────────────────────────
   directions: 1 new (Alpha modulation → fMRI feasibility)
   members: no changes
   ideas: 2 new entries
   wiki: 3 pages updated, 1 new (method: ICA pipeline)
   tasks: 2 new in inbox, 1 moved → done
   ─────────────────────────────
   ```
6. If any new directions overlap with the current project's modality or research question, highlight them: *"New team direction may be relevant: {direction}"*

### `--view`
Display current local Hive state without syncing.

1. Read `.neuroflow/hive/hive.md` and `members.md`
2. Read `sync.json` for last sync timestamp
3. Print team identity, directions, member count, last sync
4. Print: `"Run /hive --sync to fetch the latest updates."`

### `--members`
View and edit the team roster.

1. Read `members.md` from hive repo (pull first)
2. Display the members table
3. Options: add member, remove member, update role/email
4. Write updated `members.md`, push to hive repo

### `--projects`
View and manage the lab project registry (analogous to `/flowie --projects`).

1. Pull `projects/projects.json` from hive repo
2. Display all lab projects as ASCII phase timeline (same format as flowie projects)
3. Sub-flags: `--projects --add` to register a new lab project (asks id, description, repos, current phase, status)
4. Push changes to hive repo

### `--ideas`
View and append to lab-wide cross-project ideas.

1. Pull `ideas.md` from hive repo
2. Display current ideas
3. Ask: *"Add a new idea?"* — if yes, append to `ideas.md`, push
4. Also triggered from wiki ingest when synthesis spans multiple projects

### `--tasks`
Read and manage the team Kanban board at `{hive-repo}/tasks/`. Same ASCII box rendering rules as `/flowie --tasks --level hive`. Tasks get `level: hive` and `responsible: @name` in frontmatter. Pull first, push after writes. Supports `--tasks`, `--tasks --list`, `--tasks --add`, `--tasks --move`, `--tasks --done`.

### `--recommend`
Get team-aware recommendations for the current project phase.

1. Read local `hive.md` (directions section) and `members.md`
2. Read current project's `project_config.md`
3. Check `wiki/` for relevant methods and synthesis pages (search index.md)
4. Surface:
   - Team directions overlapping this project's modality or research question
   - Methods from hive wiki relevant to the current phase
   - Ideas from `ideas.md` that connect to this project
5. Present as compact digest: *"Your team has N relevant items for your current phase"*

### `--wiki`, `--wiki-ingest`, `--wiki-query`, `--wiki-lint`, `--wiki-add`, `--wiki-schema`
Operate on the hive-level team wiki at `{hive-repo}/wiki/`. Load `neuroflow:wiki` skill with `level: hive`. Same modes as `/flowie --wiki-*` but all git operations target the hive repo. This replaces the old `shared/` folder — use `--wiki-ingest` to contribute findings, methods, and literature to the team knowledge base.

---

## Collaborator join flow

When a new team member joins a project that already has neuroflow set up, they follow this sequence:

1. **Clone the project repo** — `.neuroflow/` is present (tasks/, hive/, notes/, project_config.md are all git-tracked)
2. **Run `/neuroflow`** — detects existing `.neuroflow/project_config.md`, shows current state, prompts for their own name and flowie setup
3. **Check `.neuroflow/flowie/`** — if it exists from a previous collaborator's work, `git check-ignore -v .neuroflow/flowie/` should show it's gitignored; if not, add `.neuroflow/flowie/` to `.gitignore` before running `/flowie`
4. **Run `/flowie`** — set up or link their own private flowie profile (each collaborator has a separate private `flowie` repo)
5. **Run `/hive --sync`** — pull team directions, member list, and shared content from the hive repo

**What is shared vs. private:**

| Path | Shared in project repo? |
|------|------------------------|
| `.neuroflow/project_config.md` | Yes — shared context for all |
| `.neuroflow/tasks/` | Yes — shared project Kanban |
| `.neuroflow/notes/` | Yes — shared meeting notes |
| `.neuroflow/hive/` | Yes — local cache of team data |
| `.neuroflow/sessions/` | No — gitignored (personal logs) |
| `.neuroflow/flowie/` | No — gitignored (personal profile) |

---

## Privacy and data governance

| What | Shared to Hive? |
|---|---|
| Research question | **Never** automatically — only if user explicitly runs `--share` |
| Session logs | **Never** |
| Raw data paths or outputs | **Never** |
| Analysis results | **Never** automatically — only with `--share` |
| Personal project_config.md fields | **Never** |
| Something the user explicitly approves via `--share` | Yes, after confirmation |

The Hive is **pull-first**: the researcher benefits from team knowledge without being required to share anything back.

---

## Authentication

Hive uses the same GitHub credentials as the user's local git config. The `gh` CLI (GitHub CLI) is preferred for push operations — check with `gh auth status`. If not available, fall back to constructing GitHub API calls with a PAT (personal access token) that the user provides.

Authentication instructions:
```bash
gh auth login   # recommended
# or configure git credentials for HTTPS push
```

---

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules
- `neuroflow:phase-flowie` — the personal-project counterpart to Hive; understand flowie before implementing Hive to avoid overlap
