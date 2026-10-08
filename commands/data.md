---
name: data
description: Data intake — locate data, validate BIDS structure, and run conversion scripts to get raw data ready for preprocessing.
phase: data
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/data/flow.md
  - .neuroflow/ethics/status.md
  - .neuroflow/preregistration/status.md
  - skills/phase-data/SKILL.md
writes:
  - .neuroflow/data/
  - .neuroflow/data/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
lifecycle: full
produces:
  - .neuroflow/data/data-inventory.md
  - .neuroflow/data/data-intake.md
next:
  - data-preprocess
---

# /data

Read the `neuroflow:phase-data` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` (and open with the version notice when the project's `plugin_version` is missing or older than the running neuroflow's version in `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` — **Command lifecycle**, step 3), `flow.md`, and `.neuroflow/data/flow.md` before starting. Invoke `neuroflow:bids` whenever BIDS structure, validation, or conversion is involved.

## Before you start — ethics and data access

<!-- nf-rule: ETHICS-GATE -->
**No data collection steps before ethics status is approved.** Before the intake of data from your own human participants, read the frontmatter of `.neuroflow/ethics/status.md` (see `/ethics` → The gate; a legacy table-only file counts with its `Status` and `Expires` rows). If `status` is not `approved`, it was set by the model (`set_by: model`), or `expires` has passed, stop steps 1–3 for that data and say why, naming `/ethics --approved`. Public de-identified datasets and projects that note `ethics: not-applicable` in the `project_config.md` frontmatter are outside the gate; if the person says the data were collected under an approval that has since expired, record that statement in `data-inventory.md` and continue.

<!-- nf-rule: PARTICIPANT-ROUTE -->
**Participant data is read by the model only if `ai_processing` allows it** (`/ethics` → AI processing; missing means `none`). File names, sidecar JSON and column names are fine; under `none`, recordings, `participants.tsv` rows and `sourcedata/` contents are not — write the script, let the person run it, and work from its aggregate output.

## What this command does

Takes raw recorded data and gets it ready for preprocessing. Three steps — work through them in order:

1. **Locate and inventory** — find the data, understand what is there
2. **Validate structure** — check BIDS compliance or document the current structure
3. **Convert** — run conversion scripts if needed (raw → BIDS, BrainVision → MNE, EDF → FIF, etc.)

---

## Steps

### 1 — Locate and inventory

Ask the user where the data is. Use Glob and Read to inspect the directory. Document:
- How many subjects / sessions / runs
- File formats present
- Whether it looks BIDS-compliant already
- **Where it lives.** If the path is inside a synced folder (OneDrive, Dropbox, iCloud Drive, Google Drive) or on a network share (`\\server\share`, `//server/share`, a mapped network drive, an SMB/NFS mount), say so: sync clients rewrite and lock files mid-run, online-only placeholders download when read, and a `.git` folder inside a sync root can be corrupted. Recommend a local working copy (copy the raw data to a local disk, keep the share as the archive) and record the location type.
- **The raw folders.** Offer to record the folder(s) holding the original recordings in `raw_roots` in the `project_config.md` frontmatter (ask first). From then on they are read-only (step 3).
- **DataLad.** If the dataset has a `.datalad/` folder, record it. Use `datalad get` for file content, `datalad run` to record analysis commands, `datalad unlock` only before a deliberate edit, and `datalad rerun` to reproduce; do not build a parallel provenance log next to it. On Windows, annexed files sit on an adjusted branch and are not locked, so "locked" does not mean read-only there.
- **Collected vs planned N.** If `.neuroflow/preregistration/status.md` has `planned_n`, write collected/planned (e.g. 18/48) into the inventory.
- **Identifiers.** `participants.tsv` and file names hold pseudonyms (`sub-XX`) only. If you see names, birth dates or contact details, stop and tell the person; the identity key and signed consent forms belong outside the project tree.

Save a `data-inventory.md` in `.neuroflow/data/`.

### 2 — Validate BIDS structure

Check BIDS naming conventions, required files (`dataset_description.json`, `participants.tsv`, `events.tsv`), and sidecar JSONs. Document any violations.

If bids-validator is available, run it with `--json` to a file and digest that file: `python <bids base dir>/scripts/bids_digest.py bids-validator.json` (the `neuroflow:bids` skill's folder). Exit 0 = no errors, 1 = errors listed per code with locations, 2 = not validator JSON. Keep the full JSON next to the digest and name it in `data-inventory.md`.

If the data is not in BIDS format, ask whether the user wants to convert it or proceed as-is.

### 3 — Convert

<!-- nf-rule: RAW-READONLY -->
**Files under `raw_roots` are never modified** (while `raw_roots` is unset, treat `sourcedata/` and the original recordings the person pointed to the same way). Conversion reads from the raw folders and writes somewhere else (the BIDS tree, `derivatives/`). Never rename, move, edit or delete a raw file, and never convert in place. BrainVision is the classic trap: `.vhdr`, `.vmrk` and `.eeg` point to each other by file name inside the header, so renaming them breaks the recording. Write BIDS copies with `mne_bids.write_raw_bids()` or `mne_bids.copyfiles.copyfile_brainvision()`, which rewrite the pointers.

Run or write conversion scripts as needed. Common cases:
- BrainVision (`.vhdr`/`.vmrk`/`.eeg`) → MNE Raw → FIF
- EDF → MNE Raw → FIF
- Raw folder → BIDS structure

Save conversion scripts in the project repo. Document the conversion in `data-intake.md` in `.neuroflow/data/`.

---

## At end

- Update `.neuroflow/data/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `active_phase` in `project_config.md` if the phase changed
