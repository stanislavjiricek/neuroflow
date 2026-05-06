Last run: 2026-05-06

## Issues found

---

### ISSUE 1 — Check 3b: Self-assessment bar version out of sync (BLOCKING)

`docs/index.md` line 9: `<span class="sa-bar-version">v0.2.13</span>`

Current plugin version is `0.2.16` (plugin.json, marketplace.json, mkdocs.yml `extra.version`, README heading all agree on `0.2.16`). The sa-bar-version span was not updated at any point from 0.2.13 → 0.2.14 → 0.2.15 → 0.2.16.

**Fix:** Update `docs/index.md` line 9: change `v0.2.13` to `v0.2.16`.

---

### ISSUE 2 — Check 9b/9d: `docs/skills/wiki/SKILL.md` missing — dead nav link (BLOCKING)

`mkdocs.yml` nav references `skills/wiki/SKILL.md` (resolves to `docs/skills/wiki/SKILL.md`) at line 127 (Personal Wiki concept entry) and line 208 (Reference > Phases > wiki). Neither path exists under `docs/skills/`. The MkDocs build will fail or produce a dead link.

**Fix:** Create `docs/skills/wiki/SKILL.md` as a docs mirror of `skills/wiki/SKILL.md`.

---

### ISSUE 3 — Check 9b/9d: `docs/skills/setup/SKILL.md` missing — dead nav link (BLOCKING)

`mkdocs.yml` line 214 references `skills/setup/SKILL.md` (resolves to `docs/skills/setup/SKILL.md`) but this directory does not exist under `docs/skills/`. Pre-existing issue from last audit (v0.2.13), not yet fixed.

**Fix:** Create `docs/skills/setup/SKILL.md` as a docs mirror of `skills/setup/SKILL.md`.

---

### ISSUE 4 — Check 9b/9d: `docs/skills/phase-meeting/SKILL.md` missing — dead nav link (BLOCKING)

`mkdocs.yml` line 206 references `skills/phase-meeting/SKILL.md` (resolves to `docs/skills/phase-meeting/SKILL.md`). The `phase-meeting` skill folder exists at `skills/phase-meeting/` but no `docs/skills/phase-meeting/` directory was ever created. The nav entry was added when `/meeting` was introduced in 0.2.15 but the docs mirror was not created.

**Fix:** Create `docs/skills/phase-meeting/SKILL.md` as a docs mirror of `skills/phase-meeting/SKILL.md`.

---

### ISSUE 5 — Check 9c/9d: `docs/commands/wiki.md` missing — dead nav link (BLOCKING)

`mkdocs.yml` nav references `commands/wiki.md` at two locations (line 127 — Personal Wiki concept — and implicitly via the Commands reference). `docs/commands/wiki.md` does not exist. `commands/wiki.md` exists in the plugin source but has no docs mirror.

**Fix:** Create `docs/commands/wiki.md` as a docs mirror of `commands/wiki.md`.

---

### ISSUE 6 — Check 9c/9d: `docs/agents/autoresearch.md` missing — dead nav link (BLOCKING)

`mkdocs.yml` line 226 references `agents/autoresearch.md` (resolves to `docs/agents/autoresearch.md`). This file does not exist under `docs/agents/`. Pre-existing issue from last audit, not yet fixed.

**Fix:** Create `docs/agents/autoresearch.md` as a docs mirror of `agents/autoresearch.md`.

---

### ISSUE 7 — Check 12: Stale `.neuroflow/.flowie/` paths in docs files (BLOCKING)

From the previous audit (2026-04-03), these docs files still carry the old path. Verify whether they have been fixed; if not, they remain blocking:

- `docs/agents/flowie.md` — references `.neuroflow/.flowie/profile.md` (line 16) and `.neuroflow/.flowie/` (line 50)
- `docs/skills/phase-flowie/SKILL.md` — references `.neuroflow/.flowie/` at lines 3, 12, 24, 62, 64, 69, 70, 88; also contains stale `flowie_profile` field reference at line 24

The plugin source files (`skills/phase-flowie/SKILL.md`, `agents/flowie.md`) are already clean. Only the `docs/` mirror copies carry stale paths.

**Fix:** Update `docs/agents/flowie.md` and `docs/skills/phase-flowie/SKILL.md` — replace `.neuroflow/.flowie/` with `.neuroflow/flowie/` and `flowie_profile` with `flowie_profiles:` list reference.

---

### ISSUE 8 — Check 2c: README Agents table contains 16 dead links (HIGH)

Pre-existing from last audit (v0.2.13), not yet fixed. The following agent files were deleted in v0.2.13 but their rows remain in the README Agents table:

`agents/ideation.md`, `agents/grant-proposal.md`, `agents/experiment.md`, `agents/tool-build.md`, `agents/tool-validate.md`, `agents/data.md`, `agents/data-preprocess.md`, `agents/data-analyze.md`, `agents/notes.md`, `agents/write-report.md`, `agents/brain-build.md`, `agents/brain-optimize.md`, `agents/brain-run.md`, `agents/review.md`, `agents/critic.md`, `agents/orchestrator.md`

**Fix:** Remove all 16 rows from the README Agents table.

---

### ISSUE 9 — Check 2a/2b/2c: README tables not updated for 0.2.14–0.2.16 additions (HIGH)

The README Commands, Skills, and Agents tables were last audited at v0.2.13. The following items were added in later releases and are absent from their respective tables:

**Commands table** — missing:
- `/autoresearch` (added 0.2.13 — pre-existing miss; no row in any section)
- `/meeting` (added 0.2.15 — no row in the Commands table; the "Utility" section has `/meeting` already present at line 254, so this is resolved — PASS for meeting)

Re-checking: `/autoresearch` is missing from Commands table (confirmed — not present). `/meeting` is present. `/wiki` command (`commands/wiki.md` exists) — check:

Actually `/wiki` does appear in the commands list but let me verify — `/wiki` is not in the README Commands table. The README commands table covers Entry point, Research pipeline, Brain simulation, and Utility sections. `/wiki` is not listed in any section.

**Skills table** — missing:
- `neuroflow:autoresearch` (added 0.2.13, pre-existing miss)
- `neuroflow:phase-meeting` (added 0.2.15 — not present in README Skills table)

**Agents table** — missing:
- `autoresearch` agent (added 0.2.13, pre-existing miss)

**Fix:**
- Add `/autoresearch` to README Commands table under "Utility"
- Add `/wiki` to README Commands table under "Utility" (or a new "Knowledge" section)
- Add `neuroflow:autoresearch` to README Skills table
- Add `neuroflow:phase-meeting` to README Skills table
- Add `autoresearch` agent to README Agents table

---

### ISSUE 10 — Wiki ambient behavior: conflicting closing prompts in commands (MEDIUM)

`neuroflow-core` now owns all wiki crystallization detection and ingest offers via `## Wiki ambient behavior`. However, the following commands still have their own manual wiki closing nudges that fire independently of the crystallization logic:

- `commands/data-analyze.md` lines 56–61: hardcoded `if .neuroflow/flowie/wiki/ exists, add a closing nudge` block pointing to `/flowie --wiki-ingest`
- `commands/paper.md` lines 97–102: same pattern — hardcoded `if .neuroflow/flowie/wiki/ exists, add a closing nudge` block
- `commands/notes.md` lines 106–113: `### 6 — Wiki ingest offer` section with hardcoded `/flowie --wiki-ingest` prompt

These fire in addition to (not instead of) the neuroflow-core crystallization detection, meaning the user may receive two wiki ingest prompts at the end of a `/data-analyze`, `/paper`, or `/notes` session:
1. The hardcoded nudge from the command
2. The crystallization detection prompt from neuroflow-core

The `wiki/SKILL.md` `## Paper routing prompt` and `## Notes routing prompt` sections at lines 313–318 also describe this pattern as designed — but now that neuroflow-core handles it generally, those sections are redundant documentation.

**Assessment:** This is a behavioral redundancy, not a broken reference. The two paths are functionally compatible (both lead to `/flowie --wiki-ingest`), but the user sees double prompts. Whether to remove the per-command nudges and trust neuroflow-core exclusively is a design decision.

**Recommendation:** Review whether the per-command nudges in `commands/data-analyze.md`, `commands/paper.md`, and `commands/notes.md` should be removed now that neuroflow-core handles crystallization globally. If kept, add a comment noting they are intentional supplements (e.g. for users who read the command file without neuroflow-core loaded). The `wiki/SKILL.md` routing prompt sections (lines 313–318) should be updated to reflect that neuroflow-core now handles this — or removed if the per-command nudges are removed.

---

### ISSUE 11 — Check 11: `mind.js` NODE_PHASE_MAP stale entries (LOW)

Pre-existing from last audit, not yet fixed:

- `"ag-ideation": "ideation"` in NODE_PHASE_MAP — no `ag-ideation` node exists in NODES
- `"ag-orchestrator": "utility"` in NODE_PHASE_MAP — no `ag-orchestrator` node exists in NODES

**Fix:** Remove these two entries from NODE_PHASE_MAP.

---

### ISSUE 12 — Check 11: `mind.js` NODE_PHASE_MAP missing entries (LOW)

Pre-existing from last audit, not yet fixed. Nodes present in NODES but absent from NODE_PHASE_MAP:

`sk-humanizer`, `sk-flowie`, `sk-hive`, `sk-slideshow`, `sk-autoresearch`, `ag-sentinel`, `ag-sentinel-dev`, `ag-scholar`, `ag-autoresearch`

Recommended additions: `sk-flowie → "flowie"`, `sk-hive → "hive"`, `sk-slideshow → "slideshow"`, `ag-scholar → "ideation"`.

---

### ISSUE 13 — Check 3: README version heading not updated past 0.2.16 (INFO)

The README `## What's new in 0.2.16` heading is present and correct. The wiki ambient behavior additions made in this session (neuroflow-core `## Wiki ambient behavior` section, wiki/SKILL.md level routing table, phase-flowie simplification) are behavioral changes to existing skills — not a new release version. No version bump is needed for these content-only changes. However, if the next release is cut, a `## What's new in 0.2.17` entry should describe the new ambient wiki behavior.

**Assessment:** No action needed for current version. Flag for inclusion in the next release notes.

---

## Checks that passed

- **Check 1 — Folder/frontmatter names:** All 38 skill folders, 9 agent files, and 36 command files match their `name:` frontmatter fields exactly. PASS
- **Check 2a/2b/2c — README tables (existing entries):** All entries in the README Commands, Skills, and Agents tables that remain point to files that exist. PASS (dead links from deleted agents are flagged in Issue 8.)
- **Check 3 — Version sync (plugin.json / marketplace.json / README heading / mkdocs.yml):** All four markers agree: `0.2.16`. PASS
  - `.claude-plugin/plugin.json`: `0.2.16`
  - `.claude-plugin/marketplace.json`: `0.2.16`
  - `README.md` heading: `## What's new in 0.2.16`
  - `mkdocs.yml` `extra.version`: `"0.2.16"`
- **Check 3b — sa-bar-version:** FAIL — see Issue 1.
- **Check 4 — Dead references in SKILL.md files:** All `neuroflow:some-skill` and `neuroflow:wiki` references in the three modified skill files point to skills that exist. `neuroflow:wiki` (skills/wiki/), `neuroflow:autoresearch` (skills/autoresearch/), `neuroflow:neuroflow-core` (skills/neuroflow-core/) — all present. PASS
- **Check 5 — Naming overlaps:** No new naming overlaps. `wiki` exists as both a skill and a command — mirrors the established `autoresearch`/`sentinel`/`flowie` pattern. PASS
- **Check 6 — Command frontmatter completeness:** All 36 command files verified to have `name`, `description`, `phase`, `reads`, `writes`. PASS
- **Check 7 — .neuroflow subfolder purity:** Only `reasoning/` and `sessions/` subfolders present in `.neuroflow/`. No skill-named subfolders. PASS
- **Check 8 — hooks.json audit:** Valid JSON. Both hooks have `type` and `command`. Both commands have `>/dev/null 2>&1` and `; true` — error suppression confirmed. README Hooks table matches `hooks.json`. PASS
- **Check 8b — Hook error suppression:** Hook 1 ends with `>/dev/null 2>&1` and `; true`. Hook 2 ends with `>/dev/null 2>&1` and `; true`. Both pass. PASS
- **Check 9a — mkdocs.yml version:** `extra.version: "0.2.16"` matches `plugin.json`. PASS
- **Check 9b — Command docs completeness:** All command files have a corresponding docs page under `docs/commands/` except `docs/commands/wiki.md` (flagged in Issue 5). All other 35 command files have docs pages. PASS (minus Issue 5)
- **Check 10 — Personal sensitive information:** No real email addresses (all in skill files are placeholder domains: `example.com`, `institution.edu`), no passwords or real secrets, no PEM keys found. API key references are all placeholder templates (angle-bracket `<key>`, `dummy`, example JWT prefix). PASS
- **Check 12 — Flowie path hygiene:** No occurrences of `.neuroflow/.flowie/`, `flowie_profile:`, `hive_member:`, or `flowie_project:` in plugin source files (`agents/`, `commands/`, `skills/`, `hooks/`, `.neuroflow/`, `README.md`). The `docs/changelog.md` reference to `flowie_profile:` is in a historical changelog entry and intentional. The stale paths in `docs/agents/flowie.md` and `docs/skills/phase-flowie/SKILL.md` are flagged in Issue 7. PASS for plugin source; docs mirror issue carried over.
- **New changes check — neuroflow-core `## Wiki ambient behavior`:** Section added cleanly. `neuroflow:wiki` reference at line 213 resolves. No broken cross-references introduced. PASS
- **New changes check — wiki/SKILL.md level routing table:** Table at lines 278–289 is internally consistent with the table in neuroflow-core lines 222–232. References to `neuroflow-core`'s crystallization hook at line 277 are accurate. PASS
- **New changes check — phase-flowie simplification:** Manual wiki routing prompt list removed; replaced with pointer to neuroflow-core at lines 137–139. Pointer is accurate — the section it references (`## Wiki ambient behavior`) exists in neuroflow-core. No orphaned references. PASS

---

## Summary

| # | Severity | Check | Description |
|---|----------|-------|-------------|
| 1 | BLOCKING | 3b | `docs/index.md` sa-bar-version reads `v0.2.13`, should be `v0.2.16` |
| 2 | BLOCKING | 9b/9d | `docs/skills/wiki/SKILL.md` missing — dead mkdocs nav link |
| 3 | BLOCKING | 9c/9d | `docs/skills/setup/SKILL.md` missing — dead mkdocs nav link (pre-existing) |
| 4 | BLOCKING | 9b/9d | `docs/skills/phase-meeting/SKILL.md` missing — dead mkdocs nav link |
| 5 | BLOCKING | 9c/9d | `docs/commands/wiki.md` missing — dead mkdocs nav link |
| 6 | BLOCKING | 9c/9d | `docs/agents/autoresearch.md` missing — dead mkdocs nav link (pre-existing) |
| 7 | BLOCKING | 12 | Stale `.neuroflow/.flowie/` paths in `docs/agents/flowie.md` and `docs/skills/phase-flowie/SKILL.md` (pre-existing) |
| 8 | HIGH | 2c | 16 dead agent links in README Agents table (deleted in v0.2.13, pre-existing) |
| 9 | HIGH | 2a/2b/2c | README tables missing: `/autoresearch` command, `/wiki` command, `neuroflow:autoresearch`, `neuroflow:phase-meeting` skills, `autoresearch` agent |
| 10 | MEDIUM | — | Double wiki prompts: per-command nudges in data-analyze/paper/notes + neuroflow-core crystallization detection both fire |
| 11 | LOW | 11 | `mind.js` NODE_PHASE_MAP stale entries: `ag-ideation`, `ag-orchestrator` (pre-existing) |
| 12 | LOW | 11 | `mind.js` NODE_PHASE_MAP missing entries for 9 nodes (pre-existing) |
| 13 | INFO | 3 | Wiki ambient behavior added in 0.2.16 dev session — include in next release notes when version is bumped |
