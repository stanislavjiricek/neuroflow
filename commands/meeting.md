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
  - ~/.neuroflow/hives/{org-repo}/hive.md
  - ~/.neuroflow/hives/{org-repo}/members.md
  - ~/.neuroflow/flowie/profile.md
  - ~/.neuroflow/flowie/meetings/config.json
  - ~/.neuroflow/flowie/meetings/*.md
writes:
  - .neuroflow/meetings/
  - .neuroflow/meetings/config.json
  - .neuroflow/notes/.capturing              # live-capture flag the neuroflow mod reads (--notes)
  - ~/.neuroflow/flowie/meetings/
  - ~/.neuroflow/flowie/meetings/config.json
  - ~/.neuroflow/hives/{org-repo}/meetings/
  - .neuroflow/tasks/**
  - ~/.neuroflow/flowie/tasks/**
  - ~/.neuroflow/hives/{org-repo}/tasks/**
  - .neuroflow/sessions/YYYY-MM-DD.md
lifecycle: light
produces:
  - .neuroflow/meetings/
next:
  - tasks
---

# /meeting

First-class meeting management for neuroflow. Distinct from `/notes` (which captures unstructured live input) — `/meeting` is for planned meetings with agenda, attendees, calendar integration, and action-item-to-task conversion.

Read the `neuroflow:phase-meeting` skill first. Then follow the neuroflow-core lifecycle — open with its version notice when the project's `plugin_version` is missing or older than the running neuroflow's version in `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` (**Command lifecycle**, step 3). Action items are converted to tasks following the canonical board spec in `/tasks` (`commands/tasks.md`) — `/tasks` owns the 3-tier task model.

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
| `--notes <slug>` | Take live notes into the meeting file (same capture format as `/notes`) |
| `--view <slug>` | Show meeting file with task status inline |
| `--list` | List meetings at current level — next upcoming and not-yet-closed first |
| `--invite <slug>` | (Re)send calendar invites — only after the person confirms the recipient list |
| `--close <slug>` | Finalize meeting and convert action items to tasks (`scripts/meeting_close.py`, dry run first) |
| `--init` | Set up recurring meeting templates |

Parse `--level project|flowie|hive` (default: `project`).

---

## Step 2 — Execute mode

Follow the instructions in `neuroflow:phase-meeting` for the selected mode.

---

## Step 3 — Session log

Append to `.neuroflow/sessions/YYYY-MM-DD.md` (canonical format — neuroflow-core → Command lifecycle):

```
## HH:MM — [meeting] --{mode}: {one-line summary}
```

Examples:
```
## 09:00 — [meeting] --new: created Weekly Lab Meeting 2026-04-20 (hive level), sent invites to 4 attendees
## 09:30 — [meeting] --prepare weekly-lab-2026-04-20: populated agenda with 3 active tasks and 2 hive directions
## 10:00 — [meeting] --close weekly-lab-2026-04-20: created 3 project tasks from action items
```
