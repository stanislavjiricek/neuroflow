---
name: bids-structure
description: Use when organizing neuroscience data in BIDS (Brain Imaging Data Structure) format, naming files according to BIDS conventions, creating required JSON sidecars, setting up a BIDS dataset, validating BIDS compliance, or understanding BIDS entities (sub, ses, task, run, acq). Triggers on "BIDS structure", "BIDS naming", "organize data", "BIDS validator", "dataset_description.json", "participants.tsv", "bids compliance", or "how to structure EEG/fMRI data".
version: 1.0.0
---

# BIDS Data Structure

## Purpose

Organize neuroscience datasets according to the Brain Imaging Data Structure (BIDS) specification to ensure reproducibility, shareability, and compatibility with analysis tools (MNE-BIDS, fMRIPrep, MRIQC, etc.).

## Core BIDS Principles

1. **Entities** describe file content via key-value pairs in the filename
2. **Sidecars** (`.json`) store metadata for each data file
3. **Inheritance**: settings in parent directories apply to subdirectories unless overridden
4. **Required files** at the root level must always be present

## File Naming Convention

```
sub-<label>[_ses-<label>][_task-<label>][_run-<index>][_acq-<label>]_<suffix>.<ext>
```

**Examples:**
```
sub-01_ses-01_task-oddball_eeg.fif
sub-01_ses-01_task-rest_run-1_bold.nii.gz
sub-02_task-nback_eyetrack.tsv
sub-03_ses-02_acq-highres_T1w.nii.gz
```

## Modality Suffixes

| Modality | Suffix | Extensions |
|---|---|---|
| EEG | `_eeg` | `.fif`, `.bdf`, `.edf`, `.set` |
| iEEG | `_ieeg` | `.fif`, `.edf`, `.nwb` |
| fMRI (BOLD) | `_bold` | `.nii.gz` |
| Anatomical MRI | `_T1w`, `_T2w` | `.nii.gz` |
| Eye tracking | `_eyetrack` | `.tsv.gz` |
| Physiology | `_physio` | `.tsv.gz` |
| Events | `_events` | `.tsv` |
| Channels | `_channels` | `.tsv` |
| Electrodes | `_electrodes` | `.tsv` |

## Required Root Files

```
dataset/
├── dataset_description.json    ← Required
├── participants.tsv            ← Required
├── participants.json           ← Recommended (column descriptions)
├── README                      ← Recommended
└── CHANGES                     ← Recommended
```

### `dataset_description.json`
```json
{
  "Name": "My EEG Study",
  "BIDSVersion": "1.9.0",
  "License": "CC0",
  "Authors": ["Jane Doe", "John Smith"],
  "Acknowledgements": "Funded by ...",
  "ReferencesAndLinks": ["https://doi.org/..."]
}
```

### `participants.tsv`
```tsv
participant_id	age	sex	handedness
sub-01	25	M	R
sub-02	31	F	R
```

## Directory Structure

### EEG Dataset
```
dataset/
├── dataset_description.json
├── participants.tsv
├── sub-01/
│   └── ses-01/
│       └── eeg/
│           ├── sub-01_ses-01_task-oddball_eeg.fif
│           ├── sub-01_ses-01_task-oddball_eeg.json
│           ├── sub-01_ses-01_task-oddball_channels.tsv
│           ├── sub-01_ses-01_task-oddball_events.tsv
│           └── sub-01_ses-01_electrodes.tsv
└── task-oddball_eeg.json        ← Inherited by all runs
```

### EEG JSON Sidecar (required fields)
```json
{
  "TaskName": "Oddball",
  "SamplingFrequency": 1000,
  "PowerLineFrequency": 50,
  "SoftwareFilters": "n/a",
  "EEGReference": "linked mastoids",
  "EEGGround": "AFz",
  "Manufacturer": "Brain Products",
  "ManufacturersModelName": "actiCHamp",
  "EEGChannelCount": 64,
  "EOGChannelCount": 2,
  "ECGChannelCount": 1,
  "MiscChannelCount": 0
}
```

## Derivatives

Preprocessed data goes in `derivatives/`:
```
derivatives/
└── mne-bids-pipeline/
    └── sub-01/
        └── ses-01/
            └── eeg/
                └── sub-01_ses-01_task-oddball_proc-clean_eeg.fif
```

## Validation

Use the official BIDS Validator:
```bash
pip install bids-validator
bids-validator /path/to/dataset
```

Or online: https://bids-standard.github.io/bids-validator/

## Common Mistakes

- Missing `TaskName` in EEG sidecar → validator error
- Wrong separator (use `_` between entities, `.` before extension only)
- Putting derived files in raw BIDS root (use `derivatives/`)
- Missing `_events.tsv` for task-based recordings
- Not matching participant IDs exactly between `participants.tsv` and folder names
