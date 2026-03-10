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

Read `README.md`. Extract the Commands table, Skills table, and Agents table. Cross-check:
- Every command file in `commands/` must have a row in the Commands table
- Every skill folder in `skills/` must have a row in the Skills table
- Every agent file in `agents/` must have a row in the Agents table
- Every row in all three tables must point to a file that actually exists

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

### 7 — .neuroflow subfolder purity

List all subfolders inside `.neuroflow/` (directories only, not files). In the plugin repo, `.neuroflow/` may contain `reasoning/` (the structured decision log) and nothing else as a subfolder. No subfolders named after skills are permitted.

For each subfolder found:
- If the subfolder name is `reasoning/`: permitted — skip.
- Read the skill folder names from `skills/` (one folder per skill).
- If the subfolder name matches any skill folder name: flag as a structural error — **skills must not create their own named subfolders in `.neuroflow/`**. Only `reasoning/` is permitted as a subfolder in the plugin repo's `.neuroflow/`.
- If the subfolder name does not match a skill name and is not `reasoning/`: flag as an unrecognised subfolder and ask whether it is intentional.

Auto-fix: for skill-named subfolders, offer to delete the folder (after confirming with the user that any files inside can be discarded or relocated).

### 8 — hooks.json audit

Read `hooks/hooks.json`. Check:
- The file exists and is valid JSON.
- Every hook entry has a `matcher` and at least one `hooks` item with a `type` and `command`.
- Read `README.md`. If a Hooks section or table is present, verify that every hook matcher described in the README corresponds to an entry in `hooks.json`, and every entry in `hooks.json` is documented in the README.

Flag any hooks present in `hooks.json` but missing from README, or documented in README but absent from `hooks.json`.

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
