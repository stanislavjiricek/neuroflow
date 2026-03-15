# /hive

Connect your neuroflow project to a shared team Hive repo for research direction coordination and knowledge sharing.

The `/hive` command links an individual researcher's project to a GitHub organisation private repo that the whole lab shares. It lets you pull team research directions, share findings explicitly, and get team-aware recommendations — without ever automatically exposing your personal project data.

---

## Modes

Run `/hive` with one of the following flags:

| Flag | What it does |
|---|---|
| `--init` | Connect to a Hive repo for the first time |
| `--sync` | Pull the latest team directions and shared content |
| `--view` | Display current Hive state without syncing |
| `--share` | Explicitly push a finding, method, or paper to Hive |
| `--recommend` | Get team-aware suggestions for your current phase |

If no flag is given, defaults to `--view` when already connected, or `--init` when not yet connected.

---

## What it does

### `--init`
1. Asks for the GitHub org and Hive repo name (`{org}/{hive-repo}`)
2. Asks for your GitHub handle
3. Fetches `hive.md` (team identity) and `directions.md` (active directions) from the org repo
4. Creates `.neuroflow/hive/` with local copies and `sync.json`
5. Updates `project_config.md` with `hive_repo` and `hive_member`

### `--sync`
1. Fetches the latest `hive.md`, `directions.md`, and `sync.json` from the org repo
2. Updates local `.neuroflow/hive/` copies
3. Reports what changed — new directions, updated team info
4. Highlights directions that overlap with your current project's modality or research question

### `--view`
Displays the current local Hive state without fetching from the org repo. Shows team identity, active research directions, and the last sync timestamp.

### `--share`
Lets you explicitly share a finding, method summary, or curated paper to the Hive. You choose what to share — nothing is automatic.

1. Asks what you want to share: finding, method, or literature
2. Asks for a summary title and the content (or a path to a file)
3. Writes the share to `shared/{category}/{filename}.md` in the Hive repo
4. Updates `sync.json` with `last_push: [timestamp]`

### `--recommend`
Queries the Hive's shared methods, directions, and literature to generate recommendations tuned to your current phase and research question.

---

## Privacy rule

**Nothing from your personal `.neuroflow/` project is ever automatically sent to Hive.** Every share is an explicit, intentional action. The Hive is a coordination layer, not a surveillance layer.

---

## Hive repo structure

The shared GitHub org repo follows this layout:

```
{org}/{hive-repo}/
├── hive.md              ← team identity and norms
├── directions.md        ← active research directions
├── sync.json            ← per-member sync metadata
└── shared/
    ├── methods/         ← recommended pipelines and analysis methods
    ├── literature/      ← curated papers for the team
    └── findings/        ← explicitly shared results and summaries
```

---

## Local state

When connected, Hive creates:

```
.neuroflow/hive/
├── hive.md              ← local copy of team identity
├── directions.md        ← local copy of team directions
└── sync.json            ← hive_repo URL, last_pull, last_push, member_handle
```

---

## Related

- [`neuroflow:phase-hive`](../skills/phase-hive/SKILL.md) — full skill with mode-by-mode implementation details
- [`/flowie`](flowie.md) — individual workflow coordinator (personal counterpart to Hive)
