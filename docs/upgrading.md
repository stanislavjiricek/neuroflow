---
title: Upgrading
---

# Upgrading

When a new version of neuroflow is installed, run one command in each project:

```
/neuroflow:migrate
```

It brings everything neuroflow keeps up to the version you run, level by level:

1. **The project** — `.neuroflow/` to the current memory contract: the `project_config.md` frontmatter, reasoning logs as JSON Lines, the merge-safe `.gitattributes` and local-only `.gitignore` lines, the instruction block in `.claude/CLAUDE.md`, and the neuroflow version the project is now up to date with.
2. **Your flowie** — your private repository is pulled and checked against the current formats; what is out of date (task files, a missing `.gitignore` line) is updated, committed and pushed to your repository.
3. **The team hive** — the hive is pulled and checked the same way. Anything that would change the shared hive is pushed only after your yes.

It shows the plan first and writes nothing until you agree. Running it a second time finds nothing to do.

Everyone who updates runs it once, even when a teammate has already brought the project up to date: then it finds the project current and checks only your flowie and the hive.

## How you find out

`project_config.md` records the neuroflow version the project was last brought up to date to (`plugin_version`). Only the setup of a new project and `/neuroflow:migrate` write it — switching phases or any other command leaves it alone, and it never goes down. When the installed version is newer, the first neuroflow command in each session says so in one line, until the project is migrated:

> neuroflow 0.2.22 is installed; this project is on 0.2.21 — run /neuroflow:migrate to bring the project, your flowie and the team hive up to date.

With the [neuroflow mod](concepts/mods.md), the same line stays in the band above the prompt until the project is migrated.

## Updating the plugin

Claude Code updates plugins from their marketplace; with auto-update on, a new version arrives by itself. To fetch it now:

```
/plugin marketplace update neuroflow
```

Then restart Claude Code and run `/neuroflow:migrate` in your projects. What changed in each version is in the [changelog](changelog.md).
