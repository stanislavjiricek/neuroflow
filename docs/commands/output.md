---
title: /output
---

# `/neuroflow:output`

**Output project memory or the whole project as a zip archive or folder copy — plus `--archive` for publication and `--handoff` for a project handoff.**

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
| **Project memory** | `.neuroflow/` team-tier memory — project config, flow indexes, reasoning logs, phase notes, preregistration, tasks, wiki, non-identifying ethics documents. |
| **Whole project** | All git-tracked files **plus** the same `.neuroflow/` memory. |
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

The exporter script (`skills/phase-output/scripts/export.py`) builds the file list first and drops these before anything is copied, regardless of scope:

| Excluded | Reason |
|---|---|
| `.neuroflow/sessions/`, `.neuroflow/review/`, `.neuroflow/integrations.json`, `.neuroflow/flowie/`, `.neuroflow/paper/xray-*`, `.neuroflow/wiki/.pending/` | Local tier — personal logs, colleagues' confidential manuscripts, credentials, sentence-level critiques of your unpublished manuscript, wiki cards still waiting for your review |
| `.neuroflow/fails/`, `.neuroflow/finance/` | Never leave the team |
| `.neuroflow/ethics/` files other than `status.md`, `flow.md`, `consent-vN.md`, `protocol*.md`, `amendment*.md` | May identify participants (a file you checked can be added explicitly) |
| `.env`, `*.pem`, private SSH keys, `client_secret*.json` and similar, anywhere | Credentials |

You see a dry run — what leaves, its size, and what is held back and why — and confirm it before anything is written. The result is verified against that list. A destination inside the exported tree is refused, so whole-project exports go to the folder above the project.

---

## `--archive` — publication archiving

Prepares a dataset or code for a public repository with a DOI. The readiness checklist includes three scripts:

- **Header scan** (`header_scan.py`) — EDF/BDF, BrainVision and NIfTI headers (FIF with MNE installed) and `participants.tsv` columns, checked for names, birth dates, IDs and other identifying fields.
- **Personal-data scan** (`pii_scan.py`) — emails, phone numbers, ID patterns you configure, names from a hashed participant roster, and secrets in text files.
- **Git-history audit** (`history_audit.py`) — before a repository goes public: every commit is checked for memory that must stay private, credentials, recordings and large files. Deleted files are still in the history, so the clean route is often a fresh publication repository made from an export.

None of them prints a found value — only the file, the field and the kind of finding.

---

## `--handoff` — project handoff dossier

When a project changes hands, `handoff.py` collects (read-only) git state, data roots, the preregistration freeze, ethics status, open tasks by assignee and the integrations the successor must replace. You complete the checklist together and the dossier is saved as `.neuroflow/output/handoff-YYYY-MM-DD.md` — never uploaded.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/output/flow.md` |
| Writes | `.neuroflow/output/` (export log, archive record, handoff dossier), `.neuroflow/sessions/YYYY-MM-DD.md` |

---

## Related commands

- [`/neuroflow`](neuroflow.md) — full project status before exporting
- [`/write-report`](write-report.md) — generate a human-readable summary to include in the export
