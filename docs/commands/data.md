---
title: /data
---

# `/neuroflow:data`

**Data intake — locate, inventory, validate, and convert your raw data.**

`/data` takes raw recorded data and gets it ready for preprocessing. It covers locating and inventorying the data, checking BIDS compliance, and running conversion scripts if needed.

---

## When to use it

- You've finished data collection and need to organize raw files
- You want to check if your data is BIDS-compliant
- You need to convert from a proprietary format (BrainVision, EDF, etc.) to MNE/BIDS
- You're starting fresh with an existing dataset

---

## Before the steps — ethics and data access

- **Ethics gate.** For data from your own participants, Claude first reads `.neuroflow/ethics/status.md`. If the approval is missing, expired, or was not confirmed by a person, intake stops and Claude says why and points to [`/ethics`](ethics.md). Public de-identified datasets and projects marked `ethics: not-applicable` are outside the gate.
- **What the model may read.** `ai_processing` in the same file decides whether Claude may open participant-level files. With `none`, Claude looks at file names, sidecars and column names only, writes the scripts, and works from what they print in aggregate.

## Three steps

Claude works through these in order:

### Step 1 — Locate and inventory

Claude uses Glob and file inspection to understand your data:

- How many subjects / sessions / runs
- File formats present
- Whether it looks BIDS-compliant already
- Where it lives — a synced folder (OneDrive, Dropbox, iCloud Drive, Google Drive) or a network share gets a warning and a recommendation to work on a local copy
- Which folders hold the original recordings — recorded as `raw_roots` in `project_config.md` (after asking), and read-only from then on
- Whether it is a DataLad dataset — then `datalad get` / `run` / `unlock` / `rerun` are used instead of a parallel log
- Collected vs planned participants (e.g. 18/48) when the preregistration records `planned_n`
- That `participants.tsv` and file names hold pseudonyms only

```
Claude: I found 24 subject folders (sub-01 through sub-24), each with:
        - sub-XX_task-oddball_eeg.vhdr
        - sub-XX_task-oddball_eeg.vmrk
        - sub-XX_task-oddball_eeg.eeg

        No dataset_description.json or participants.tsv found.
        This is not yet BIDS-compliant.

        Saving inventory to .neuroflow/data/data-inventory.md
```

**Output:** `data-inventory.md` saved to `.neuroflow/data/`

### Step 2 — Validate BIDS structure

Checks for BIDS compliance:
- Naming conventions (`sub-XX_task-YY_eeg.vhdr`)
- Required files (`dataset_description.json`, `participants.tsv`, `events.tsv`)
- Sidecar JSON completeness

If bids-validator is installed, its `--json` output is condensed by `bids_digest.py` into counts per issue code with the first locations — no issue code is dropped, and the full JSON is kept.

If data is not in BIDS format, Claude asks whether you want to convert or proceed as-is.

### Step 3 — Convert

Raw recordings are never modified: conversion reads from them and writes the BIDS copy elsewhere. BrainVision files are never renamed by hand — `.vhdr`, `.vmrk` and `.eeg` point to each other by name, so a renamed set breaks; MNE-BIDS writes the copy and fixes the pointers.

Runs or writes conversion scripts for common cases:

| Source format | Target format |
|---|---|
| BrainVision (`.vhdr`/`.vmrk`/`.eeg`) | MNE Raw → FIF, or BIDS via MNE-BIDS |
| EDF / EDF+ | MNE Raw → FIF |
| Raw folder structure | BIDS layout |
| `.set` (EEGLAB) | MNE Raw |

Conversion scripts are saved in your project repository (not inside `.neuroflow/`).

**Output:** `data-intake.md` saved to `.neuroflow/data/`

---

## Example session

```
/neuroflow:data
```

```
You: Data is in data/raw/ — BrainVision format, 24 subjects.

Claude: Found 24 subjects in data/raw/. BrainVision format (.vhdr/.vmrk/.eeg).
        No BIDS structure detected.

        Do you want to convert to BIDS format?
        1. Yes — convert with MNE-BIDS
        2. No — proceed as-is (I'll note the raw paths)

You: Yes — convert to BIDS.

Claude: I'll write a conversion script using mne_bids.write_raw_bids().
        The script will:
        - Create dataset_description.json with your study metadata
        - Create participants.tsv from your subject list
        - Convert each .vhdr file to BIDS naming convention
        - Add sidecar JSONs with EEG metadata

        [generates scripts/convert_to_bids.py]
```

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/data/flow.md`, `.neuroflow/ethics/status.md`, `.neuroflow/preregistration/status.md` |
| Writes | `.neuroflow/data/`, `.neuroflow/data/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md`, `scripts/` (conversion code) |

---

## Related commands

- [`/ethics`](ethics.md) — the approval and `ai_processing` this command checks first
- [`/experiment`](experiment.md) — the recording setup that generated this data
- [`/data-preprocess`](data-preprocess.md) — the next step after data intake
