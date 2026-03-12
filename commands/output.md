---
name: output
description: Output project memory or the whole project — pack it as a zip archive or copy it to a target location for sharing, archiving, or handoff.
phase: output
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/output/flow.md
writes:
  - .neuroflow/output/
  - .neuroflow/output/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /output

Pack and move project data out of the current workspace. Useful for sharing with collaborators, handing off to a supervisor, archiving before a major change, or backing up project state.

Read the `neuroflow:phase-output` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` and `flow.md` before starting.

---

## Step 0 — Check for .neuroflow/

If `.neuroflow/` does not exist, stop and tell the user to run `/neuroflow` first.

---

## Step 1 — Read project state

Read `.neuroflow/project_config.md` and `.neuroflow/flow.md`.

If `.neuroflow/output/` does not exist yet, create it now:
- Create `output/flow.md` with the standard index table (empty, today's date)
- Update the root `.neuroflow/flow.md` to add a row for `output/`

If `output/` exists, read `output/flow.md`.

---

## Step 2 — Choose what to export

Ask the user which scope to export:

| Option | What is included |
|---|---|
| **A — Project memory** | `.neuroflow/` only — project config, flow indexes, reasoning logs, phase notes, preregistration, ethics, finance, fails. Excludes `sessions/` (local-only) and `integrations.json` (credentials). |
| **B — Whole project** | All git-tracked files in the repository **plus** the `.neuroflow/` memory folder (excluding `sessions/` and `integrations.json`). |
| **C — Specific phase** | One phase subfolder from `.neuroflow/{phase}/` plus `project_config.md` and `flow.md`. User selects which phase. |

If the user is unsure, recommend **A** for sharing project context and **B** for full archiving or handoff.

---

## Step 3 — Choose the output format

Ask the user which output format they want:

| Option | When to use |
|---|---|
| **Zip archive** | Cross-platform sharing, email attachments, long-term archiving |
| **Folder copy** | Local backups, moving to another drive or shared network folder |

Default: **Zip archive**.

---

## Step 4 — Choose the destination

Ask: *"Where should the export be saved?"*

Suggest a sensible default: `./output-[project-slug]-[YYYY-MM-DD].zip` (or folder) in the current working directory, where `project-slug` is the project name from `project_config.md` lowercased with spaces replaced by hyphens.

---

## Step 5 — Confirm and export

Show the user a summary before proceeding:

```
Export summary
──────────────
Scope:       <A / B / C — phase name>
Format:      <zip / folder>
Destination: <resolved path>
Excludes:    sessions/, integrations.json

Proceed? [Y/n]
```

If the user confirms, run the export:

### Zip archive

Use Python's built-in `zipfile` module (preferred — no external dependencies) or the system `zip` command as a fallback:

```python
import zipfile, os, datetime
# walk the selected scope, add files to archive
# skip sessions/ and integrations.json
```

Alternatively, if Python is unavailable, try:
```bash
zip -r "<destination>" <source-paths> --exclude "*/sessions/*" --exclude "*/integrations.json"
```

### Folder copy

Use `cp -r` (macOS/Linux) or `xcopy /E` (Windows) to copy the selected scope to the destination, then manually remove `sessions/` and `integrations.json` from the copy.

---

## Step 6 — Verify and report

After the export completes:

1. Verify the output exists at the destination path.
2. If it is a zip, report the file size.
3. If it is a folder, report the number of files copied.

Tell the user what was excluded and why:
> Sessions and credential files are excluded by default — they are local-only and should not be shared.

---

## Step 7 — Log the output

Write an output log entry to `.neuroflow/output/`:

Save as `output-[YYYY-MM-DD-HH-mm].md`:

```
date: YYYY-MM-DD HH:MM
scope: <memory / whole-project / phase:name>
format: <zip / folder>
destination: <resolved path>
excluded: sessions/, integrations.json
size: <file size or file count>
```

Update `.neuroflow/output/flow.md` immediately.

Append to `.neuroflow/sessions/YYYY-MM-DD.md`:

```
[HH:MM] /output — Output <scope> as <format> to <destination>.
```

---

## At end

- Updated `output/flow.md` with the new log entry
- Appended to `sessions/YYYY-MM-DD.md`
- Confirmed the export file or folder exists at destination
