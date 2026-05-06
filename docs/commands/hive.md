# /hive

Connect your neuroflow project to a shared team Hive repo for research coordination, knowledge sharing, and team-aware recommendations.

The `/hive` command links a researcher's project to a GitHub organisation private repo that the whole lab shares. Hive caches are stored globally at `~/.neuroflow/hive/{org-repo}/` — never inside a project repo.

---

## Modes

Run `/hive` with one of the following flags:

| Flag | What it does |
|---|---|
| `--init` | Connect to a Hive repo for the first time |
| `--sync` | Pull the latest team state + show change digest |
| `--view` | Display current Hive state without syncing |
| `--members` | View and edit the team roster |
| `--projects` | View and manage the lab project registry |
| `--ideas` | View and append to lab-wide cross-project ideas |
| `--tasks` | Show and manage the team Kanban board |
| `--recommend` | Get team-aware suggestions for your current phase |
| `--wiki-ingest` | Add a source to the team wiki |
| `--wiki-query` | Query the team wiki |
| `--wiki-lint` | Health check the team wiki |

If no flag is given, defaults to `--view` when already connected, or `--init` when not yet connected.

---

## What it does

### `--init`
1. Checks your `~/.neuroflow/flowie/profile.md` for known hives (shows picker if found)
2. Asks for the GitHub org and Hive repo name (`{org}/{hive-repo}`)
3. Asks for your GitHub handle
4. Creates `~/.neuroflow/hive/{org-repo}/` with local copies and `sync.json`
5. Updates `project_config.md` with `hive_repo:`

### `--sync`
1. Fetches the latest `hive.md`, `members.md`, `ideas.md`, and `sync.json` from the org repo
2. Updates local `~/.neuroflow/hive/{org-repo}/` copies
3. Reports what changed — new directions, updated members, new ideas
4. Highlights directions that overlap with your current project's modality or research question

### `--view`
Displays the current local Hive state without fetching from the org repo. Shows team identity, active research directions, member count, and the last sync timestamp.

### `--recommend`
Queries the Hive's wiki, directions, and ideas to generate recommendations tuned to your current phase and research question.

---

## Privacy rule

**Nothing from your personal `.neuroflow/` project is ever automatically sent to Hive.** Every share is an explicit, intentional action. The Hive is a coordination layer, not a surveillance layer.

---

## Hive repo structure

The shared GitHub org repo follows this layout:

```
{org}/{hive-repo}/
├── hive.md          ← team identity, norms, and active research directions
├── members.md       ← team roster: name, email, github, role
├── ideas.md         ← cross-project team hypotheses and open questions
├── sync.json        ← per-member sync metadata
├── projects/        ← lab project registry
├── tasks/           ← team Kanban board
├── meetings/        ← team meeting files
└── wiki/            ← team knowledge base
```

---

## Local hive cache

Hive data is cached globally — not inside any project repo:

```
~/.neuroflow/hive/{org-repo}/
├── hive.md          ← local copy of team identity + directions
├── members.md       ← local copy of team roster
├── ideas.md         ← local copy of team ideas
└── sync.json        ← hive_repo URL, last_pull, last_push, member_handle
```

---

## Related

- [`neuroflow:phase-hive`](../skills/phase-hive/SKILL.md) — full skill with mode-by-mode implementation details
- [`/flowie`](flowie.md) — individual workflow coordinator (personal counterpart to Hive)
