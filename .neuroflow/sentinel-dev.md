Last run: 2026-03-15

## Checks

- ✅ Check 1 — Frontmatter name consistency
- ✅ Check 3 — Version sync
- ✅ Check 4 — Dead skill/command references
- ✅ Check 6 — Command frontmatter completeness
- ✅ Check 8 — hooks.json validity
- ✅ Check 9a — mkdocs.yml version sync
- ✅ Check 9b — Command docs completeness
- ✅ Check 9c — Nav dead links

## All clear

_All checks passed — no issues found._

---

### Issues resolved this run

Three issues were found and fixed before this clean report:

1. **Check 4** — `skills/phase-paper/SKILL.md` referenced `neuroflow:scholar` which is an agent, not a skill. Fixed to `scholar` agent (no `neuroflow:` namespace).
2. **Check 9b** — `commands/hive.md` had no docs page. Created `docs/commands/hive.md` and added the `hive` entry to `mkdocs.yml` nav under Utilities.
3. **Check 9c** — `mkdocs.yml` nav referenced `skills/auto-issue/SKILL.md` which no longer exists (deleted, merged inline into neuroflow-core). Removed the dead nav entry. Also added missing skill nav entries: `phase-hive`, `notebooklm`, `pupil-labs-neon-realtime`.

<!-- old content below --
Last run: 2026-03-10

## Issues found

- **Naming overlap — agent `sentinel` and command `sentinel` share the same name.** `agents/sentinel.md` (`name: sentinel`) and `commands/sentinel.md` (`name: sentinel`) are identical. The agent is invoked by the command, so the overlap is structural, but it can cause confusion when referencing them in documentation or skill files. The previous run flagged this as intentional by design; noting here for completeness.

## Checks passed

### Check 1 — Folder name vs frontmatter name: PASS
All 16 `skills/*/SKILL.md` `name:` fields match their folder names exactly. All 3 agent files (`scholar`, `sentinel`, `sentinel-dev`) match their filenames. All 15 command files match their filenames.

### Check 2 — README tables: PASS
All 15 command files have a matching row in the Commands table. All 16 skill folders have a matching row in the Skills table. All table links resolve to existing files.

### Check 3 — Version sync: PASS
`plugin.json` version `0.1.3` matches the `## What's new in 0.1.3` heading in `README.md`.

### Check 4 — Dead references inside SKILL.md files: PASS
All `neuroflow:` references found across SKILL.md files (`neuroflow:neuroflow-core`, `neuroflow:review-neuro`) point to existing skill folders.

### Check 5 — Naming overlaps: NOTE (intentional)
`sentinel` is both a command name (`commands/sentinel.md`) and an agent name (`agents/sentinel.md`). Flagged previously as intentional by design. No other overlaps found between skill names, command names, and agent names.

### Check 6 — Command frontmatter completeness: PASS
All 15 command files contain the five required frontmatter fields: `name`, `description`, `phase`, `reads`, `writes`.

### Check 7 — plugin.json consistency: PASS
`plugin.json` contains: `name`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`, `mcpServers` (pubmed, biorxiv, miro, context7). All referenced MCP servers use standard `npx -y` invocation patterns. No issues found.
