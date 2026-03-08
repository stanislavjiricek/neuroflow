---
description: Validate the BIDS directory structure of a neuroscience dataset — checks file naming, required files, JSON sidecars, participants.tsv, and events files. Reports all violations with fix suggestions.
argument-hint: [dataset-path]
allowed-tools: [Read, Bash, Glob]
---

# /check-bids — Validate BIDS Structure

You are validating a neuroscience dataset for BIDS compliance.

**Dataset path**: $ARGUMENTS

## Your Task

Perform a comprehensive BIDS compliance check without requiring the official validator to be installed.

## Step 1: Locate Dataset

1. Use the path from arguments, or current directory if not provided
2. Look for `dataset_description.json` to confirm this is a BIDS root
3. If not found, report: "No BIDS dataset_description.json found at [path]. Is this the BIDS root?"

## Step 2: Check Required Root Files

Verify presence of:
- [ ] `dataset_description.json` — required
- [ ] `participants.tsv` — required
- [ ] `participants.json` — recommended
- [ ] `README` — recommended
- [ ] `CHANGES` — recommended

Read `dataset_description.json` and check required fields:
- `Name` present
- `BIDSVersion` present and matches format "X.Y.Z"
- `Authors` present (recommended)
- `License` present (recommended)

## Step 3: Check Subject Directories

For each `sub-*` directory found:

### Directory structure
- Does it follow: `sub-{label}/[ses-{label}/]{modality}/`?
- Modality folders: `eeg/`, `ieeg/`, `func/`, `anat/`, `fmap/`, `beh/`

### File naming
For each data file, check:
- Correct entity order: `sub → ses → task → acq → run → suffix.ext`
- No spaces or special characters in filenames
- Consistent label usage across subjects

### Sidecar files
For each data file (`.fif`, `.bdf`, `.edf`, `.nii.gz`), check:
- Matching `.json` sidecar exists
- JSON contains required fields for modality

**EEG JSON required fields:**
- TaskName, SamplingFrequency, PowerLineFrequency, EEGReference

**fMRI JSON required fields:**
- TaskName, RepetitionTime, MagneticFieldStrength

### Events files
For each task-based recording:
- `_events.tsv` exists alongside data file
- Events file has: `onset`, `duration`, `trial_type` columns
- Onset times are in seconds (numeric)

## Step 4: Check Participants File

Read `participants.tsv`:
- Header row present
- `participant_id` column present
- All participant IDs follow `sub-{label}` format
- All participant IDs match existing `sub-*` directories

## Step 5: Report

Produce a structured BIDS validation report:

```
## BIDS Validation Report

**Dataset**: [Name from dataset_description.json]
**Path**: [path]
**BIDS Version**: [BIDSVersion]
**Date**: [today]

---

### ✅ Passed
- dataset_description.json: present and valid
- participants.tsv: present, N={count} subjects
- ...

### ❌ Errors (must fix)
1. Missing _events.tsv for: sub-03_ses-01_task-oddball_eeg.fif
   Fix: Create sub-03_ses-01_task-oddball_events.tsv with onset, duration, trial_type columns

2. Invalid filename: sub01_eeg.bdf
   Fix: Rename to sub-01_task-{taskname}_eeg.bdf

### ⚠️ Warnings (recommended)
1. Missing participants.json (column descriptions)
2. No README file

---

### Summary
Subjects: {N}
Sessions: {S}
Modalities: {list}
Critical errors: {n}
Warnings: {n}
```

Also recommend running the official BIDS Validator:
```bash
pip install bids-validator
bids-validator {path}
# Or online: https://bids-standard.github.io/bids-validator/
```
