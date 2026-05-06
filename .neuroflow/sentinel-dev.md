Last run: 2026-05-06

## Issues found

---

### ISSUE 1 — Check 9b/9d: `docs/commands/wiki.md` exists but is not in mkdocs.yml nav (BLOCKING)

`docs/commands/wiki.md` was created (committed as a chore after v0.2.17) and the file exists on disk. However, `mkdocs.yml` has no nav entry for `commands/wiki.md`. Users cannot reach the `/wiki` docs page via the nav tree. The `skills/wiki/SKILL.md` nav entries (lines 127 and 208 in mkdocs.yml) point to the skill doc, not the command doc — these are separate pages.

**Fix:** Add a nav entry for `commands/wiki.md` under the Utilities section of the Concepts > Research Pipeline nav, alongside `/search`, `/sentinel`, etc. Suggested placement — after `/search`:

```yaml
- "📖 Wiki": commands/wiki.md
```

Also add to the Reference > Commands section (`commands/index.md` page or inline nav).

---

### ISSUE 2 — Check 2: README Agents table contains dead links in What's new sections (INFO)

The README Agents **table** (lines 316–332) is clean — all 10 entries point to files that exist. However, the historical `## What's new` changelog sections in the README contain links to agent files that were deleted in v0.2.13:

- Line 155: `agents/ideation.md`, `agents/grant-proposal.md`, `agents/experiment.md`, `agents/tool-build.md`, `agents/tool-validate.md`, `agents/data.md`, `agents/data-preprocess.md`, `agents/data-analyze.md`, `agents/notes.md`, `agents/write-report.md`, `agents/brain-build.md`, `agents/brain-optimize.md`, `agents/brain-run.md` (What's new 0.1.5)
- Line 97: `agents/review.md` (What's new 0.2.3)
- Line 117: `agents/orchestrator.md`, `agents/critic.md` (What's new 0.1.9)

These are historical changelog links, not table entries. Broken links in changelog prose are acceptable as they are historical record, but noted here for completeness.

**Assessment:** Low priority. If markdown link-checking CI is ever added, these will cause failures. Consider converting historical agent links in What's new sections to plain text (not hyperlinked) or adding a note that these agents were removed.

---

### ISSUE 3 — Check 2 (dead README link): `skills/setup/scripts/proxy.mjs` wrong path (LOW)

Line 63 of README (What's new 0.2.10) links to `skills/setup/scripts/proxy.mjs`. The actual file is at `skills/setup/scripts/einfra/proxy.mjs` (one subdirectory deeper). The link is dead. This is in a historical changelog section, not a nav table.

**Fix:** Update line 63 to `skills/setup/scripts/einfra/proxy.mjs`.

---

### ISSUE 4 — Check 5: Naming overlaps (INFO)

Three skill/command name pairs share identical names: `autoresearch`, `setup`, `wiki`. This mirrors the established `sentinel`/`flowie` pattern (also overlaps). No functional breakage — skill names are namespaced `neuroflow:<name>` and command names are `/neuroflow:<name>` — but IDE tab-completion and search may surface both. Document as intentional.

---

### ISSUE 5 — Check 4: Placeholder/template text produces false "broken ref" matches (INFO)

The following references in SKILL.md files pattern-match as broken skill or command references but are template/placeholder text, not real references:

- `skills/autoresearch/SKILL.md:239` — `neuroflow:phase-` (partial, doc prose)
- `skills/neuroflow-develop/SKILL.md:83` — `neuroflow:my-skill` (template example)
- `skills/neuroflow-develop/SKILL.md:104` — `neuroflow:my-command` (template example)
- `skills/neuroflow-develop/SKILL.md:191` — `neuroflow:skill-name` (template example)
- `skills/worker-critic/SKILL.md:166` — `neuroflow:phase-` (partial, doc prose)

These are intentional placeholder strings in developer documentation. No fix needed.

---

### ISSUE 6 — Check 10: Emails in `phase-poster/SKILL.md` (needs human review)

Four lines in `skills/phase-poster/SKILL.md` contain email-shaped strings inside LaTeX poster templates. These appear to be placeholder addresses within LaTeX `\texttt{}` blocks, not real personal email addresses:

- Line 153: `c***@i***.edu` (inside `\textbf{Contact:} \texttt{corresponding.author@institution.edu}`)
- Line 232: `e***@i***.edu` (inside `\small \textbf{Contact:} \texttt{email@institution.edu}`)
- Line 292: `e***@i***.edu` (inside `\small \textbf{Contact:} \texttt{email@inst.edu}`)
- Line 410: `e***@i***.edu` (inside `\texttt{email@institution.edu}`)

All four use generic `institution.edu` or `inst.edu` domains — clearly template placeholders, not real addresses. The `institution.edu` domain is not in the skip-list (`example.com`, `example.org`, `test.com`, `domain.com`, `localhost`), hence the flag.

**Assessment:** False positive. The addresses are template placeholders embedded in LaTeX code blocks. No action needed, but the skip-domain list could be extended to include `institution.edu` and `inst.edu` if these patterns become common.

---

## Checks that passed

- **Check 1 — Folder/frontmatter names:** All 38 skill folders match `name:` in SKILL.md. All 9 agent files match `name:`. All 36 command files match `name:`. PASS

- **Check 2 — README tables (tables only):**
  - All commands in `commands/` have a row in the Commands table (including `/wiki` added in v0.2.17). PASS
  - All skills in `skills/` have a row in the Skills table. PASS
  - All agents in `agents/` have a row in the Agents table (all 10 current agents present). PASS
  - No dead links in the active table rows. PASS
  - Historical What's new sections contain dead links to deleted agents — flagged as Issue 2 (INFO level).

- **Check 3 — Version sync:** All four markers agree on `0.2.17`. PASS
  - `.claude-plugin/plugin.json`: `"0.2.17"`
  - `.claude-plugin/marketplace.json`: `"0.2.17"`
  - `README.md` heading: `## What's new in 0.2.17`
  - `mkdocs.yml` `extra.version`: `"0.2.17"`

- **Check 3b — sa-bar-version:** `docs/index.md` line 9 reads `v0.2.17` — matches plugin.json. PASS (was FAIL at v0.2.13 in previous run; fixed in v0.2.17.)

- **Check 4 — Dead references in SKILL.md files:** All real `neuroflow:skill-name` and `/neuroflow:command-name` references resolve. The false positives listed in Issue 5 are template placeholders. PASS

- **Check 5 — Naming overlaps:** `autoresearch`, `setup`, `wiki` each exist as both skill and command. All are intentional by the established pattern (`sentinel`, `flowie`). PASS

- **Check 6 — Command frontmatter completeness:** All 36 command files have `name`, `description`, `phase`, `reads`, `writes`. PASS

- **Check 7 — .neuroflow subfolder purity:** `.neuroflow/` contains only `reasoning/` and `sessions/` as subfolders. No skill-named subfolders. PASS

- **Check 8 — hooks.json audit:** Valid JSON. Both PostToolUse hooks have `matcher`, `type`, and `command`. README Hooks table documents both hooks (ruff formatter, flowie git-sync) — matches `hooks.json` entries. PASS

- **Check 8b — Hook error suppression:** Hook 1 (ruff formatter): ends with `>/dev/null 2>&1` and `; true`. Hook 2 (flowie git-sync): ends with `>/dev/null 2>&1` and `; true`. Both pass.

- **Check 8c — Flowie hook path post-v0.2.17:** The flowie git-sync hook pattern `*/.neuroflow/flowie/*` correctly matches the global path `~/.neuroflow/flowie/file` (expands to `/home/user/.neuroflow/flowie/file`, which matches `*/.neuroflow/flowie/*`). The `d` variable extraction `${f%%/.neuroflow/*}/.neuroflow/flowie` correctly resolves to `~/.neuroflow/flowie` for global paths. PASS

- **Check 9a — mkdocs.yml version:** `extra.version: "0.2.17"` matches `plugin.json`. PASS

- **Check 9b — Command docs completeness:** All 36 command files have a corresponding `docs/commands/<name>.md` page. `docs/commands/wiki.md` was created post-v0.2.17 and exists. PASS (nav gap flagged in Issue 1.)

- **Check 9c — Skill docs completeness:** All skills have a `docs/skills/<name>/SKILL.md` entry in mkdocs.yml nav. `skills/wiki/SKILL.md`, `skills/setup/SKILL.md`, and `skills/phase-meeting/SKILL.md` docs mirrors — all fixed in v0.2.17. PASS

- **Check 9d — No dead nav links:** All files referenced in mkdocs.yml nav exist on disk. Previously blocking issues (wiki, setup, phase-meeting docs mirrors; autoresearch agent docs) were all resolved in v0.2.17. PASS

- **Check 10 — Personal sensitive information:** No real email addresses found (only template placeholders in LaTeX poster templates — flagged as Issue 6 for human review). No passwords, secrets, or PEM keys found. No hardcoded personal names in non-example context. PASS (with human review note on Issue 6.)

- **Check 11 — mind.js sync:** The mind.js was redesigned from a per-entity node map to a concept-cluster map. It no longer uses `NODE_PHASE_MAP` (previously Issues 11/12 in the last run — both resolved). The concept map has nodes for all major categories. Individual per-skill/command/agent node coverage is not required by the current design. PASS

- **Check 12 — Flowie path hygiene:**
  - No `.neuroflow/.flowie/` (old dot-prefixed path) found in plugin source files. PASS
  - `docs/agents/flowie.md` and `docs/skills/phase-flowie/SKILL.md` previously had stale paths — both fixed in v0.2.17. PASS
  - `hooks/hooks.json`: the flowie hook still uses `.neuroflow/flowie/` in the path pattern — this is correct for matching the global `~/.neuroflow/flowie/` structure (see Check 8c). PASS
  - `agents/sentinel.md` line 171 references "legacy project-level `.neuroflow/hive/`" — this is migration guidance prose, not a stale usage. PASS
  - `commands/flowie.md` line 593 uses `flowie_project:` and `flowie_profile:` in an inline condition for backward-compatibility handling (replacing legacy fields). This is migration logic, not stale usage. PASS
  - `README.md` line 32 and `docs/changelog.md` reference `flowie_project:` and `hive_member:` in migration guard description — historical/documentation context. PASS
  - `docs/changelog.md` line 85: `flowie_profile:` in historical 0.2.14 changelog entry. Intentional historical record. PASS

- **v0.2.17 refactor — per-command wiki nudges removed:** `commands/data-analyze.md`, `commands/paper.md`, and `commands/notes.md` no longer contain hardcoded wiki ingest nudges (Issue 10 from previous run resolved). PASS

- **v0.2.17 refactor — global path adoption:** `skills/phase-flowie/SKILL.md` has 12 references to `~/.neuroflow/flowie/` (correct global path). `skills/phase-hive/SKILL.md` and `agents/flowie.md` use `~/.neuroflow/` paths throughout. PASS

---

## Notes

- **docs/commands/wiki.md chore commit:** `docs/commands/wiki.md` was committed after v0.2.17 was tagged, without a version bump. This is a chore-level doc addition and does not require a version bump by itself. However, the file is not yet in the mkdocs.yml nav (Issue 1), so it is currently unreachable from the docs site.
- **README historical dead links:** The README What's new sections are a changelog — broken links to deleted agents are historical record. They are not load-bearing navigation. They would fail link-checker CI if that were ever added.
- **proxy.mjs path:** `skills/setup/scripts/proxy.mjs` referenced in README What's new 0.2.10 but the actual file is at `skills/setup/scripts/einfra/proxy.mjs`. Low priority fix.

---

## Summary

| # | Severity | Check | Description |
|---|----------|-------|-------------|
| 1 | BLOCKING | 9b/9d | `docs/commands/wiki.md` exists but missing from mkdocs.yml nav — unreachable from docs site |
| 2 | INFO | 2 | 16+ dead agent links in README What's new historical sections (not table rows) |
| 3 | LOW | 2 | `skills/setup/scripts/proxy.mjs` dead link in README What's new 0.2.10 (correct path: `scripts/einfra/proxy.mjs`) |
| 4 | INFO | 5 | `autoresearch`, `setup`, `wiki` are both skill and command names — intentional, no fix needed |
| 5 | INFO | 4 | Template/placeholder text in neuroflow-develop and autoresearch skills matches broken-ref pattern — false positives |
| 6 | INFO | 10 | Emails in `phase-poster/SKILL.md` are LaTeX template placeholders — needs human confirmation, no action expected |
