---
title: Three levels
---

# You, the project, the team

neuroflow keeps memory at three levels. Each level is a git repository of plain files, so it travels, merges and keeps its history like code.

| Level | Where | Who sees it | Holds |
|---|---|---|---|
| **You** | `~/.neuroflow/flowie/`, your private flowie repository | you | profile and writing style, ideas, your task board across projects, project registry, notes, meetings, personal wiki |
| **The project** | `.neuroflow/` in the project's repository | everyone on the project | configuration, objectives, timeline, task board, meetings, decisions with their reasons, wiki, phase folders |
| **The team** | a hive repository for the lab, cloned to `~/.neuroflow/hives/` | the lab | members, projects, research directions and ideas, team board, known problems in shared datasets, team wiki |

Personal settings and consents stay outside every repository, in `~/.neuroflow/user.yaml`.

## What lives at each level

| | You | The project | The team |
|---|---|---|---|
| Tasks | `/flowie --tasks` | [`/tasks`](../commands/tasks.md) | `/hive --tasks` |
| Wiki | `/flowie --wiki-*` | [`/wiki`](../commands/wiki.md) | `/hive --wiki-*` |
| Meetings | `/meeting` at flowie level | [`/meeting`](../commands/meeting.md) | `/meeting` at hive level |
| Overview | [`/flowie`](../commands/flowie.md) | [`/dashboard`](../commands/dashboard.md) | [`/hive --view`](../commands/hive.md) |

One task format serves all three boards, so an action item from a meeting can land on any of them.

## What crosses between levels

- **Into the project** — nothing personal. Your profile shapes how Claude helps you; it is never written into papers, reports, grants or slides.
- **Into the team** — only what you share explicitly, such as a finding pushed to the team wiki. Pushes to a shared hive happen only after your yes in that turn.
- **Out of your machine** — daily session logs, review copies of confidential manuscripts and the wiki capture queue never leave it.

The exact rules are the sharing tiers in [project memory](project-memory.md).

## Keeping the levels up to date

After neuroflow updates, run [`/neuroflow:migrate`](../commands/migrate.md) once per project. It brings the project, your flowie and the team hive to the current version, shows the plan first and changes nothing until you agree. → [Upgrading](../upgrading.md)
