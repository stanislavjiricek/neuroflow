---
name: output
description: Output project memory or the whole project — pack it as a zip archive or copy it to a target location for sharing, archiving, or handoff. Use --archive for publication archiving (repository prep, license, de-identification and git-history checks, DOI recording) and --handoff for a project handoff dossier.
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
lifecycle: full
produces:
  - .neuroflow/output/
---

# /output

Pack and move project data out of the current workspace. Useful for sharing with collaborators, handing off to a supervisor, archiving before a major change, or backing up project state.

Read the `neuroflow:phase-output` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` and `flow.md` before starting.

**`--archive` mode** — publication archiving (dataset/code to a public repository with a DOI) is a different job from backup; its spec is at the end of this file. A zip in a folder is a backup; archiving is what journals and funders mean by "data availability".

**`--handoff` mode** — when the project changes hands, compile a handoff dossier for the successor (spec after `--archive`).

All modes use the scripts in the phase-output skill's `scripts/` folder (`<phase-output skill base dir>` below is that skill's base directory). They apply the sharing tiers in code (neuroflow-core → Sharing tiers) and never print secret or personal values.

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
| **A — Project memory** | `.neuroflow/` team-tier memory — project config, flow indexes, reasoning logs, phase notes, preregistration, tasks, wiki, and the ethics documents on the non-identifying allowlist. |
| **B — Whole project** | All git-tracked files in the repository **plus** the same `.neuroflow/` memory. |
| **C — Specific phase** | One phase subfolder from `.neuroflow/{phase}/` plus `project_config.md` and `flow.md`. User selects which phase. |

If the user is unsure, recommend **A** for sharing project context and **B** for full archiving or handoff.

Whatever the scope, these never leave through `/output` (neuroflow-core → Sharing tiers): the local tier (`sessions/`, `review/`, `integrations.json`, `flowie/`, `paper/xray-*`, `wiki/.pending/`), `fails/`, `finance/`, ethics files that are not on the non-identifying allowlist (`status.md`, `flow.md`, `consent-vN.md` form versions, `protocol*.md`, `amendment*.md`), and credential files anywhere in the tree (`.env`, `*.pem`, private SSH keys, `client_secret*.json`, …). The exporter drops them from the file list before anything is copied.

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

Suggest a sensible default: `output-[project-slug]-[YYYY-MM-DD].zip` (or folder), where `project-slug` is `project_name` from the `project_config.md` frontmatter, lowercased with spaces replaced by hyphens — in the project root for scopes A and C, and in the folder **above** the project root for scope B. The destination may never sit inside the tree being exported (`.neuroflow/` for A and C, the whole project for B); the exporter refuses it.

---

## Step 5 — Preview, confirm and export

Export only with the exporter script — never with `zip`, `tar`, `cp`, `xcopy` or `Compress-Archive`, which skip the exclusions. If Python is not available, stop and say so.

1. **Dry run** — list exactly what would leave (`--scope memory` = A, `project` = B, `phase --phase NAME` = C):
   ```bash
   python <phase-output skill base dir>/scripts/export.py --scope memory|project|phase [--phase NAME] --format zip|folder --dest "<destination>" --dry-run --json
   ```
2. **Show and confirm** — ask with `AskUserQuestion`; put the plan in the option preview (file count, total size, per-folder totals, and the full held-back list with reasons):
   ```
   Export summary
   ──────────────
   Scope:       <A / B / C — phase name>
   Format:      <zip / folder>
   Destination: <resolved path>
   Leaves:      <N files, size>
   Held back:   <M paths, with reasons>

   Proceed? [Y/n]
   ```
   <!-- nf-rule: EGRESS-CONFIRM -->
   Nothing is written until the person confirms in this turn. A held-back ethics file is added only after the person has checked that it holds no participant-identifying content: rerun with `--include-ethics <path>`. Local-tier paths, `fails/`, `finance/` and credential files have no override — if the person needs one of them elsewhere, they copy it themselves.
3. **Export** — run the same command without `--dry-run`. Exit codes:
   - `0` — written and verified against the plan (the zip's file list is re-read; a folder copy is checked file by file).
   - `1` — written, but verification failed: delete the faulty output, report the listed problems, offer to retry.
   - `2` — refused or failed (no `.neuroflow/`, destination inside the exported tree or already present, no git repository for scope B, unknown phase): fix what the message names and start again from the dry run.

---

## Step 6 — Report

Report the destination, the size (zip) or file count (folder), and what was held back and why:
> Local-only memory (sessions, referee reviews, credentials), the fails and finance logs, and ethics files that could identify participants never leave through `/output`.

---

## Step 7 — Log the output

Write an output log entry to `.neuroflow/output/`:

Save as `output-[YYYY-MM-DD-HH-mm].md`:

```
date: YYYY-MM-DD HH:MM
scope: <memory / whole-project / phase:name>
format: <zip / folder>
destination: <resolved path>
held back: <count, by reason>
size: <file size or file count>
verified: yes
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
- The exporter verified the export file or folder at the destination

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

1. **De-identification** — no participant names, dates of birth, IDs or facial features in anything deposited:
   - Run the header scan over the dataset: `python <phase-output skill base dir>/scripts/header_scan.py "<dataset folder>" --json`. It reads EDF/BDF, BrainVision and NIfTI headers (FIF only with MNE installed) and `participants.tsv`, and reports fields and classes, never values. Exit `0` → clean; `1` → findings or files it could not scan: fix each finding (anonymise the header, drop the column) or have the person accept it explicitly, and install MNE (`pip install mne`) or check unscanned files by hand; `2` → usage error.
   - Read the `participants.tsv` column names yourself too: the script's list of identifying column names is English — columns named in other languages are yours to catch. Check the columns against what consent permits.
   - Text in the deposit (code, notes, memory): `python <phase-output skill base dir>/scripts/pii_scan.py <paths> --json` (emails, phone numbers, configured ID patterns, roster names, secrets; same exit codes).
   - Faces: anatomical MRI must be defaced — the header scan does not check images. For BIDS data, invoke the `neuroflow:bids` skill and run `bids-validator`.
2. **Consent covers sharing** — check `.neuroflow/ethics/status.md` exists and the consent form version in force permits public deposit, and that no participant who withdrew consent is in the deposit. If `/ethics` was never run, warn and ask the user to confirm manually.
3. **License chosen** — data: CC0 or CC-BY (OpenNeuro requires CC0); code: ask (MIT/BSD/GPL); record the choice in a reasoning entry.
4. **README completeness** — dataset description, citation instructions, contact; generate a draft if missing.
5. **Code freshness** — if archiving code, check the repo has no uncommitted changes and suggest a tagged release. If the pipeline wrote provenance records (`provenance/*.json` and `environment.md`, from the data-analyze skill's `nf_provenance.py`), keep them in the deposit and verify each first: `python <phase-data-analyze skill base dir>/scripts/nf_provenance.py verify <record>` (exit `1` = recorded outputs changed or missing — re-run or explain before depositing).
6. **Git history** — required before any repository becomes public (a code DOI through a public repository needs one): `python <phase-output skill base dir>/scripts/history_audit.py --json`. Going public publishes every commit: memory, credentials and participant files deleted long ago are still in the history, and existing clones keep it. Exit `0` → write the audited HEAD commit into the archive record; `1` → do not change the repository's visibility. Offer the clean route — a new publication repository made from a scope-B folder export (`export.py --scope project --format folder`, then `git init` inside the copy: no history) — or a history rewrite the person runs with a dedicated tool, and rotate every credential the audit found; then audit again. `2` → not a git repository or a git error.
7. **Clean-room reproduction** (optional — offer it; if declined, record "not run") — rerun the confirmatory results from a fresh clone in a fresh environment: `python <phase-data-analyze skill base dir>/scripts/cleanroom.py --record <nf_provenance run record> --requirements requirements.txt --link <untracked input data> --report .neuroflow/data-analyze/cleanroom-<date>.md` (in the background for long pipelines). ✅ only on exit `0`; `1` → ❌, list the outputs that differ or are missing; `2` → setup failed (clone, environment, data link): fix and rerun.

Do not proceed past a ❌ without the user explicitly accepting the gap; record each accepted gap in the archive record.

### Step A3 — Deposit and record

1. Walk the user through the deposit for the chosen repository (login → create dataset/release → upload → publish), one step at a time.
2. When the DOI exists, record it: `project_config.md` (`dataset_doi:` / `code_doi:` field), `.neuroflow/output/archive-YYYY-MM-DD.md` (what, where, license, DOI, checklist results), and offer to update the data/code availability statements in the manuscript (`/paper --submit` reads these).
3. Session milestone: `## HH:MM — [output] Archived {what} to {repository}: {DOI}`. Reasoning entry for the license/repository choice.

---

## Mode: `--handoff` — project handoff dossier

When a student leaves mid-project or a project changes hands, compile what the successor needs that no single file states, and list what stays with the person leaving. This mode uploads and shares nothing.

### Step H1 — Collect

Run `python <phase-output skill base dir>/scripts/handoff.py --json` (add `--no-hpc` when not on a cluster). It is read-only: git state (uncommitted, unpushed, stashed, local-only branches), data roots, the preregistration freeze (verified by the preregistration freeze script), ethics status and expiry, open tasks by owner (a task naming several people is listed under each), integrations connected with personal credentials (key names only), HPC jobs. Exit `0` → nothing needs attention; `1` → items under `attention` need the person; `2` → no `.neuroflow/` or a runtime error.

### Step H2 — Complete it with the person

Walk through the attention items, then what the script cannot know:
- Who takes over each open task.
- Running analyses and scheduled or long-running loops (e.g. autoresearch): stop, hand over or document each.
- Shared services connected with the leaver's own credentials (repository hosting, OSF/Zenodo, team hive, cloud storage, HPC allocation): the successor connects their own accounts; rotate any shared secret the leaver knew.
- Ethics: is the successor on the approved study personnel list? If not, an amendment comes before they handle participant data.
- Data custody: where raw data and the identity key live, and who holds access.
- Unpushed work: the person commits and pushes it before leaving — each push only after they confirm.

### Step H3 — Write the dossier

Write `.neuroflow/output/handoff-YYYY-MM-DD.md` (team tier — the successor reads it from the repository). It holds key names and paths only: never credentials, tokens or participant data. List separately what stays with the person leaving and is never handed over: `~/.neuroflow/` (flowie profile, wellbeing data, private notes, personal ideas, `user.yaml`, `integrations.json`), Claude Code's own MCP configuration, `.neuroflow/sessions/`, `.neuroflow/review/`, `.neuroflow/paper/xray-*`, `.neuroflow/wiki/.pending/`.

Do not write `ONBOARDING.md` or any other file in the project root, and do not upload the dossier anywhere: it reaches the successor through a commit the person pushes, or an `/output` export. Update `output/flow.md`; session milestone: `## HH:MM — [output] Handoff dossier written: {N} attention items`.
