Last run: 2026-04-02

## Issues found

---

### ISSUE 1 — Check 9d: Dead nav link — `docs/skills/setup/SKILL.md` missing (BLOCKING)

`mkdocs.yml` nav references `skills/setup/SKILL.md` (resolves to `docs/skills/setup/SKILL.md`) but this directory and file do not exist under `docs/`.

All 35 other skill folders have a corresponding `docs/skills/<name>/` directory. Only `setup` is absent. The source `skills/setup/SKILL.md` exists in the plugin root.

**Fix:** Create `docs/skills/setup/SKILL.md` matching the pattern used for all other skills.

---

## Checks that passed

- **Check 1 — Folder/frontmatter names:** All 36 skill folders, 24 agent files, and 33 command files match their `name:` frontmatter fields exactly. PASS
- **Check 2 — README tables:** All commands, skills, and agents have rows in their respective README tables. All table links resolve to existing files. PASS
- **Check 3 — Version sync:** All four version markers agree on `0.2.12`.
  - `plugin.json`: `0.2.12` PASS
  - `marketplace.json`: `0.2.12` PASS
  - `README.md` — `## What's new in 0.2.12` heading present PASS
  - `mkdocs.yml` `extra.version`: `"0.2.12"` PASS
  - `docs/index.md` `sa-bar-version`: `v0.2.12` PASS
  - `.neuroflow/project_config.md` `Plugin version`: `0.2.12` PASS
- **Check 3b — Self-assessment bar sync:** `sa-bar-version` reads `v0.2.12`, matches `plugin.json`. PASS
- **Check 4 — Dead references in modified files:**
  - `commands/notes.md` — all `neuroflow:phase-notes` skill ref resolves; no broken refs. PASS
  - `commands/flowie.md` — all `neuroflow:phase-flowie` skill ref resolves; `flowie_profile:` mention is documentation text (describing the old field to replace), not a live reference. PASS
  - `skills/phase-notes/SKILL.md` — `neuroflow:neuroflow-core` resolves; `neuroflow:notes` appears only in the slash command string `/neuroflow:notes` (valid invocation form, not a skill ref). PASS
  - `skills/phase-flowie/SKILL.md` — `neuroflow:neuroflow-core` resolves; `neuroflow:flowie` appears only in `/neuroflow:flowie` (valid command invocation). PASS
- **Check 5 — Naming overlaps:** `setup` exists as both `skills/setup/` and `commands/setup.md`. This overlap pre-dates 0.2.12 and is unchanged. No new overlaps introduced. PASS (pre-existing known deviation)
- **Check 6 — Command frontmatter completeness:** All 33 command files contain all five required fields (`name`, `description`, `phase`, `reads`, `writes`). PASS
- **Check 7 — .neuroflow subfolder purity:** `.neuroflow/` contains only `reasoning/` as a subfolder. No skill-named subfolders present. PASS
- **Check 8 — hooks.json audit:** Valid JSON. Both hook entries (`Edit|Write` matcher) have `type` and `command`. Error suppression verified:
  - Hook 1 (ruff formatter): `>/dev/null 2>&1` and `; true` both present. PASS
  - Hook 2 (flowie git-sync): `>/dev/null 2>&1` and `|| true` both present. PASS
  - README Hooks table documents both `ruff formatter` and `flowie git-sync` — matches `hooks.json` entries. PASS
- **Check 9a — mkdocs.yml version:** `extra.version: "0.2.12"` matches `plugin.json`. PASS
- **Check 9b — Command docs completeness:** All 33 command files have `docs/commands/<name>.md` and all appear in `mkdocs.yml` nav. PASS
- **Check 9c — Skill docs completeness (nav):** All 36 skill folders appear in `mkdocs.yml` nav. PARTIAL — `setup` skill is listed in nav but `docs/skills/setup/SKILL.md` is missing (see Issue 1).
- **Check 9d — No dead nav links:** One dead link found — see Issue 1 above. All other nav entries resolve to existing files. PARTIAL
- **Check 10 — Personal sensitive information:** No email addresses, passwords, secrets, private keys, or real personal names found in commands, agents, skills, docs, hooks, or README. PASS
- **Check 11 — mind.js sync:** All commands, skills, and agents present in the repo have corresponding nodes in `docs/javascripts/mind.js`. `/notes` and `/flowie` command nodes verified present. `phase-notes` and `phase-flowie` skill nodes verified present. `notes` and `flowie` agent nodes verified present. PASS
- **Check 12 — Flowie path hygiene:** No stale `.neuroflow/.flowie/` paths found in commands, skills, agents, or hooks. `flowie_profile:` occurrences in `commands/flowie.md` and `agents/sentinel-dev.md` and `agents/sentinel.md` are documentation text describing the old field name to detect — not live broken references. PASS
- **docs/changelog.md:** `## 0.2.12` entry present with correct content. PASS

---

## Summary

| # | Severity | Check | Status |
|---|----------|-------|--------|
| 1 | BLOCKING | `docs/skills/setup/SKILL.md` missing — dead mkdocs nav link | fix: create the file |

All other checks passed.
