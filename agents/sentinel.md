---
name: sentinel
description: Project coherence guard. Audits .neuroflow/ for internal consistency — checks flow.md completeness, timestamps, broken references, preregistration drift, and session consistency. Scoped to .neuroflow/ by default; full workspace scan is opt-in. Called by the /sentinel command.
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
- Also allow the standard root subfolders that are not phase-specific: `sessions`, `reasoning`, `ethics`, `preregistration`, `finance`.

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
