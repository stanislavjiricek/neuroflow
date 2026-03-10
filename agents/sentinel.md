---
name: sentinel
description: Project coherence guard. Audits .neuroflow/ against the actual repository — checks flow.md timestamps, broken references, preregistration drift, and session consistency. Called by the /sentinel command.
---

# sentinel

Audits the `.neuroflow/` folder for consistency and drift. Called by the `/sentinel` command. Writes its report to `.neuroflow/sentinel.md`.

## Checks

### 1 — flow.md completeness

Read root `.neuroflow/flow.md` and every phase subfolder's `flow.md`. For each:
- Every file listed in `flow.md` must actually exist on disk
- Every file that exists in the subfolder must be listed in `flow.md`
- Flag any mismatches

### 2 — Timestamp drift

Check `flow.md` last-changed dates against actual file modification times. Flag:
- Subfolders with recent file activity but stale `flow.md`
- Subfolders that haven't been touched in a long time while the project is active (possible abandoned phase)

### 3 — Broken references

If `references/` exists, read `references/flow.md`. For each entry:
- If it is a local path: check that the path exists
- If it is a URL: note it (do not fetch — just list for user review)

Flag any local paths that no longer exist.

### 4 — Phase consistency

Compare:
- Active phase in `project_config.md`
- Most recent session log in `sessions/`
- Which phase subfolders exist and when they were last modified

Flag if these tell different stories.

### 5 — Preregistration vs progress

If `preregistration/` exists, read it. Compare stated hypotheses and planned analyses against:
- `decisions.md` (were there undocumented deviations?)
- `.neuroflow/data-analyze/` analysis summary (were different analyses run?)

Flag deviations. Do not judge — just surface them for the user.

### 6 — linked_flows.md

If `linked_flows.md` exists, check that all listed paths resolve to actual `.neuroflow/` folders.

### 7 — Plugin version sync

Read the neuroflow `plugin.json` to get the current plugin version. Compare it against `plugin_version` in `project_config.md`.

- If `plugin_version` is missing from `project_config.md`: flag it — the field is required
- If the plugin version is higher than `plugin_version` in `project_config.md`: flag as out of sync — the plugin has been updated since this project was last configured, structural changes may apply
- If versions match: all clear

Auto-fix: update `plugin_version` in `project_config.md` to match the current plugin version.

### 8 — CLAUDE.md neuroflow reference

Check whether `.claude/CLAUDE.md` exists in the project repo.

- If it does not exist: flag it — Claude Code will not load project config without it
- If it exists but does not reference `project_config.md`: flag it — Claude Code agents will not know where project memory lives

Auto-fix: if the file exists but is missing the neuroflow block, append the same block that `/start` writes:

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
- Append the neuroflow block to `.claude/CLAUDE.md`, or create the file, if the reference to `project_config.md` is missing (Check 8)

After applying any fixes, rewrite `.neuroflow/sentinel.md` to reflect the current state — either listing only the remaining unfixed issues, or writing "All clear" if everything was resolved.
