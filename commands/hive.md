---
name: hive
description: Connect neuroflow to a shared team GitHub org repo for research direction coordination, explicit knowledge sharing, and team-aware recommendations. Use --init to connect, --sync to pull updates, --view to see team state, --share to explicitly push a finding, --recommend to get team-aware suggestions for the current phase. Never auto-shares personal project data.
phase: hive
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/hive/hive.md
  - .neuroflow/hive/directions.md
  - .neuroflow/hive/sync.json
writes:
  - .neuroflow/hive/
  - .neuroflow/hive/sync.json
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /hive

Read the `neuroflow:phase-hive` skill first. Then follow the neuroflow-core lifecycle.

---

## Step 0 — Check for .neuroflow/

If `.neuroflow/` does not exist, stop and tell the user to run `/neuroflow` first.

---

## Step 1 — Parse the mode flag

Parse the command for a mode flag. If no flag is given, default to `--view` if `.neuroflow/hive/` exists, or `--init` if it does not.

| Flag | Action |
|---|---|
| `--init` | Connect to a Hive repo for the first time |
| `--sync` | Pull the latest state + show change digest |
| `--view` | Display current Hive state without syncing |
| `--members` | View and edit the team roster |
| `--projects` | View and manage the lab project registry |
| `--ideas` | View and append to lab-wide cross-project ideas |
| `--tasks` | Show and manage the team Kanban board |
| `--recommend` | Get team-aware recommendations for the current phase |
| `--wiki` | Show team wiki overview |
| `--wiki-ingest` | Add a source to the team wiki (replaces --share) |
| `--wiki-query` | Query the team wiki |
| `--wiki-lint` | Health check the team wiki |
| `--wiki-add` | Add a page to the team wiki manually |
| `--wiki-schema` | View/edit team wiki conventions |

---

## Step 2 — Execute mode

Follow the instructions for the selected mode exactly as defined in `neuroflow:phase-hive`.

---

## Step 3 — Session log

Append a brief entry to `.neuroflow/sessions/YYYY-MM-DD.md`:

```
[HH:MM] /hive --{mode} — {one-line summary of what was done}.
```

Examples:
```
[14:23] /hive --init — Connected to acme-neuroscience/hive-lab. Team: ACME Neuro Lab. 3 active directions loaded.
[15:01] /hive --share — Shared finding: "ICA-cleaned EEG pipeline for auditory MMN" to shared/methods/eeg-mmn-pipeline.md.
[09:45] /hive --sync — Pulled 2 new directions and 1 new curated paper from team Hive.
```
