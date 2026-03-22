Last run: 2026-03-22

## All clear

All checks passed. No issues found.

---

## Checks with no issues

- **Check 1 — Folder name vs frontmatter name:** All 35 skill folders, 24 agent files, and 33 command files match their `name:` frontmatter fields exactly.
- **Check 2 — README tables:** Every command file has a row in the README Commands table; every skill folder has a row in the README Skills table (including `humanizer`); every agent file has a row in the README Agents table. All links in the three tables point to files that exist. The `neuroflow-developer` agent is correctly linked to `.github/agents/neuroflow-developer.md`, which exists.
- **Check 3 — Version sync (plugin.json / README / mkdocs.yml / marketplace.json):** `plugin.json` version is `0.2.7`. README heading is `## What's new in 0.2.7`. `mkdocs.yml` `extra.version` is `0.2.7`. `marketplace.json` version is `0.2.7`. All four agree.
- **Check 3b — Self-assessment bar sync:** `docs/index.md` line 9 contains `<span class="sa-bar-version">v0.2.7</span>`. Matches `plugin.json` version. No issue.
- **Check 4 — Dead references inside SKILL.md files:** The refs `neuroflow:my-command`, `neuroflow:my-skill`, and `neuroflow:skill-name` in `skills/neuroflow-develop/SKILL.md` are intentional developer-guide placeholders (lines 83, 104, 190). The ref `/neuroflow:` in `skills/neuroflow-core/SKILL.md` is a formatting element, not a broken command link. No genuine dead references found.
- **Check 5 — Naming overlaps:** No skill folder name and command filename are identical. Agent-command name matches (e.g. `ideation`, `experiment`) are intentional architectural pairs, not naming confusion.
- **Check 6 — Command frontmatter completeness:** All 33 command files contain all five required fields: `name`, `description`, `phase`, `reads`, `writes`.
- **Check 7 — .neuroflow subfolder purity:** Only `reasoning/` subfolder present inside `.neuroflow/`. No skill-named subfolders.
- **Check 8 — hooks.json:** Valid JSON. Both hook entries have a `matcher` and at least one `hooks` item with `type` and `command`. Hook 1 (ruff formatter, `Edit|Write`) has `2>/dev/null` and `; true`. Hook 2 (session logger, `Write|Edit|Bash`) has `; true`. Both pass error suppression check. README Hooks table documents both hooks and matches `hooks.json` exactly.
- **Check 9a — mkdocs.yml version sync:** `extra.version: "0.2.7"` matches `plugin.json` version `0.2.7`.
- **Check 9b — Command docs completeness:** All 33 command files have a `docs/commands/<name>.md` page and appear in the `mkdocs.yml` nav.
- **Check 9c — Skill docs completeness:** All 35 skill folders appear in `mkdocs.yml` nav and have a `docs/skills/<name>/SKILL.md`. `humanizer` added: `docs/skills/humanizer/SKILL.md` created and `mkdocs.yml` nav updated (Expert section).
- **Check 9d — No dead nav links:** All paths listed in `mkdocs.yml` nav resolve to existing files under `docs/`.
- **Check 10 — Personal sensitive information:** Email addresses in `skills/phase-poster/SKILL.md` and `docs/skills/phase-poster/SKILL.md` are LaTeX template placeholders (`email@institution.edu`, `corresponding.author@institution.edu`, `email@inst.edu`) — clearly synthetic, used inside LaTeX poster templates. The `sentinel-dev[bot]@users.noreply.github.com` address in `scripts/automation/sentinel_check.py` is a GitHub Actions bot address, not a personal email. All `GITHUB_TOKEN` and `MIRO_ACCESS_TOKEN` usages in scripts are read from environment variables via `os.environ.get()` — no hardcoded secrets. Author name (`Stanislav Jiricek`) in `plugin.json` and `marketplace.json` is intentional public attribution. No passwords, private keys, or hardcoded secrets found.
