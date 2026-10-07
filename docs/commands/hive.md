# /hive

Connect your neuroflow project to a shared team Hive repo for research coordination, knowledge sharing, and team-aware recommendations.

The `/hive` command links a researcher's project to a GitHub organisation private repo that the whole lab shares. Hive caches are stored globally at `~/.neuroflow/hives/{org-repo}/` — never inside a project repo.

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
| `--tasks` | Show and manage the team Kanban board (same format as [`/tasks`](tasks.md)) |
| `--errata` | View known problems in shared datasets, or add one with `--errata --add` |
| `--doctor` | Check your setup — GitHub auth, hive clone, roster entry, private flowie, ignored secrets |
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
4. Clones the hive repo into `~/.neuroflow/hives/{org-repo}/` and writes your local `sync.json` (never pushed)
5. Updates `project_config.md` with `hive_repo:`

### `--sync`
1. Pulls the hive repo into your local clone at `~/.neuroflow/hives/{org-repo}/`
2. Reports what changed — new directions, updated members, new ideas, new errata, wiki and task changes (what changed, not who did what)
3. Highlights directions that overlap with your current project's modality or research question
4. Flags new errata for any shared dataset your project's memory mentions — deciding what they affect stays with you

### `--view`
Displays the current local Hive state without fetching from the org repo. Shows team identity, active research directions, member count, and the last sync timestamp.

### `--errata`
Known problems in shared datasets — a trigger offset in one subject, a mislabelled session, a dead channel — live in `errata/{dataset-id}.md` in the hive repo, one append-only table per dataset. `--errata --add` asks for the dataset, scope, problem and workaround, shows the row, and pushes it after you confirm. Scopes use dataset labels only (`sub-07`, `ses-02`), never participant identifiers.

### `--doctor`
A read-only checklist for new and existing members: GitHub CLI signed in, hive cache is an up-to-date git clone, your handle is in the roster, the project is linked, your flowie repo is private and fully pushed, and `integrations.json` is ignored in both the project and flowie. Each failing row comes with the exact command that fixes it.

### `--recommend`
Queries the Hive's wiki, directions, and ideas to generate recommendations tuned to your current phase and research question.

---

## Lab review checklist

A hive can carry a `review_checklist.md` — the lab's own rubric (one checkbox per item). When it is present, `/paper`'s critic step and `/review` add its items to their checklist.

---

## Privacy rule

**Nothing from your personal `.neuroflow/` project is ever automatically sent to Hive.** Every share is an explicit, intentional action, and every push to the hive repo is shown to you first. The Hive is a coordination layer, not a surveillance layer: neuroflow never infers or broadcasts anyone's presence, activity, working hours, progress or mood, and your pull/push times stay on your machine.

---

## Hive repo structure

The shared GitHub org repo follows this layout:

```
{org}/{hive-repo}/
├── hive.md          ← team identity, norms, and active research directions
├── members.md       ← team roster: name, email, github, role
├── ideas.md         ← cross-project team hypotheses and open questions
├── review_checklist.md ← optional lab review rubric
├── errata/          ← known problems in shared datasets
├── projects/        ← lab project registry
├── tasks/           ← team Kanban board
├── meetings/        ← team meeting files
└── wiki/            ← team knowledge base
```

---

## Local hive cache

Hive data is cached globally — not inside any project repo. The cache is a git clone of the hive repo:

```
~/.neuroflow/hives/{org-repo}/
├── hive.md          ← team identity + directions
├── members.md       ← team roster
├── ideas.md         ← team ideas
├── sync.json        ← your hive_repo URL, last_pull, last_push, member_handle (local only, never pushed)
└── …                ← errata/, tasks/, meetings/, wiki/
```

---

## Related

- [`neuroflow:phase-hive`](../skills/phase-hive/SKILL.md) — full skill with mode-by-mode implementation details
- [`/flowie`](flowie.md) — individual workflow coordinator (personal counterpart to Hive)
