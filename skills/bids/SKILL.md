---
name: bids
description: >
  This skill should be used whenever the user mentions BIDS, Brain Imaging Data Structure,
  BIDS conversion, BIDS validation, BIDS compliance, organizing neuroimaging data,
  dataset_description.json, participants.tsv, bids-validator, pybids, MNE-BIDS, or
  asks how to structure EEG/MEG/fMRI/iEEG/PET/DWI data for sharing or preprocessing.
  Also invoke when the user asks how to name scan files, what sidecar JSON fields are
  needed, how to set up derivatives/, or how to run fMRIPrep/MRIQC on their dataset.
  Invoke proactively during /data, /data-preprocess, and /data-analyze phases whenever
  the dataset structure is relevant to the task at hand.
---

# BIDS — Brain Imaging Data Structure

BIDS is the community-standard way to organize, name, and describe neuroimaging datasets.
It covers MRI/fMRI, EEG, MEG, iEEG, PET, DWI, NIRS, microscopy, motion capture, and MRS.
BIDS compliance unlocks the full ecosystem: bids-validator, fMRIPrep, MRIQC, pybids, MNE-BIDS,
and 100+ BIDS Apps. Over 1500 public datasets on OpenNeuro use it; 3000+ papers cite it.

---

## When to invoke this skill

- User asks how to structure, organize, or convert neuroimaging data
- Dataset has BIDS-like structure and you need to navigate or validate it
- User is setting up a new study and needs to know what files/folders to create
- Running `/data` phase: inventory, validate, or convert to BIDS
- Running `/data-preprocess`: loading BIDS-organized data into MNE or nibabel
- Running `/data-analyze`: querying the dataset with pybids or MNE-BIDS
- User mentions bids-validator errors or compliance issues

---

## BIDS hierarchy at a glance

```
dataset/
├── dataset_description.json   ← required
├── participants.tsv            ← required
├── participants.json           ← recommended
├── README                      ← recommended
├── CHANGES                     ← recommended
├── .bidsignore                 ← optional
├── sub-<label>/
│   ├── [ses-<label>/]          ← optional; omit if single session
│   │   ├── anat/               ← T1w, T2w, FLAIR, ...
│   │   ├── func/               ← BOLD fMRI + events
│   │   ├── dwi/                ← diffusion + bval/bvec
│   │   ├── fmap/               ← field maps
│   │   ├── eeg/                ← EEG + channels + coordsystem
│   │   ├── meg/                ← MEG + channels + coordsystem
│   │   ├── ieeg/               ← iEEG + electrodes + coordsystem
│   │   ├── pet/                ← PET + blood data
│   │   ├── perf/               ← perfusion (ASL)
│   │   ├── nirs/               ← fNIRS
│   │   ├── motion/             ← motion capture
│   │   ├── mrs/                ← MR spectroscopy
│   │   └── beh/                ← behavioral-only data
│   └── scans.tsv               ← optional; lists files + acq_time
├── sourcedata/                 ← raw/pre-BIDS originals (unvalidated)
├── derivatives/                ← pipeline outputs (fMRIPrep, MNE, etc.)
└── code/                       ← analysis scripts
```

---

## Filename entity ordering

Entities appear in this exact order — wrong order fails validation:

```
sub-<label>  [ses-<label>]  [task-<label>]  [acq-<label>]  [ce-<label>]
[rec-<label>]  [dir-<label>]  [run-<index>]  [echo-<index>]  [flip-<index>]
[part-<label>]  [chunk-<index>]  _<suffix>.<extension>
```

**Examples:**
```
sub-01_T1w.nii.gz
sub-01_ses-01_task-rest_bold.nii.gz
sub-01_ses-01_task-faces_run-1_bold.nii.gz
sub-01_task-rest_acq-multiband_bold.json
sub-01_dir-AP_epi.nii.gz
sub-01_ses-01_task-rest_eeg.edf
sub-01_ses-01_task-auditory_meg.fif
```

**Rules:** alphanumeric + hyphens + underscores only; no spaces; each entity once per filename; case-sensitive; suffix always last before extension.

---

## Required top-level files

### dataset_description.json (required)

```json
{
  "Name": "My Study",
  "BIDSVersion": "1.11.1",
  "DatasetType": "raw",
  "License": "CC-BY-4.0",
  "Authors": [{"name": "Jane Doe", "email": "jane@example.com"}],
  "Acknowledgements": "Funded by ...",
  "HowToAcknowledge": "Please cite: ...",
  "Funding": [{"Funder": "NIH", "Grant": "R01DA123456"}],
  "EthicsApprovals": [{"Name": "IRB", "Reference": "IRB00012345"}],
  "ReferencesAndLinks": ["https://doi.org/10.1038/..."]
}
```

For derivatives, add:
```json
{
  "DatasetType": "derivative",
  "GeneratedBy": [{"Name": "fMRIPrep", "Version": "22.1.1",
                   "CodeURL": "https://github.com/nipreps/fmriprep"}],
  "SourceDatasets": [{"URL": "ds004157", "Version": "1.0.0"}]
}
```

### participants.tsv (required)

```tsv
participant_id	age	sex	group	handedness
sub-01	25	M	control	R
sub-02	28	F	patient	L
```

### participants.json (recommended)

```json
{
  "age": {"Description": "Age in years", "Units": "years"},
  "sex": {"Description": "Biological sex", "Levels": {"M": "male", "F": "female"}},
  "group": {"Description": "Group", "Levels": {"control": "Healthy control", "patient": "Patient"}}
}
```

---

## Key metadata rules by modality

| Modality | Required in JSON sidecar |
|----------|--------------------------|
| func BOLD | `TaskName`, `RepetitionTime` |
| EEG | `SamplingFrequency`, `PowerLineFrequency` |
| MEG | `SamplingFrequency` |
| iEEG | `SamplingFrequency`, `PowerLineFrequency` |
| DWI | (needs `.bval` and `.bvec` files, not just JSON) |
| PET | `Manufacturer`, `BodyPart`, `TracerName`, `InjectedRadioactivity` |

For full field lists → `references/metadata.md`

---

## BIDS validation

```bash
# CLI (Node.js)
npm install -g bids-validator
bids-validator /path/to/dataset

# Web tool
# https://bids-standard.github.io/bids-validator/

# Python
pip install bids-validator
python -m bids_validator /path/to/dataset
```

Suppress known non-issues with `.bidsignore`:
```
*_physio.tsv.gz      # custom physio format
sourcedata/          # always excluded
tmp_*/               # temp folders
```

For validator error codes and fixes → `references/tools.md`

---

## Loading BIDS in Python

```python
from bids import BIDSLayout

layout = BIDSLayout('/path/to/dataset')
print(layout.get_subjects())          # ['01', '02', ...]
print(layout.get_tasks())             # ['rest', 'nback']

# Get all BOLD files
bold = layout.get(suffix='bold', extension='nii.gz', return_type='file')

# Get metadata
meta = layout.get_metadata('sub-01_task-rest_bold.nii.gz')
print(meta['RepetitionTime'])
```

For MNE-BIDS (EEG/MEG) → `references/tools.md`
For pybids full API → `references/tools.md`
For complete example datasets → `references/examples.md`

---

## Derivatives

Preprocessed outputs live in `derivatives/<pipeline>/`:
- Use `space-MNI152NLin2009cAsym` entity for normalized images
- Use `res-<label>` for resampled resolution
- `derivatives/` needs its own `dataset_description.json` with `DatasetType: derivative`

Full derivatives structure → `references/structure.md`

---

## BIDS in neuroflow phases

### /data phase
1. Inventory the data directory — identify modalities, subjects, sessions
2. Validate with bids-validator or manual check against this skill
3. Convert if needed: raw → BIDS using `mne_bids.write_raw_bids()` (EEG/MEG) or `dcm2niix` + renaming (MRI)
4. Save `data-inventory.md` to `.neuroflow/data/` noting BIDS compliance status

### /data-preprocess phase
- Load BIDS data: `BIDSLayout` + `layout.get()` or `mne_bids.read_raw_bids()`
- Pull sidecar metadata: sampling rate, task name, events from `events.tsv`
- Save preprocessed outputs to `derivatives/<pipeline>/` with correct `dataset_description.json`

### /data-analyze phase
- Query dataset structure with pybids before loading data
- Match analysis design to BIDS metadata (task labels, run indices, subject groups from `participants.tsv`)
- Store analysis outputs in `derivatives/analysis/` or project `results/`

---

## Reference files in this skill

| File | Contents |
|------|----------|
| `references/structure.md` | Full folder hierarchy per modality, all required/optional files, entity table |
| `references/metadata.md` | JSON sidecar fields for MRI/EEG/MEG/iEEG/PET, events.tsv, scans.tsv |
| `references/tools.md` | bids-validator, pybids, MNE-BIDS, fMRIPrep, MRIQC — install + usage |
| `references/examples.md` | Complete example dataset trees + Python code snippets |

Read the relevant reference file when you need:
- All required/optional files for a specific modality → `structure.md`
- Which JSON fields to put in a sidecar → `metadata.md`
- How to use a specific BIDS tool → `tools.md`
- A full working example to base conversion code on → `examples.md`

---

## Quick troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Validator: "Not a valid BIDS filename" | Entity order wrong or unknown suffix | Check entity order (sub, ses, task, acq, run…); verify suffix against spec |
| Validator: "IntendedFor missing file" | JSON references non-existent image | Check path; must be relative from dataset root |
| Validator: "Missing required file" | `dataset_description.json` or `participants.tsv` absent | Create the file |
| Validator: "JSON_KEY_RECOMMENDED" | Sidecar missing recommended field | Add field or use `.bidsignore` for now |
| pybids: empty layout | Wrong root path or missing `dataset_description.json` | Check path; ensure root-level JSON exists |
| MNE-BIDS: wrong channel types | `channels.tsv` type column incorrect | Fix: EEG, EOG, ECG, EMG, STIM, MISC, etc. |

For more validator error codes → `references/tools.md`
