---
name: meeting
description: First-class meeting command — schedule meetings, prepare agendas with project context, send calendar invites, take structured notes, and auto-create tasks from action items. Supports project, flowie, and hive levels.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/tasks/**
  - .neuroflow/meetings/config.json
  - .neuroflow/meetings/*.md
  - .neuroflow/hive/hive.md
  - .neuroflow/flowie/profile.md
  - .neuroflow/flowie/meetings/config.json
  - .neuroflow/flowie/meetings/*.md
writes:
  - .neuroflow/meetings/
  - .neuroflow/meetings/config.json
  - .neuroflow/flowie/meetings/
  - .neuroflow/flowie/meetings/config.json
  - .neuroflow/tasks/**
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /meeting

First-class meeting management for neuroflow. Distinct from `/notes` (which captures unstructured live input) — `/meeting` is for planned meetings with agenda, attendees, calendar integration, and action-item-to-task conversion.

Read the `neuroflow:phase-meeting` skill first. Then follow the neuroflow-core lifecycle.

---

## Step 0 — Check for .neuroflow/

If `.neuroflow/` does not exist, stop and tell the user to run `/neuroflow` first.

---

## Step 1 — Parse mode flag

If no flag given: default to `--list` if any meeting files exist, otherwise `--new`.

| Flag | Action |
|------|--------|
| `--new` | Schedule a new meeting |
| `--prepare <slug>` | Prepare agenda with project context |
| `--view <slug>` | Show meeting file with task status inline |
| `--list` | List all meetings at current level |
| `--invite <slug>` | (Re)send calendar invites |
| `--close <slug>` | Finalize meeting and convert action items to tasks |
| `--init` | Set up recurring meeting templates |

Parse `--level project|flowie|hive` (default: `project`).

---

## Step 2 — Execute mode

Follow the instructions in `neuroflow:phase-meeting` for the selected mode.

---

## Step 3 — Session log

Append to `.neuroflow/sessions/YYYY-MM-DD.md`:

```
[HH:MM] /meeting --{mode} — {one-line summary}
```

Examples:
```
[09:00] /meeting --new — created Weekly Lab Meeting 2026-04-20 (hive level), sent invites to 4 attendees
[09:30] /meeting --prepare weekly-lab-2026-04-20 — populated agenda with 3 active tasks and 2 hive directions
[10:00] /meeting --close weekly-lab-2026-04-20 — created 3 project tasks from action items
```
