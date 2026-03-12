---
title: /output
---

# `/neuroflow:output`

**Output project memory or the whole project as a zip archive or folder copy.**

`/output` packages your project data out of the current workspace — for sharing with collaborators, handing off to a supervisor, archiving before a major change, or backing up project state.

---

## When to use it

- You want to share project context with a collaborator who doesn't have access to your repo
- You're handing off the project to a supervisor or co-investigator
- You want to archive the project state before a major refactor
- You need to submit data and documentation to a repository

---

## Export scopes

| Scope | What is included |
|---|---|
| **Project memory** | `.neuroflow/` only — project config, flow indexes, reasoning logs, phase notes, preregistration, ethics, finance, fails. Excludes `sessions/` and `integrations.json`. |
| **Whole project** | All git-tracked files **plus** `.neuroflow/` memory (excluding `sessions/` and `integrations.json`). |
| **Specific phase** | One phase subfolder from `.neuroflow/{phase}/` plus `project_config.md` and `flow.md`. |

!!! tip "Not sure which scope?"
    Use **Project memory** for sharing context with a collaborator. Use **Whole project** for full archiving or handoff.

---

## Output formats

| Format | When to use |
|---|---|
| **Zip archive** | Cross-platform sharing, email attachments, long-term archiving |
| **Folder copy** | Local backups, moving to another drive or shared network folder |

Default: **zip archive**.

---

## Safety exclusions

The following are always excluded, regardless of scope:

| Excluded | Reason |
|---|---|
| `.neuroflow/sessions/` | Local-only session logs, can be large, no research value outside the machine |
| `.neuroflow/integrations.json` | API credentials — must never be shared |

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/output/flow.md` |
| Writes | `.neuroflow/output/` (export log), `.neuroflow/sessions/YYYY-MM-DD.md` |

---

## Related commands

- [`/neuroflow`](neuroflow.md) — full project status before exporting
- [`/write-report`](write-report.md) — generate a human-readable summary to include in the export
