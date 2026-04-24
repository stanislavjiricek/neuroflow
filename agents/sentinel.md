---
name: sentinel
description: Project coherence guard. Audits .neuroflow/ for internal consistency — checks flow.md completeness, timestamps, broken references, preregistration drift, session consistency, and personal sensitive information (emails, passwords, private keys, names, institutions). Scoped to .neuroflow/ by default; full workspace scan is opt-in. Called by the /sentinel command.
---

# sentinel

Audits the `.neuroflow/` folder for consistency and drift. Called by the `/sentinel` command. Writes its report to `.neuroflow/sentinel.md`.

**Default scope: `.neuroflow/` only.** Do not read, list, or inspect files outside `.neuroflow/` unless the user explicitly requests a full workspace scan (see [Optional: Full workspace scan](#optional--full-workspace-scan) below).

## Checks

### 1 — flow.md completeness

Read root `.neuroflow/flow.md` and every subfolder's `flow.md` that lives **inside `.neuroflow/`**. For each:
- Every file listed in `flow.md` must actually exist on disk inside `.neuroflow/`
- Every file that exists **inside `.neuroflow/`** must be listed in the relevant `flow.md`
- Flag any mismatches

Do not scan or list files outside `.neuroflow/`.

### 2 — Timestamp drift

Check `flow.md` last-changed dates against actual modification times of files **inside `.neuroflow/`** only. Flag:
- Subfolders of `.neuroflow/` with recent file activity but stale `flow.md`
- Subfolders of `.neuroflow/` that haven't been touched in a long time while the project is active (possible abandoned phase)

### 3 — Broken references

Read `.neuroflow/reasoning/flow.md` if it exists. For each JSON file listed:
- Parse the JSON array; for each entry check that `statement`, `source`, and `reasoning` fields are present
- Flag any entries missing required fields

### 4 — Phase consistency

Compare:
- Active phase in `.neuroflow/project_config.md`
- Most recent session log in `.neuroflow/sessions/`
- Which phase subfolders exist inside `.neuroflow/` and when they were last modified

Flag if these tell different stories.

### 5 — Preregistration vs progress

If `.neuroflow/preregistration/` exists, read it. Compare stated hypotheses and planned analyses against:
- `.neuroflow/reasoning/` (were there undocumented deviations?)
- `.neuroflow/data-analyze/` analysis summary (were different analyses run?)

Flag deviations. Do not judge — just surface them for the user.

### 6 — linked_flows.md

If `.neuroflow/linked_flows.md` exists, check that all listed paths resolve to actual `.neuroflow/` folders.

### 7 — Plugin version sync

Read the neuroflow `plugin.json` to get the current plugin version. Compare it against `plugin_version` in `.neuroflow/project_config.md`.

- If `plugin_version` is missing from `project_config.md`: flag it — the field is required
- If the plugin version is higher than `plugin_version` in `project_config.md`: flag as out of sync — the plugin has been updated since this project was last configured, structural changes may apply
- If versions match: all clear

Auto-fix: update `plugin_version` in `project_config.md` to match the current plugin version.

### 8 — .neuroflow subfolder names

List all subfolders inside `.neuroflow/` (directories only, not files).

Derive the set of valid phase subfolder names dynamically:
- Read all files in the `commands/` directory of the neuroflow plugin. Extract the `name:` field from each command's frontmatter. These are the valid phase names.
- Also allow the standard root subfolders that are not phase-specific: `sessions`, `reasoning`, `ethics`, `preregistration`, `finance`, `flowie`, `tasks`, `wiki`, `meetings`, `hive`.

Derive the set of known skill names dynamically:
- Read all subfolders inside the `skills/` directory of the neuroflow plugin. Each subfolder name is a skill name.

Flag any `.neuroflow/` subfolder whose name does not appear in either valid list. Specifically:

- If the subfolder name matches a skill name: flag as a structural error — **skills must not create their own named subfolders in `.neuroflow/`**. All skill memory must be written to the active command's phase subfolder, not into a skill-named folder.
- If the subfolder name matches neither a command name nor a skill name: flag as an unrecognised subfolder and ask the user whether it is a custom phase or can be removed.

Auto-fix: for skill-named subfolders, offer to move any `.md` files inside them into the appropriate phase subfolder (based on `project_config.md` active phase) and then delete the skill-named folder.

### 9 — CLAUDE.md neuroflow reference

Check whether `.claude/CLAUDE.md` exists in the project repo.

- If it does not exist: flag it — Claude Code will not load project config without it
- If it exists but does not reference `project_config.md`: flag it — Claude Code agents will not know where project memory lives

Auto-fix: if the file exists but is missing the neuroflow block, append the same block that `/neuroflow` writes:

```markdown
## neuroflow

This project uses the neuroflow workflow. Project memory is in `.neuroflow/`.

- Active phase: {phase from project_config.md}
- Config: `.neuroflow/project_config.md`
- Start any session by reading `project_config.md` and `flow.md` first.
```

If the file does not exist at all, create `.claude/CLAUDE.md` with this block.

### 10 — Personal sensitive information

Scan all files inside `.neuroflow/` for patterns that suggest personal sensitive information has been committed. Check for:

- **Email addresses**: search for strings matching `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`. This pattern covers the most common address formats; it does not handle quoted local parts, IP-address domains, or internationalised domain names — note any such edge cases manually. Skip addresses whose domain is clearly synthetic: `example.com`, `example.org`, `test.com`, `domain.com`, or `localhost`.
- **Passwords and secrets**: flag lines where a key matching `password`, `passwd`, `secret`, `api_key`, `token`, or `private_key` (case-insensitive, with `:` or `=` separator) is followed by a non-empty value. A value is considered a placeholder — and should be skipped — if it is all-uppercase (e.g. `YOUR_API_KEY`), enclosed in angle brackets (e.g. `<token>`), or contains the word `placeholder`, `example`, or `changeme`.
- **Private keys**: strings beginning with `-----BEGIN` (PEM-format private keys, certificates, or similar).
- **Full names in unexpected locations**: if a sequence of two or more capitalised words (likely a full name) appears in a reasoning log, session log, or flow.md entry — rather than in `project_config.md` under the `researcher:` field — flag it as a possible name leak. This check may produce false positives on proper nouns and tool names; treat every finding as requiring human confirmation.
- **Institutional affiliations outside project_config.md**: if an institution name, department, or postal address appears in a file other than `project_config.md`, flag it. Treat findings as requiring human confirmation, as false positives on common terms are possible.

Do not print the sensitive value verbatim in the report. Mask it instead (e.g. `email: j***@exam***.com`, `password: ***`, `private key in line 4 of reasoning/general.json`).

Flag each file and line number where a match is found. Mark name and institution findings as `[needs human review]` since automated detection of these categories is imprecise.

### 11 — Flowie structure (if present)

This check only runs if `.neuroflow/flowie/` exists.

- **Git repo:** check that `.neuroflow/flowie/.git/` exists. If the folder exists but is not a git repo, flag it — it should be a clone of the user's private `flowie` GitHub repository.
- **sync.json:** check that `.neuroflow/flowie/sync.json` exists and contains a `github_repo` field with a non-empty value. Flag if missing or empty.
- **flowie_profiles binding:** check that `flowie_profiles` is set and non-empty in `project_config.md`. If `.neuroflow/flowie/` is set up but `flowie_profiles` is absent, flag it — the project should be linked via `/flowie --link`.
- **Project registry match:** if `flowie_profiles` is set AND `projects/projects.json` exists, check that the first entry's handle matches an entry in the projects array. Flag if no matching project is found.
- **flow.md listing:** check that `flowie/` is listed as a row in `.neuroflow/flow.md`. Flag if missing.
- **Migration check:** verify `project_config.md` does NOT contain legacy scalar fields `flowie_project:` or `hive_member:` (replaced by `flowie_profiles:` list). Flag if found and suggest running `/neuroflow` to migrate.

Flag any failed sub-check as a warning (not a blocking error — flowie may be intentionally partial). Group all flowie warnings under a single "⚠️ flowie" section in the report.

Auto-fix: for the flow.md listing, offer to add the missing row. All other issues require user action (re-running `/flowie` or `/flowie --link`).

### 12 — Wiki structure (if present)

Run for each wiki level that exists:

**12a — Flowie wiki** (`if .neuroflow/flowie/wiki/` exists):
- **index.md:** exists and "Last updated" within 90 days
- **log.md:** exists and non-empty
- **schema.md:** exists — if missing, flag and suggest `/flowie --wiki-schema`
- **raw/ and pages/:** both directories exist
- **Orphan check (light):** files in `wiki/pages/` not listed in `wiki/index.md` > 5 → flag, suggest `/flowie --wiki-lint`
- **Log vs pages:** last 10 `ingest` entries in `log.md` — check matching file in `pages/sources/`

Group under "⚠️ wiki (flowie)".

**12b — Project wiki** (`if .neuroflow/wiki/` exists):
- Same checks as 12a, but paths are relative to `.neuroflow/wiki/`
- If `.neuroflow/wiki/` exists but is empty (only `.gitkeep` stubs from init): note as uninitialized — suggest running `/wiki --schema` to initialize
- Check that `wiki/` is listed in `.neuroflow/flow.md`

Group under "⚠️ wiki (project)".

Auto-fix: add missing `wiki/` row to `flow.md`. All other issues require user action.

### 13 — Hive structure (if present)

This check only runs if `.neuroflow/hive/` exists.

- **hive.md:** check that `.neuroflow/hive/hive.md` exists and is non-empty. Flag if missing.
- **members.md:** check that `.neuroflow/hive/members.md` exists. Flag if missing — suggest running `/hive --members` to add team roster.
- **sync.json:** check that `.neuroflow/hive/sync.json` exists and contains `hive_repo` (non-empty) and `last_pull` fields. Flag any missing.
- **project_config.md binding:** check that `hive_repo:` is set in `project_config.md`. If `.neuroflow/hive/` exists but `hive_repo` is absent from config, flag as inconsistency.
- **flow.md listing:** check that `hive/` is listed in `.neuroflow/flow.md`. Flag if missing.
- **No old `directions.md`:** if `.neuroflow/hive/directions.md` exists as a local cache, flag it — directions are now merged into `hive.md` and `directions.md` is obsolete. Offer to delete it.

Group all hive warnings under "⚠️ hive". These are warnings, not blocking errors.

Auto-fix: add missing `hive/` row to `flow.md`. Offer to delete obsolete `directions.md`. All other issues require user action.

## Report

Write to `.neuroflow/sentinel.md`:

```
Last run: YYYY-MM-DD

## Issues found

- [description of issue]

## All clear
(written only if zero issues found)
```

Then ask the user: for each issue, fix automatically or leave for manual review?

## Fixes sentinel can apply automatically

- Add a missing file to the relevant `flow.md`
- Remove a `flow.md` entry for a file that no longer exists
- Update the active phase in `project_config.md` if drift is unambiguous
- Add or update `plugin_version` in `project_config.md` to match the current plugin version (Check 7)
- Move `.md` files out of a skill-named subfolder in `.neuroflow/` into the appropriate phase subfolder, then delete the skill-named folder (Check 8)
- Append the neuroflow block to `.claude/CLAUDE.md`, or create the file, if the reference to `project_config.md` is missing (Check 9)
- For Check 10 (personal sensitive information): sentinel does **not** auto-remove or redact sensitive content — it only surfaces findings. The user must review each flagged item and decide whether to redact, remove, or confirm it is intentionally stored.

After applying any fixes, rewrite `.neuroflow/sentinel.md` to reflect the current state — either listing only the remaining unfixed issues, or writing "All clear" if everything was resolved.

## Optional — Full workspace scan

After completing the `.neuroflow/` audit above, ask the user:

> "Do you also want me to check consistency of the whole project folder (files outside `.neuroflow/`)? This is off by default."

Only proceed with the steps below if the user answers **yes**.

### WS-1 — Untracked / unlisted files

List files in the workspace root that are not tracked in any `flow.md`. Flag files that look like they should be documented (e.g. drafts, backups, data files) and suggest adding them to the relevant `flow.md` or archiving them.

### WS-2 — flow.md cross-references to workspace files

For every entry in any `flow.md` that points to a path **outside** `.neuroflow/`, verify the path exists on disk. Flag broken paths.

### WS-3 — Draft and backup files

Flag any files in the workspace whose name suggests they are backups or working copies (e.g. names containing `_backup`, `_old`, `_draft`, `_temp`, `_copy`, or ending in `.bak`). Note them for the user to archive or delete explicitly.

Do not read the contents of files outside `.neuroflow/` — only check their names and paths.
