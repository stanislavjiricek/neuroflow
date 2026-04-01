Last run: 2026-05-27

## Issues found

---

### 🔴 ISSUE 1 — Check 3b: Self-assessment bar version not updated (BLOCKING)

`docs/index.md` contains `<span class="sa-bar-version">v0.2.8</span>` but `plugin.json` version is `0.2.10`.
The sa-bar-version was NOT updated during the 0.2.10 bump. All other version markers are consistent:
- `plugin.json`: `0.2.10` ✅
- `README.md`: `## What's new in 0.2.10` ✅
- `mkdocs.yml` `extra.version`: `"0.2.10"` ✅
- `docs/index.md` `sa-bar-version`: **`v0.2.8`** ❌

**Fix:** Update `docs/index.md` — change `<span class="sa-bar-version">v0.2.8</span>` → `<span class="sa-bar-version">v0.2.10</span>`.

---

### 🔴 ISSUE 2 — Check 9d: Dead nav link — `docs/skills/setup/SKILL.md` missing (BLOCKING)

`mkdocs.yml` nav references `skills/setup/SKILL.md` (resolves to `docs/skills/setup/SKILL.md`) but this file does not exist.
The `docs/skills/setup/` directory was never created for the new `setup` skill.

All other skills have their `docs/skills/<name>/SKILL.md` copy under `docs/`. Only `setup` is absent.
`skills/setup/SKILL.md` (the source) exists in the repo root ✅ — the docs copy is missing.

**Fix:** Create `docs/skills/setup/SKILL.md` (copy or symlink from `skills/setup/SKILL.md`), matching the pattern used for all other skills.

---

### 🟡 ISSUE 3 — Check 8: hooks.json vs README Hooks table mismatch

The README `## Hooks` section documents these two hooks:
1. **ruff formatter** — `PostToolUse` Edit/Write — auto-formats `.py` files ✅ (exists in hooks.json)
2. **session logger** — `PostToolUse` Write/Edit/Bash — appends to `.neuroflow/sessions/` ❌ **does NOT exist in hooks.json**

`hooks.json` has these two hooks (both on `Edit|Write`):
1. **ruff format** — `ruff format "$f" >/dev/null 2>&1; true` ✅ (documented in README)
2. **flowie git-sync** — auto-commits and pushes `.neuroflow/flowie/` on file writes ❌ **NOT documented in README**

The README still references the old "session logger" hook (removed in an earlier session). The new flowie git-sync hook added this session is absent from the README.

**Fix:** Update README `## Hooks` table — remove the "session logger" row, add a row for the flowie git-sync hook.

---

### 🟡 ISSUE 4 — Check 9c: `flowie` agent docs page not in mkdocs.yml nav

`docs/agents/flowie.md` exists but is NOT listed in the `mkdocs.yml` Agents nav section.
The nav currently lists only `critic`, `orchestrator`, and `poster-critic` under Agents.

Note: most agent doc pages also lack nav entries (existing design — 21 of 24 are unlisted). This is an established pattern. However, since `flowie` was just added in this session and `docs/agents/flowie.md` was explicitly created, it should be evaluated whether it belongs in the nav alongside critic/orchestrator/poster-critic.

**Fix (optional):** Add `"flowie": agents/flowie.md` to the Agents nav in `mkdocs.yml`, or acknowledge the existing pattern and leave it unlisted.

---

### 🔴 ISSUE 5 — Check 12: Stale `.neuroflow/.flowie/` paths in docs/ copies (BLOCKING)

The actual source files are clean:
- `skills/phase-flowie/SKILL.md` — no stale paths ✅
- `agents/flowie.md` — no stale paths ✅

But the docs/ mirror copies are **out of date**:

**`docs/agents/flowie.md`:**
- Line 16: uses `.neuroflow/.flowie/profile.md` (old path — should be `.neuroflow/flowie/profile.md`)
- Line 50: uses `.neuroflow/.flowie/` (old path — should be `.neuroflow/flowie/`)

**`docs/skills/phase-flowie/SKILL.md`:**
- Lines 3, 12, 62, 64, 69, 70, 88: `.neuroflow/.flowie/` → should be `.neuroflow/flowie/`
- Line 24: `flowie_profile` → should be `flowie_project:`

These docs copies appear to be the pre-migration version. The source files were updated but the docs/ copies were not.

**Fix:** Sync `docs/agents/flowie.md` and `docs/skills/phase-flowie/SKILL.md` from their source counterparts, or apply targeted find-replace:
- `.neuroflow/.flowie/` → `.neuroflow/flowie/`
- `flowie_profile` → `flowie_project:` (line 24 of docs/skills/phase-flowie/SKILL.md)

---

### 🔵 ISSUE 6 — Check 5: Naming overlap — `setup` is both a skill and a command (NOTE)

`skills/setup/` and `commands/setup.md` share the identical bare name `setup`.
Unlike all other phase skills which use the `phase-X` naming convention (e.g. `phase-ideation` vs `ideation`), the new `setup` skill uses the same name as its command with no prefix.

This is the only exact naming overlap in the entire plugin. It is very likely intentional (the skill backs the command directly), but deviates from the established `phase-X` prefix convention for phase-paired skills.

**No immediate fix required.** Flagged for awareness. If a naming convention policy update is desired, options are: rename skill to `phase-setup` or document the pattern as an explicit exception.

---

### 🔵 ISSUE 7 — Check 4: Placeholder refs in neuroflow-develop/SKILL.md (NOTE — false positives)

`skills/neuroflow-develop/SKILL.md` lines 83, 104, and 191 contain `neuroflow:my-skill`, `neuroflow:my-command`, and `neuroflow:skill-name`. These are **intentional developer-guide template examples** showing the invocation syntax, not real skill/command references. No fix required.

All other flagged "broken skill refs" (e.g. `neuroflow:brain-build` in `phase-brain-build/SKILL.md`) are false positives — the regex matched `neuroflow:brain-build` *within* the slash command string `/neuroflow:brain-build`, which is a valid command invocation. No broken references found.

---

### 🔵 ISSUE 8 — Check 10: Email-like strings in phase-poster SKILL.md (needs human review)

`skills/phase-poster/SKILL.md` and its docs copy `docs/skills/phase-poster/SKILL.md` contain the following at these lines:
- Line 153: `c***@institution.edu`
- Line 232: `e***@institution.edu`
- Line 292: `e***@inst.edu`
- Line 410: `e***@institution.edu`

These appear to be **LaTeX poster template examples** (placeholder author email fields inside `\author{}` blocks). The domain `institution.edu` is synthetic. These are very likely intentional — but `institution.edu` and `inst.edu` are not in the skip-list of synthetic domains.

**[needs human review]** — Confirm these are LaTeX template examples with no real personal data, then optionally add `institution.edu` and `inst.edu` to the sensitive-scan skip list.

---

## Checks that passed

- **Check 1 — Folder/frontmatter names:** All 36 skill folders, 24 agent files, and 33 command files match their `name:` frontmatter fields exactly. ✅
- **Check 2 — README tables:** All command, skill, and agent files have rows in their respective README tables. All table links resolve to existing files. New `setup` command ✅, `setup` skill ✅, `flowie` agent ✅ all have rows. `neuroflow-developer` correctly points to `.github/agents/neuroflow-developer.md`. ✅
- **Check 3 — Version sync (partial):** `plugin.json`, `README.md`, and `mkdocs.yml` all agree on `0.2.10`. ✅ (sa-bar-version fails — see Issue 1.)
- **Check 6 — Command frontmatter completeness:** All 33 command files have all five required fields (`name`, `description`, `phase`, `reads`, `writes`). ✅
- **Check 7 — .neuroflow subfolder purity:** `.neuroflow/` contains only `reasoning/` as a subfolder. No skill-named subfolders. ✅
- **Check 8 (partial) — hooks.json structure:** Valid JSON. Both hooks have `matcher` and `hooks` items with `type` and `command`. Error suppression present in both (hook 1: `>/dev/null 2>&1` + `; true`; hook 2: `>/dev/null 2>&1` + `; true`). ✅ (README documentation mismatch — see Issue 3.)
- **Check 9a — mkdocs.yml version:** `extra.version: "0.2.10"` matches `plugin.json`. ✅
- **Check 9b — Command docs completeness:** All 33 command files have `docs/commands/<name>.md` and all appear in `mkdocs.yml` nav. `setup` command: `docs/commands/setup.md` exists ✅ and `"⚙️ setup": commands/setup.md` is in nav ✅.
- **Check 9c — Skill docs completeness (partial):** All 36 skill folders appear in `mkdocs.yml` nav. `setup` skill is in nav. ✅ (docs file missing — see Issue 2.)
- **Check 11 — mind.js sync:** All three new items are present in `docs/javascripts/mind.js`. `setup` skill: `{ id: "sk-setup", label: "setup", type: "skill", ... }` ✅. `setup` command: `{ id: "cmd-setup", label: "/setup", type: "command", ... }` ✅. `flowie` agent: `{ id: "ag-flowie", label: "flowie", type: "agent", ... }` ✅.
- **Check 12 (source files) — Flowie path hygiene:** Source files `skills/phase-flowie/SKILL.md` and `agents/flowie.md` contain no stale `.neuroflow/.flowie/` paths. ✅ (docs/ copies are stale — see Issue 5.)

---

## Summary

| # | Severity | Check | Status |
|---|----------|-------|--------|
| 1 | 🔴 BLOCKING | sa-bar-version stuck at v0.2.8 | fix: update `docs/index.md` |
| 2 | 🔴 BLOCKING | `docs/skills/setup/SKILL.md` missing | fix: create the file |
| 3 | 🟡 MEDIUM | hooks README vs hooks.json mismatch | fix: update README Hooks table |
| 4 | 🟡 MEDIUM | `flowie` agent not in mkdocs.yml nav | optional: add to Agents nav |
| 5 | 🔴 BLOCKING | docs/ flowie copies have stale paths | fix: sync from source files |
| 6 | 🔵 NOTE | `setup` naming overlap (skill + command) | no action required |
| 7 | 🔵 NOTE | neuroflow-develop placeholder refs | no action required |
| 8 | 🔵 NOTE | poster SKILL.md email-like strings | human review |
