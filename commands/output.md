---
name: output
description: Output project memory or the whole project — pack it as a zip archive or copy it to a target location for sharing, archiving, or handoff. Use --archive for publication archiving — repository prep (OpenNeuro/OSF/Zenodo), license, de-identification checklist, and DOI recording.
phase: output
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/output/flow.md
writes:
  - .neuroflow/output/
  - .neuroflow/output/flow.md
  - .neuroflow/project_config.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /output

Pack and move project data out of the current workspace. Useful for sharing with collaborators, handing off to a supervisor, archiving before a major change, or backing up project state.

Read the `neuroflow:phase-output` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` and `flow.md` before starting.

**`--archive` mode** — publication archiving (dataset/code to a public repository with a DOI) is a different job from backup; its spec is at the end of this file. A zip in a folder is a backup; archiving is what journals and funders mean by "data availability".

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
## HH:MM — [output] Output <scope> as <format> to <destination>.
```

---

## At end

- Updated `output/flow.md` with the new log entry
- Appended to `sessions/YYYY-MM-DD.md`
- Confirmed the export file or folder exists at destination

---

## Mode: `--archive` — publication archiving

Prepare the dataset and/or code for deposit in a public repository with a DOI. This mode **guides and verifies** — the actual upload happens in the user's browser/CLI (repositories require authenticated accounts); neuroflow prepares everything so the upload is a formality, then records the result.

### Step A1 — What is being archived

Ask: dataset, code, or both? Then recommend the repository:

| Content | Recommend |
|---|---|
| Neuroimaging/ephys dataset in BIDS | **OpenNeuro** (free, BIDS-native, DOI, no size fuss for typical datasets) |
| Non-BIDS dataset, mixed materials, prereg linkage | **OSF** (DOI, versioning, links to preregistration) |
| Code / analysis pipeline | **Zenodo** via GitHub release integration (DOI per release), code stays on GitHub |
| Dataset with heavy access restrictions (clinical) | **EBRAINS or institutional repository** — flag that consent/GDPR terms decide, not preference |

### Step A2 — Readiness checklist (run every item, report ✅/❌)

1. **De-identification** — no participant names, dates of birth, or facial features (defacing for anatomical MRI); check `participants.tsv` columns against what consent permits. For BIDS data, invoke the `neuroflow:bids` skill and run `bids-validator`.
2. **Consent covers sharing** — check `.neuroflow/ethics/status.md` exists and the consent form version in force permits public deposit. If `/ethics` was never run, warn and ask the user to confirm manually.
3. **License chosen** — data: CC0 or CC-BY (OpenNeuro requires CC0); code: ask (MIT/BSD/GPL); record the choice in a reasoning entry.
4. **README completeness** — dataset description, citation instructions, contact; generate a draft if missing.
5. **Code freshness** — if archiving code, check the repo has no uncommitted changes and suggest a tagged release.

Do not proceed past a ❌ without the user explicitly accepting the gap.

### Step A3 — Deposit and record

1. Walk the user through the deposit for the chosen repository (login → create dataset/release → upload → publish), one step at a time.
2. When the DOI exists, record it: `project_config.md` (`dataset_doi:` / `code_doi:` field), `.neuroflow/output/archive-YYYY-MM-DD.md` (what, where, license, DOI, checklist results), and offer to update the data/code availability statements in the manuscript (`/paper --submit` reads these).
3. Session milestone: `## HH:MM — [output] Archived {what} to {repository}: {DOI}`. Reasoning entry for the license/repository choice.
