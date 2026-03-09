---
name: sentinel
description: Full audit of .neuroflow/ — checks flow.md timestamps, detects drift, compares preregistration vs actual progress, and writes a report to sentinel.md.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/sentinel.md
  - .neuroflow/preregistration/
  - .neuroflow/sessions/
writes:
  - .neuroflow/sentinel.md
  - .neuroflow/project_config.md
---

# /sentinel

## What this command does

Runs a full coherence audit of the `.neuroflow/` folder. Writes a report to `sentinel.md`. If everything is in sync, writes only the last run date and "all clear".

---

## Steps

1. **Read all `flow.md` files** — root + every phase subfolder. Note the last-changed date for each.

2. **Check for drift** — flag any of these:
   - Phase subfolder exists in the repo but has no entry in root `flow.md`
   - `flow.md` in a subfolder hasn't been updated in a long time while the subfolder has new files
   - A file is listed in `flow.md` but does not actually exist
   - `project_config.md` says the current phase is X but the most recent session log mentions phase Y

3. **Check references/** — for every entry in `references/flow.md`, verify the target (URL or local path) still exists. Flag broken links.

4. **Compare preregistration vs progress** — if `preregistration/` exists, read it and compare stated hypotheses and planned analyses against what is recorded in `data-analyze/` and `decisions.md`. Flag deviations.

5. **Update `project_config.md`** — correct the active phase if drift was detected and the correct phase is unambiguous.

6. **Write `sentinel.md`** — list all issues found with a brief description. If no issues: write only the last run date and "all clear".

7. **Ask the user** — for each issue found, ask whether to fix it automatically or leave it for manual review.

---

## sentinel.md format

```
Last run: YYYY-MM-DD

## Issues found

- [issue description]
- [issue description]

## All clear
(written only if no issues)
```
