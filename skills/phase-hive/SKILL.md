---
name: phase-hive
description: Team-level knowledge layer for neuroflow. Connects a researcher's personal neuroflow project to a shared GitHub organisation repo where team research directions, cross-project findings, and recommended methods are coordinated. Use when the user wants to sync their work with a team, share findings explicitly, view team directions, or get team-aware recommendations. Never automatically copies personal project data to Hive — all sharing is explicit.
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/hive/hive.md
  - .neuroflow/hive/directions.md
  - .neuroflow/hive/sync.json
writes:
  - .neuroflow/hive/
  - .neuroflow/hive/hive.md
  - .neuroflow/hive/directions.md
  - .neuroflow/hive/sync.json
---

# phase-hive — Team research layer

Hive is the **team-level counterpart to flowie**. Where flowie tracks an individual researcher's project workflow and session state, Hive connects to a shared GitHub organisation private repo that the whole lab or team uses to:

- Announce shared research directions
- Share curated findings (always explicitly — never automatic)
- Coordinate recommended analysis methods and tools
- Broadcast relevant literature they want all team members to see

**Privacy rule (enforced absolutely):** Nothing from a personal `.neuroflow/` project is ever automatically sent to Hive. Every share is an explicit, intentional action by the researcher. The Hive is a shared workspace, not a surveillance layer.

---

## Hive repo structure (GitHub org private repo)

```
{org}/{hive-repo}/
├── hive.md              ← team identity: who we are, what we study, norms
├── directions.md        ← active research directions (updated by PIs / team leads)
├── sync.json            ← sync metadata: last pull per member, last push timestamps
└── shared/
    ├── methods/         ← recommended analysis methods and pipelines
    ├── literature/      ← curated papers the team wants everyone to read
    └── findings/        ← explicitly shared results and summaries
```

---

## Local hive state (per-project)

When a project has joined a Hive, the following folder exists:

```
.neuroflow/hive/
├── hive.md              ← local copy of team identity (pulled from org repo)
├── directions.md        ← local copy of team research directions
└── sync.json            ← sync metadata: hive_repo URL, last_pull, last_push, member_handle
```

---

## Command modes

This skill is invoked by the `/hive` command, which supports five modes:

### `--init`
Connect the current neuroflow project to a Hive repo for the first time.

1. Ask for the GitHub org and repo name: `{org}/{hive-repo}`
2. Ask for the researcher's GitHub handle (used as `member_handle` in sync.json)
3. Clone or fetch the hive repo to read `hive.md` and `directions.md`
4. Create `.neuroflow/hive/` with local copies of both files and an initial `sync.json`
5. Update `.neuroflow/flow.md` to add a `hive/` row
6. Write `hive_repo: {org}/{hive-repo}` and `hive_member: {handle}` to `project_config.md`
7. Confirm: print the team identity from `hive.md` and the active directions from `directions.md`

### `--sync`
Pull the latest state from the Hive repo and update local copies.

1. Fetch the latest `hive.md`, `directions.md`, and `sync.json` from the org repo
2. Update `.neuroflow/hive/hive.md` and `directions.md`
3. Update `sync.json` with `last_pull: [timestamp]`
4. Report what changed (diff summary: new directions, updated team info)
5. If any new directions overlap with the current project's research question or modality, highlight them as potentially relevant

### `--view`
Display the current state of the team Hive without syncing.

1. Read local `.neuroflow/hive/hive.md` and `directions.md`
2. Read `sync.json` to show when last synced
3. Print team identity, active directions, and last sync timestamp
4. Note: "Run `/hive --sync` to fetch the latest updates from the team."

### `--share`
Explicitly share a finding, method, or curation from this project to the Hive.

This is the **only** way anything from a personal project reaches the Hive. It is always user-initiated.

1. Ask what to share:
   - A finding (summary + file)
   - A recommended method or pipeline (markdown description)
   - A curated paper (citation + abstract + why it's relevant)
2. Ask for a title and one-line description
3. Compose the sharing entry and show it to the user for review
4. Only after explicit confirmation: push to `shared/{category}/{slug}.md` in the Hive repo via GitHub API (or gh CLI if available)
5. Update local `sync.json` with `last_push: [timestamp]` and a log entry
6. Confirm: "Shared to Hive: `shared/{category}/{slug}.md`"

If the user has not connected to a Hive (`--init` not run), stop and prompt them to run `/hive --init` first.

### `--recommend`
Get team-aware recommendations for the current project phase.

1. Read local `hive.md` and `directions.md`
2. Read the current project's `project_config.md` to know phase, modality, and research question
3. Check `shared/methods/` and `shared/literature/` in the Hive (if accessible) for relevant shared content
4. Surface:
   - Team directions that overlap with this project
   - Recommended methods shared by teammates for the same modality
   - Literature curated by the team relevant to the research question
5. Present as a compact digest: "Your team has shared X relevant items for your current phase"

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
