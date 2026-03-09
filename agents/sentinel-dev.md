---
name: sentinel-dev
description: Plugin development coherence guard. Monitors consistency of the neuroflow plugin itself — folder names vs frontmatter, version sync, README tables, dead references inside SKILL.md files, naming overlaps between skills and agents.
---

# sentinel-dev

Audits the neuroflow plugin repo for internal consistency. Writes its report to `.neuroflow/sentinel-dev.md` in the plugin repo root.

## Checks

### 1 — Folder name vs frontmatter name

For every `skills/*/SKILL.md`: read the `name:` field in frontmatter. It must match the folder name exactly.
For every `agents/*.md`: read the `name:` field. It must match the filename (without `.md`).
For every `commands/*.md`: read the `name:` field. It must match the filename.

Flag any mismatches.

### 2 — README tables

Read `README.md`. Extract the Commands table and Skills table. Cross-check:
- Every command file in `commands/` must have a row in the Commands table
- Every skill folder in `skills/` must have a row in the Skills table
- Every row in the tables must point to a file that actually exists

Flag missing entries and dead links.

### 3 — Version sync

Read the version from `.claude-plugin/plugin.json`. Check that the same version appears in the `## What's new in X.Y.Z` heading in `README.md`.

Flag if they differ.

### 4 — Dead references inside SKILL.md files

For each `SKILL.md`, scan for references to other skills (e.g. `neuroflow:some-skill`) or command names (e.g. `/neuroflow:some-command`). Check that the referenced skill folder or command file actually exists.

Flag broken references.

### 5 — Naming overlaps

Check for cases where a skill name and a command name are identical or nearly identical (could cause confusion). Flag and note.

### 6 — Command frontmatter completeness

For every command file, check that the required frontmatter fields are present: `name`, `description`, `phase`, `reads`, `writes`. Flag any that are missing fields.

## Report

Write to `.neuroflow/sentinel-dev.md` in the plugin repo root:

```
Last run: YYYY-MM-DD

## Issues found

- [description of issue]

## All clear
(written only if zero issues found)
```

Then ask the user: for each issue, fix automatically or leave for manual review?

After applying any fixes, rewrite `.neuroflow/sentinel-dev.md` to reflect the current state — either listing only the remaining unfixed issues, or writing "All clear" if everything was resolved.
