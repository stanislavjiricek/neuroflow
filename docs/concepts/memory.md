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

## One project, one card

A project is described once. A team project's card — status, phase, description, repositories — lives in the team's hive; a personal project's lives in your flowie. Your flowie keeps only a pointer to a team project, with your own notes, so the two can never disagree. A phase change or a new status is written on the card, wherever you make it; for a hive card you see the change and confirm before it is pushed. Registries from before this rule hold two cards for some projects: [`/neuroflow:migrate`](../commands/migrate.md) folds them, asking which value wins where they differ, and [`/sentinel`](../commands/sentinel.md) reports what is left.

Tasks stay on three boards, and each goes on the narrowest one everyone who must see it can read: only you — your flowie; the team — the hive (the default for a team project); the people working in one repository, about its code — that repository's board. [`/tasks --project {id}`](../commands/tasks.md) shows one project's open tasks from every board at once, including the boards of its repositories that are not checked out on this machine, fetched into a local cache each time.

## What crosses between levels

- **Into the project** — nothing personal. Your profile shapes how Claude helps you; it is never written into papers, reports, grants or slides.
- **Into the team** — only what you share explicitly, such as a finding pushed to the team wiki. Pushes to a shared hive happen only after your yes in that turn.
- **Out of your machine** — daily session logs, review copies of confidential manuscripts and the wiki capture queue never leave it.

The exact rules are the sharing tiers in [project memory](project-memory.md).

## Keeping the levels up to date

After neuroflow updates, run [`/neuroflow:migrate`](../commands/migrate.md) once per project. It brings the project, your flowie and the team hive to the current version, shows the plan first and changes nothing until you agree. → [Upgrading](../upgrading.md)
