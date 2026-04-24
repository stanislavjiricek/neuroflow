Last run: 2026-04-03

## Issues found

---

### ISSUE 1 — Check 9b/9d: `docs/commands/autoresearch.md` missing — dead nav link (BLOCKING)

`mkdocs.yml` nav references `commands/autoresearch.md` (resolves to `docs/commands/autoresearch.md`) but this file does not exist under `docs/commands/`. All other 33 command files have a corresponding docs page; only `autoresearch` is absent. The MkDocs build will fail.

**Fix:** Create `docs/commands/autoresearch.md` following the pattern of any other command docs page.

---

### ISSUE 2 — Check 9c/9d: `docs/skills/autoresearch/` missing — dead nav link (BLOCKING)

`mkdocs.yml` nav references `skills/autoresearch/SKILL.md` (resolves to `docs/skills/autoresearch/SKILL.md`) but neither the directory nor the file exists under `docs/skills/`. The MkDocs build will fail.

**Fix:** Create `docs/skills/autoresearch/SKILL.md` as a docs mirror of `skills/autoresearch/SKILL.md`.

---

### ISSUE 3 — Check 9c/9d: `docs/skills/setup/` missing — dead nav link (BLOCKING)

`mkdocs.yml` nav references `skills/setup/SKILL.md` (resolves to `docs/skills/setup/SKILL.md`) but this directory does not exist under `docs/skills/`. Pre-existing issue carried over from v0.2.12.

**Fix:** Create `docs/skills/setup/SKILL.md` as a docs mirror of `skills/setup/SKILL.md`.

---

### ISSUE 4 — Check 12: Stale `.neuroflow/.flowie/` paths in docs files (BLOCKING)

The following `docs/` files contain the old `.neuroflow/.flowie/` path (should be `.neuroflow/flowie/`) and stale field names (`flowie_profile` / `flowie_project` — both replaced by the `flowie_profiles:` list). These are the built website source files, not the plugin source — users reading the live docs will see the stale canonical path.

- `docs/agents/flowie.md` line 16: `.neuroflow/.flowie/profile.md`
- `docs/agents/flowie.md` line 50: `.neuroflow/.flowie/`
- `docs/skills/phase-flowie/SKILL.md` line 3 (description): `.neuroflow/.flowie/`
- `docs/skills/phase-flowie/SKILL.md` line 12: `.neuroflow/.flowie/`
- `docs/skills/phase-flowie/SKILL.md` line 24: `.neuroflow/.flowie/profile.md` and `flowie_profile` field reference
- `docs/skills/phase-flowie/SKILL.md` lines 62, 64, 69, 70, 88: `.neuroflow/.flowie/`

Note: The plugin source files (`skills/phase-flowie/SKILL.md`, `agents/flowie.md`) are already clean. Only the `docs/` mirror copies carry stale paths. The `docs/changelog.md` reference is an intentional historical note documenting the rename — do not change it.

**Fix:** Update `docs/agents/flowie.md` and `docs/skills/phase-flowie/SKILL.md` — replace `.neuroflow/.flowie/` with `.neuroflow/flowie/`, `flowie_profile` with `flowie_profiles:` list, and `flowie_project:` scalar with `flowie_profiles:` list.

---

### ISSUE 5 — Check 2a: `autoresearch` command missing from README Commands table (HIGH)

`commands/autoresearch.md` exists but has no row in the README Commands table (under the "Utility" section or any section). The command is mentioned only in the `## What's new in 0.2.13` section.

**Fix:** Add a row for `/autoresearch` to the README Commands table under "Utility".

---

### ISSUE 6 — Check 2b: `autoresearch` skill missing from README Skills table (HIGH)

`skills/autoresearch/SKILL.md` exists but has no row in the README Skills table.

**Fix:** Add a row for `neuroflow:autoresearch` to the README Skills table.

---

### ISSUE 7 — Check 2c: `autoresearch` agent missing from README Agents table (HIGH)

`agents/autoresearch.md` exists but has no row in the README Agents table.

**Fix:** Add a row for `autoresearch` to the README Agents table.

---

### ISSUE 8 — Check 2c: README Agents table contains 16 dead links (HIGH)

The following 16 agent files were deleted in v0.2.13 but their rows remain in the README Agents table:

- `agents/ideation.md`
- `agents/grant-proposal.md`
- `agents/experiment.md`
- `agents/tool-build.md`
- `agents/tool-validate.md`
- `agents/data.md`
- `agents/data-preprocess.md`
- `agents/data-analyze.md`
- `agents/notes.md`
- `agents/write-report.md`
- `agents/brain-build.md`
- `agents/brain-optimize.md`
- `agents/brain-run.md`
- `agents/review.md`
- `agents/critic.md`
- `agents/orchestrator.md`

**Fix:** Remove all 16 rows from the README Agents table.

---

### ISSUE 9 — Check 11: Stale entries in `mind.js` NODE_PHASE_MAP (LOW)

Two entries in `NODE_PHASE_MAP` reference node IDs that do not exist in the `NODES` array (deleted agents):

- `"ag-ideation": "ideation"` — no `ag-ideation` node in NODES
- `"ag-orchestrator": "utility"` — no `ag-orchestrator` node in NODES

These are orphaned map keys that are unused but should be cleaned up.

**Fix:** Remove `"ag-ideation"` and `"ag-orchestrator"` from `NODE_PHASE_MAP` in `docs/javascripts/mind.js`.

---

### ISSUE 10 — Check 11: 9 nodes missing from `mind.js` NODE_PHASE_MAP (LOW)

The following node IDs exist in the `NODES` array but are absent from `NODE_PHASE_MAP`. They will default to the "utility" cluster, which is acceptable for most but may misplace `sk-flowie`, `sk-hive`, `sk-slideshow`, and `sk-autoresearch`:

- `sk-humanizer` (reasonable to leave in utility)
- `sk-flowie` (should map to "flowie")
- `sk-hive` (should map to "hive")
- `sk-slideshow` (should map to "slideshow")
- `sk-autoresearch` (reasonable to leave in utility)
- `ag-sentinel` (reasonable to leave in utility)
- `ag-sentinel-dev` (reasonable to leave in utility)
- `ag-scholar` (should map to "ideation")
- `ag-autoresearch` (reasonable to leave in utility)

**Fix:** Add entries for `sk-flowie`, `sk-hive`, `sk-slideshow`, and `ag-scholar` to NODE_PHASE_MAP with their correct phases. The remaining five can stay in utility or be added as desired.

---

## Checks that passed

- **Check 1 — Folder/frontmatter names:** All 37 skill folders, 9 agent files, and 34 command files match their `name:` frontmatter fields. PASS
- **Check 3 — Version sync:** All four version markers agree on `0.2.13`.
  - `.claude-plugin/plugin.json`: `0.2.13` PASS
  - `.claude-plugin/marketplace.json`: `0.2.13` PASS
  - `README.md` heading: `## What's new in 0.2.13` PASS
  - `mkdocs.yml` `extra.version`: `"0.2.13"` PASS
- **Check 3b — Self-assessment bar sync:** `docs/index.md` `sa-bar-version` reads `v0.2.13`, matches `plugin.json`. PASS
- **Check 4 — Dead references in SKILL.md files:** No broken `neuroflow:some-skill` or `/neuroflow:some-command` refs found in surviving skill files. The `worker-critic` "orchestrator" mentions are role descriptions, not agent file references. PASS
- **Check 5 — Naming overlaps:** `autoresearch` exists as both skill and agent — mirrors the established `sentinel`/`flowie` pattern. No new confusing overlaps introduced. PASS
- **Check 6 — Command frontmatter completeness:** All 34 command files have all five required fields (`name`, `description`, `phase`, `reads`, `writes`). PASS
- **Check 7 — .neuroflow subfolder purity:** Only `reasoning/` and `sessions/` subfolders present. No skill-named subfolders. PASS
- **Check 8 — hooks.json audit:** Valid JSON. Both hooks have `type` and `command`. Error suppression confirmed on both. README Hooks table matches `hooks.json`. PASS
- **Check 9a — mkdocs.yml version:** `extra.version: "0.2.13"` matches `plugin.json`. PASS
- **Check 10 — Personal sensitive information:** No email addresses (outside synthetic domains), passwords, secrets, private keys, or real personal names found across all scanned paths. PASS
- **Check 11 — mind.js NODES coverage:** All current skills, commands, and agents have nodes in `mind.js`. PASS (NODE_PHASE_MAP issues are cosmetic only — see Issues 9 and 10)
- **docs/changelog.md:** `## 0.2.13` entry present. PASS

---

## Summary

| # | Severity | Check | Description |
|---|----------|-------|-------------|
| 1 | BLOCKING | 9b/9d | `docs/commands/autoresearch.md` missing — dead mkdocs nav link |
| 2 | BLOCKING | 9c/9d | `docs/skills/autoresearch/SKILL.md` missing — dead mkdocs nav link |
| 3 | BLOCKING | 9c/9d | `docs/skills/setup/SKILL.md` missing — dead mkdocs nav link (pre-existing) |
| 4 | BLOCKING | 12 | Stale `.neuroflow/.flowie/` paths in `docs/agents/flowie.md` and `docs/skills/phase-flowie/SKILL.md` |
| 5 | HIGH | 2a | `/autoresearch` missing from README Commands table |
| 6 | HIGH | 2b | `neuroflow:autoresearch` skill missing from README Skills table |
| 7 | HIGH | 2c | `autoresearch` agent missing from README Agents table |
| 8 | HIGH | 2c | 16 dead agent links in README Agents table (deleted in v0.2.13) |
| 9 | LOW | 11 | `mind.js` NODE_PHASE_MAP: stale `ag-ideation` and `ag-orchestrator` entries |
| 10 | LOW | 11 | `mind.js` NODE_PHASE_MAP: 9 nodes missing (will default to utility cluster) |
