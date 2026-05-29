Last run: 2026-05-29

## Issues found

---

### ISSUE 1 — Check 9d: `docs/skills/bids/SKILL.md` missing — dead nav link (BLOCKING)

`mkdocs.yml` line 176 contains:
```yaml
- "bids": skills/bids/SKILL.md
```
This resolves to `docs/skills/bids/SKILL.md`, which does not exist. The `bids` skill has a source file at `skills/bids/SKILL.md` but no docs mirror has been created at `docs/skills/bids/SKILL.md`. Every other skill has a mirror under `docs/skills/<name>/SKILL.md` — `bids` is the only one missing.

**Fix:** Create `docs/skills/bids/` and copy (or symlink) `skills/bids/SKILL.md` there. Also check whether the reference sub-files (`references/structure.md`, `references/metadata.md`, `references/tools.md`, `references/examples.md`) need mirrors as well.

---

### ISSUE 2 — Check 3b: `docs/index.md` sa-bar-version shows `v0.2.17`, plugin is `0.2.19` (BLOCKING)

`docs/index.md` line 9:
```html
<span class="sa-bar-version">v0.2.17</span>
```
`plugin.json` version: `0.2.19`

The self-assessment bar was not updated during the v0.2.18 or v0.2.19 releases. This check exists precisely because this element is most commonly missed during manual releases.

**Fix:** Update `docs/index.md` line 9 to `v0.2.19`.

---

### ISSUE 3 — Check 2 (dead README link): `skills/setup/scripts/proxy.mjs` wrong path (LOW)

README line 63 (What's new 0.2.10) links to `skills/setup/scripts/proxy.mjs`. The actual file is at `skills/setup/scripts/einfra/proxy.mjs`. The link is dead. This is in a historical changelog section, not the nav table.

**Fix:** Update README line 63 to `skills/setup/scripts/einfra/proxy.mjs`. Low priority.

---

### ISSUE 4 — Check 2: README What's new sections contain dead agent links (INFO)

The README Agents **table** (lines 329–338) is clean — all 10 entries point to files that exist. However, historical `## What's new` changelog sections contain links to agent files deleted in v0.2.13:

- Line 161 (What's new 0.1.5): `agents/ideation.md`, `agents/grant-proposal.md`, `agents/experiment.md`, `agents/tool-build.md`, `agents/tool-validate.md`, `agents/data.md`, `agents/data-preprocess.md`, `agents/data-analyze.md`, `agents/notes.md`, `agents/write-report.md`, `agents/brain-build.md`, `agents/brain-optimize.md`, `agents/brain-run.md`
- Line 103 (What's new 0.2.3): `agents/review.md`
- Line 123 (What's new 0.1.9): `agents/orchestrator.md`, `agents/critic.md`

These are historical changelog links — not load-bearing navigation. If link-checker CI is ever added these will fail.

**Assessment:** Low priority. Consider converting historical dead agent links to plain text (not hyperlinked).

---

### ISSUE 5 — Check 5: Naming overlaps (INFO)

Three skill/command name pairs share identical names: `autoresearch`, `setup`, `wiki`. This mirrors the established `sentinel`/`flowie` pattern (also overlaps). No functional breakage — skill names are namespaced as `neuroflow:<name>` and command names as `/neuroflow:<name>`. Document as intentional.

---

### ISSUE 6 — Check 4: Template placeholder strings match broken-ref pattern (INFO)

The following references in SKILL.md files pattern-match as broken skill/command references but are template or placeholder text, not real references:

- `skills/autoresearch/SKILL.md` — `neuroflow:phase-` (partial, doc prose)
- `skills/neuroflow-develop/SKILL.md` — `neuroflow:my-skill`, `neuroflow:my-command`, `neuroflow:skill-name` (template examples)
- `skills/worker-critic/SKILL.md` — `neuroflow:phase-` (partial, doc prose)

No fix needed.

---

### ISSUE 7 — Check 10: Emails in `skills/bids/SKILL.md` and `references/examples.md` (needs human review)

Two files contain `jane@lab.edu` inside a `dataset_description.json` example block:

- `skills/bids/SKILL.md` line 103: `j***@lab.edu` (inside JSON example: `"email": "jane@lab.edu"`)
- `skills/bids/references/examples.md` line 58: `j***@lab.edu` (same JSON example block)

The `lab.edu` domain is not in the skip-list (`example.com`, `example.org`, `test.com`, `domain.com`, `localhost`), so it is flagged. The value `"jane@lab.edu"` is a clearly synthetic placeholder name — "Jane Doe" is a standard placeholder. No real person is at risk, but the domain `lab.edu` is not formally synthetic.

**Assessment:** Likely false positive. If preferred, replace `jane@lab.edu` with `jane@example.com` to match the skip-list and prevent future flags.

---

### ISSUE 8 — Check 10: Emails in `skills/phase-poster/SKILL.md` (needs human review)

Four lines contain email-shaped strings inside LaTeX poster template blocks:

- Line 153: `c***@i***.edu` (inside `\textbf{Contact:} \texttt{corresponding.author@institution.edu}`)
- Line 232: `e***@i***.edu` (inside `\small \textbf{Contact:} \texttt{email@institution.edu}`)
- Line 292: `e***@i***.edu` (inside `\small \textbf{Contact:} \texttt{email@inst.edu}`)
- Line 410: `e***@i***.edu` (inside `\texttt{email@institution.edu}`)

All four use generic `institution.edu`/`inst.edu` domains — clearly template placeholders. The domains are not in the skip-list.

**Assessment:** False positive. No action required.

---

## Checks that passed

- **Check 1 — Folder/frontmatter names:** All 40 skill folders match `name:` in SKILL.md. All 9 agent files match `name:`. All 36 command files match `name:`. PASS

- **Check 2 — README tables (tables only):**
  - All 36 commands in `commands/` have a row in the Commands table. PASS
  - All 40 skills in `skills/` have a row in the Skills table (including `neuroflow:bids` — confirmed present). PASS
  - All 9 agents in `agents/` have a row in the Agents table. The `neuroflow-developer` entry links to `.github/agents/neuroflow-developer.md` — file confirmed present. PASS
  - No dead links in the active table rows. PASS

- **Check 3 — Version sync:**
  - `plugin.json`: `0.2.19`
  - `marketplace.json`: `0.2.19`
  - `README.md` heading: `## What's new in 0.2.19`
  - `mkdocs.yml` `extra.version`: `"0.2.19"`
  All four agree. PASS. (sa-bar-version in `docs/index.md` is out of sync — flagged as Issue 2.)

- **Check 4 — Dead references in SKILL.md files:**
  - `neuroflow:bids` reference in `phase-data`, `phase-data-preprocess`, `phase-data-analyze` — `skills/bids/` folder exists, SKILL.md present. PASS
  - All other `neuroflow:skill-name` and `/neuroflow:command-name` references resolve. PASS
  - Template placeholder strings flagged as Issue 6 (false positives).

- **Check 6 — Command frontmatter completeness:** All 36 command files have `name`, `description`, `phase`, `reads`, `writes`. PASS

- **Check 7 — .neuroflow subfolder purity:** `.neuroflow/` contains `reasoning/` (permitted) and `sessions/` (standard project memory subfolder). No skill-named subfolders present. PASS

- **Check 8 — hooks.json audit:** Valid JSON. Both PostToolUse hooks have `matcher`, `type`, and `command`. README Hooks section documents both hooks (ruff formatter, flowie git-sync) — matches `hooks.json` entries exactly. PASS

- **Check 8b — Hook error suppression:** Both hooks end with `; true`. Ruff hook also uses `>/dev/null`. Flowie hook uses `>/dev/null 2>&1`. Both pass.

- **Check 9a — mkdocs.yml version:** `extra.version: "0.2.19"` matches `plugin.json`. PASS

- **Check 9b — Command docs completeness:** All 36 command files have a corresponding `docs/commands/<name>.md` page. `docs/commands/wiki.md` exists. PASS. (The wiki command is now in the mkdocs nav — Issue 1 from the v0.2.17 run is resolved.)

- **Check 9c — Skill docs completeness:** All skills (except `bids` — Issue 1) have `docs/skills/<name>/SKILL.md` mirrored and in the mkdocs.yml nav. PASS for all except `bids`.

- **Check 9d — No dead nav links:** One dead nav link found — `skills/bids/SKILL.md` in mkdocs.yml maps to `docs/skills/bids/SKILL.md` which does not exist. All other nav paths exist. Flagged as Issue 1.

- **Check 10 — Personal sensitive information:** No real personal email addresses found. No passwords, API keys with real values, or PEM private keys found. `GITHUB_TOKEN`, `MIRO_ACCESS_TOKEN`, etc. are all referenced via environment variable expansion (`${{ secrets.GITHUB_TOKEN }}`, `"eyJ..."` placeholder, `<your-api-key>`) — no live credentials. `Stanislav Jiricek` appears in `plugin.json`, `marketplace.json`, and `README.md` as the author credit — appropriate and expected context. PASS (with human review notes on Issues 7 and 8.)

- **Check 11 — mind.js sync:** The mind.js uses a concept-cluster map (not a per-entity map). The new `sk-bids` node (`id: "sk-bids"`, `label: "BIDS skill"`, `category: "pipeline"`) was added and is linked to `c-data` — correctly placed in the pipeline cluster. PASS

- **Check 12 — Flowie/hive path hygiene:**
  - No `.neuroflow/.flowie/` (old dot-prefixed path) found in plugin source files. PASS
  - `.neuroflow/flowie/` occurrences: present in `docs/changelog.md` (historical — exempt) and in `agents/sentinel-dev.md`/`agents/sentinel.md` (sentinel-context — exempt). All other occurrences use the correct `~/.neuroflow/flowie/` global path. PASS
  - `.neuroflow/hive/` occurrences: `docs/changelog.md` (historical — exempt) and `agents/sentinel.md` line 167 (migration guidance prose — exempt). PASS
  - `flowie_project:` occurrences: `commands/flowie.md` line 593 (backward-compatibility migration logic — not stale usage), `README.md` and `docs/changelog.md` (documentation of migration guard — historical). PASS
  - `hive_member:` occurrences: `agents/sentinel.md` and `agents/sentinel-dev.md` (definition of the check itself), `docs/changelog.md` and `README.md` (historical migration record). No operational stale usage found. PASS
  - `flowie_profile:` occurrences: `docs/changelog.md` (historical entry for v0.2.14 rename). PASS

---

## BIDS integration status (v0.2.19 — special focus)

- `skills/bids/SKILL.md` — present, `name: bids` matches folder. PASS
- `skills/bids/references/` — all four reference files present (`structure.md`, `metadata.md`, `tools.md`, `examples.md`). PASS
- `phase-data/SKILL.md` — `neuroflow:bids` listed in Relevant skills. PASS
- `phase-data-preprocess/SKILL.md` — `neuroflow:bids` listed in Relevant skills. PASS
- `phase-data-analyze/SKILL.md` — `neuroflow:bids` listed in Relevant skills. PASS
- `mind.js` `sk-bids` node — present, linked to `c-data`. PASS
- README Skills table row for `neuroflow:bids` — present. PASS
- mkdocs.yml nav entry `skills/bids/SKILL.md` — present. PASS
- `docs/skills/bids/SKILL.md` mirror — MISSING (Issue 1).

---

## Summary

| # | Severity | Check | Description |
|---|----------|-------|-------------|
| 1 | BLOCKING | 9d | `docs/skills/bids/SKILL.md` does not exist — mkdocs nav link is dead, bids skill unreachable from docs site |
| 2 | BLOCKING | 3b | `docs/index.md` sa-bar-version reads `v0.2.17`, plugin is `0.2.19` — two releases behind |
| 3 | LOW | 2 | `skills/setup/scripts/proxy.mjs` dead link in README What's new 0.2.10 (correct path: `scripts/einfra/proxy.mjs`) |
| 4 | INFO | 2 | 16+ dead agent links in README What's new historical sections (not table rows) |
| 5 | INFO | 5 | `autoresearch`, `setup`, `wiki` are both skill and command names — intentional overlap |
| 6 | INFO | 4 | Template/placeholder text in neuroflow-develop, autoresearch, worker-critic skills matches broken-ref pattern — false positives |
| 7 | INFO | 10 | `jane@lab.edu` in `skills/bids/SKILL.md` and `references/examples.md` — synthetic placeholder, needs human confirmation |
| 8 | INFO | 10 | Emails in `skills/phase-poster/SKILL.md` are LaTeX template placeholders — needs human confirmation |
