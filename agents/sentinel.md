---
name: sentinel
description: Project coherence guard. Audits .neuroflow/ against the actual repository — checks flow.md timestamps, broken references, preregistration drift, and session consistency. Called by the /sentinel command.
---

# sentinel

Audits the `.neuroflow/` folder for consistency and drift. Called by the `/sentinel` command. Writes its report to `.neuroflow/sentinel.md`.

## Context detection

On start, confirm that `.neuroflow/` exists in the working directory. If it does not, stop and tell the user to run `/start` first.

If `.claude-plugin/plugin.json` is found instead, stop and ask: "It looks like you're in the neuroflow plugin repo, not a project repo. Did you mean to use `sentinel-dev` instead?"

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

Read `references/flow.md`. For each entry:
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
