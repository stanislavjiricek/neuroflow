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
2. **Your flowie** — your private repository is pulled and checked against the current formats; what is out of date (task files, a missing `.gitignore` line) is updated, committed and pushed to your repository. Changes you have not synced yet do not hold it back: it offers to sync them first, or leaves them uncommitted and out of the migration (if the plan has to change one of those files, it asks first).
3. **The team hive** — the hive is pulled and checked the same way, around any changes still waiting in your copy, which it never commits unless you agree. Anything that would change the shared hive is pushed only after your yes.

It shows the plan first and writes nothing until you agree. Running it a second time finds nothing to do.

Everyone who updates runs it once, even when a teammate has already brought the project up to date: then it finds the project current and checks only your flowie and the hive.

## How you find out

`project_config.md` records the neuroflow version the project was last brought up to date to (`plugin_version`). Only the setup of a new project and `/neuroflow:migrate` write it — switching phases or any other command leaves it alone, and it never goes down. When the installed version is newer, the first neuroflow command in each session says so in one line, until the project is migrated:

> neuroflow 0.2.22 is installed; this project is on 0.2.21 — run /neuroflow:migrate to bring the project, your flowie and the team hive up to date.

With the [neuroflow mod](concepts/mods.md), the same line stays in the band above the prompt until the project is migrated.

The notice reads the shared `project_config.md`, so once a teammate has migrated the project and pushed it, it no longer appears for you. Run `/neuroflow:migrate` once after your own update anyway: your flowie is yours to bring up to date.

## Updating the plugin

neuroflow 0.2.22 and later need Claude Code 2.1.271 or later: older versions cannot load the plugin, because its settings offer fixed choices (`userConfig` options). If yours is older, update Claude Code first — see [System requirements](installation.md#system-requirements).

Claude Code updates a plugin by itself only when auto-update is on for its marketplace, and for a marketplace you added yourself, such as neuroflow's, it is off by default. Turn it on in `/plugin` → **Marketplaces** → `neuroflow` → **Enable auto-update**: a new version is then fetched after a session starts and loads in the next one.

To update now, open `/plugin` → **Installed** → `neuroflow` → **Update now**, or run in your shell:

```
claude plugin marketplace update neuroflow
claude plugin update neuroflow@neuroflow
```

`/plugin marketplace update neuroflow` on its own only refreshes the catalog; the installed plugin stays as it was. Then run `/reload-plugins` (or restart Claude Code) and `/neuroflow:migrate` in your projects. What changed in each version is in the [changelog](changelog.md).
