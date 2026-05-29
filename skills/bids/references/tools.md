# BIDS Tools Reference

## bids-validator

### Installation
```bash
# Node.js CLI (recommended)
npm install -g bids-validator

# Python wrapper
pip install bids-validator

# Docker (no install needed)
docker run -ti --rm -v /path/to/dataset:/data:ro \
  bids/validator /data
```

### Usage
```bash
# Basic validation
bids-validator /path/to/dataset

# JSON output (parse errors programmatically)
bids-validator --json /path/to/dataset > validation_results.json

# Ignore specific error codes
bids-validator --ignoreNiftiHeaders /path/to/dataset

# Web tool (no install): https://bids-standard.github.io/bids-validator/
```

### .bids-validator-config.json
Place at dataset root to suppress known non-issues:
```json
{
  "ignore": [
    {"code": "JSON_KEY_RECOMMENDED", "location": "/T1w.json"},
    "EMPTY_FILE",
    {"code": "NOT_INCLUDED", "location": "/sourcedata"}
  ],
  "warning": ["INCONSISTENT_COLUMNS"],
  "error": []
}
```

### Common error codes and fixes

| Code | Meaning | Fix |
|------|---------|-----|
| `NOT_INCLUDED` | File not in BIDS spec | Move to `sourcedata/` or add to `.bidsignore` |
| `MISSING_JSON` | No sidecar JSON for NIfTI | Create `*_<suffix>.json` with required fields |
| `INVALID_JSON` | Malformed JSON sidecar | Validate JSON syntax (jsonlint, Python json.load) |
| `JSON_KEY_RECOMMENDED` | Missing recommended field | Add field or ignore in config |
| `INCONSISTENT_PARAMETERS` | TR differs across subjects | Add per-subject JSON override |
| `EVENTS_COLUMN_ONSET_ZERO` | onset=0 in events.tsv | Only warn; onset=0 is valid |
| `EMPTY_FILE` | Zero-byte file in dataset | Delete or fix the file |
| `FILENAME_COLUMN` | scans.tsv path wrong | Paths must be relative, forward slashes |
| `MISSING_SESSION` | ses entity in filename but no session folder | Add `ses-*` folder |
| `DUPLICATE_NIFTI` | Two NIfTI with same entities | Check for duplicate files |
| `NIFTI_HEADER_UNMATCHED_DIMENSIONS` | Shape in JSON ≠ actual file | Fix JSON or regenerate |
| `ECHO_METADATA_NOT_DEFINED` | Multi-echo without EchoTime | Add `EchoTime` per echo or use echo entity |
| `INTENDED_FOR` | IntendedFor path not found | Use path relative to **subject folder** for old spec, **dataset root** for new spec |
| `CHANNELS_COLUMN_MISSING` | channels.tsv missing required column | Add `name`, `type`, `units` columns |
| `COORDSYSTEM_UNITS` | Unknown coordinate units | Use `m`, `mm`, `cm` |

---

## PyBIDS (pybids)

### Installation
```bash
pip install pybids
```

### Core usage

```python
from bids import BIDSLayout

# Initialize (builds index of all files)
layout = BIDSLayout('/path/to/dataset')

# With derivatives
layout = BIDSLayout('/path/to/dataset', derivatives=True)

# With specific derivatives folder
layout = BIDSLayout('/path/to/dataset',
                    derivatives='/path/to/dataset/derivatives/fmriprep')
```

### Querying files

```python
# All subjects
subs = layout.get_subjects()              # ['01', '02', '03']

# All sessions
sess = layout.get_sessions()              # ['ses-01', 'ses-02']

# All tasks
tasks = layout.get_tasks()               # ['rest', 'nback']

# All BOLD files
bold_files = layout.get(suffix='bold', extension='nii.gz', return_type='file')

# BOLD for specific subject and task
files = layout.get(
    subject='01',
    task='rest',
    suffix='bold',
    extension='nii.gz',
    return_type='file'
)

# T1w files for all subjects
t1_files = layout.get(suffix='T1w', extension='nii.gz', return_type='file')

# EEG files
eeg_files = layout.get(suffix='eeg', return_type='file')

# Get events for a task
events = layout.get(task='rest', suffix='events', extension='tsv',
                    return_type='file')

# Get files by run
run1 = layout.get(run=1, suffix='bold', return_type='file')

# Return as BIDSFile objects (not just paths)
bids_files = layout.get(suffix='bold', extension='nii.gz')
for f in bids_files:
    print(f.filename, f.get_entities())
```

### Accessing metadata

```python
# Get all metadata for a file
meta = layout.get_metadata('/path/to/dataset/sub-01/func/sub-01_task-rest_bold.nii.gz')
print(meta['RepetitionTime'])   # 2.0
print(meta['TaskName'])         # 'rest'

# Parse entities from filename
entities = layout.parse_file_entities('sub-01_ses-01_task-rest_run-1_bold.nii.gz')
# {'subject': '01', 'session': '01', 'task': 'rest', 'run': 1, 'suffix': 'bold'}

# Get participants dataframe
participants = layout.get_collections(level='dataset')[0].to_df()
```

### Loading data

```python
import pandas as pd
import nibabel as nib

# Read NIfTI
img = nib.load(layout.get(subject='01', task='rest', suffix='bold')[0].path)
data = img.get_fdata()   # shape: (x, y, z, t)
tr = meta['RepetitionTime']

# Read events
events_file = layout.get(subject='01', task='rest', suffix='events')[0]
events_df = pd.read_csv(events_file.path, sep='\t')

# Read participants
parts_df = pd.read_csv(f"{layout.root}/participants.tsv", sep='\t')
```

---

## MNE-BIDS

### Installation
```bash
pip install mne-bids
# Requires MNE-Python: pip install mne
```

### Reading BIDS EEG/MEG data

```python
from mne_bids import BIDSPath, read_raw_bids

# Construct BIDS path
bids_path = BIDSPath(
    subject='01',
    session='01',       # omit if no sessions
    task='rest',
    run='1',            # omit if no runs
    datatype='eeg',     # or 'meg', 'ieeg'
    root='/path/to/dataset'
)

# Read raw data
raw = read_raw_bids(bids_path=bids_path)
print(raw.info['sfreq'])      # sampling rate
print(raw.ch_names)            # channel names
print(raw.info['nchan'])       # channel count

# Get events from events.tsv
from mne_bids import get_entity_vals
events, event_id = mne.events_from_annotations(raw)
```

### Writing BIDS EEG/MEG data

```python
from mne_bids import write_raw_bids, BIDSPath
import mne

# Load raw data from original format
raw = mne.io.read_raw_brainvision('sub-01_task-rest.vhdr', preload=False)

# Define BIDS path
bids_path = BIDSPath(
    subject='01',
    task='rest',
    datatype='eeg',
    root='/path/to/output/bids'
)

# Write to BIDS
write_raw_bids(
    raw,
    bids_path=bids_path,
    events=events,          # optional; MNE events array
    event_id=event_id,      # optional; dict mapping event names to codes
    overwrite=True,
    verbose=True
)
```

### Conversion pipeline example (BrainVision → BIDS EEG)

```python
from pathlib import Path
import mne
from mne_bids import write_raw_bids, BIDSPath, make_dataset_description

bids_root = Path('/path/to/bids_output')
bids_root.mkdir(exist_ok=True)

# Create dataset_description.json
make_dataset_description(
    path=bids_root,
    name='My EEG Study',
    bids_version='1.11.1',
    dataset_type='raw',
    license='CC-BY-4.0',
    authors=['Jane Doe', 'John Smith'],
    overwrite=True
)

subjects = ['01', '02', '03']
for sub in subjects:
    raw = mne.io.read_raw_brainvision(
        f'/raw_data/sub-{sub}_task-rest.vhdr', preload=False
    )
    # Set channel types if not auto-detected
    raw.set_channel_types({'EOG1': 'eog', 'EOG2': 'eog', 'ECG': 'ecg'})
    # Set montage
    raw.set_montage('standard_1020')

    bids_path = BIDSPath(
        subject=sub, task='rest', datatype='eeg', root=bids_root
    )
    write_raw_bids(raw, bids_path=bids_path, overwrite=True)
```

### Useful MNE-BIDS utilities

```python
from mne_bids import (
    get_entity_vals,     # list subjects/sessions/tasks
    inspect_dataset,     # interactive QC
    mark_channels,       # mark bad channels in channels.tsv
    get_anat_landmarks,  # get fiducials
    update_sidecar_json  # update metadata after writing
)

# List all subjects in dataset
subs = get_entity_vals('/path/to/bids', 'subject')

# Update a sidecar JSON field
update_sidecar_json(bids_path, {'PowerLineFrequency': 50})
```

---

## fMRIPrep

### Purpose
Robust, minimal preprocessing pipeline for fMRI data. Takes raw BIDS dataset, outputs preprocessed data in `derivatives/fmriprep/`.

### Installation
```bash
# pip (requires FreeSurfer license)
pip install fmriprep

# Docker (recommended)
docker pull nipreps/fmriprep:latest

# Singularity (HPC)
singularity pull docker://nipreps/fmriprep:22.1.1
```

### Usage
```bash
# Basic run
fmriprep /path/to/bids /path/to/bids/derivatives participant \
  --participant-label 01 02 03 \
  --fs-license-file /path/to/license.txt \
  --output-spaces MNI152NLin2009cAsym:res-2 T1w \
  --skip-bids-validation \
  --nprocs 8 --mem-mb 32000

# Docker
docker run --rm \
  -v /path/to/bids:/data:ro \
  -v /path/to/output:/out \
  -v /path/to/license.txt:/opt/freesurfer/license.txt:ro \
  nipreps/fmriprep:22.1.1 \
  /data /out participant \
  --participant-label 01 \
  --output-spaces MNI152NLin2009cAsym:res-2
```

### Key outputs
```
derivatives/fmriprep/
├── dataset_description.json
├── sub-01/
│   ├── anat/
│   │   ├── sub-01_space-MNI152NLin2009cAsym_res-2_T1w.nii.gz
│   │   ├── sub-01_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz
│   │   └── sub-01_space-T1w_desc-aparcaseg_dseg.nii.gz
│   └── func/
│       ├── sub-01_task-rest_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz
│       ├── sub-01_task-rest_desc-confounds_timeseries.tsv   ← motion + noise regressors
│       └── sub-01_task-rest_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.json
└── sub-01.html   ← visual QC report
```

### Loading fMRIPrep output

```python
import pandas as pd
import nibabel as nib
from bids import BIDSLayout

layout = BIDSLayout('/path/to/bids', derivatives=True)

# Get preprocessed BOLD
bold = layout.get(
    subject='01', task='rest',
    space='MNI152NLin2009cAsym', res='2',
    desc='preproc', suffix='bold', extension='nii.gz'
)[0]

# Get confounds
confounds_file = layout.get(
    subject='01', task='rest',
    desc='confounds', suffix='timeseries', extension='tsv'
)[0]
confounds = pd.read_csv(confounds_file.path, sep='\t')

# Useful confound columns for denoising
motion_cols = [c for c in confounds.columns if 'motion' in c.lower()]
csf_wm_cols = ['csf', 'white_matter', 'global_signal']
```

---

## MRIQC

### Purpose
Automated quality assessment for anatomical and functional MRI. Produces visual reports and machine-readable IQMs (Image Quality Metrics).

### Installation
```bash
pip install mriqc
# Docker:
docker pull nipreps/mriqc:latest
```

### Usage
```bash
mriqc /path/to/bids /path/to/output participant \
  --participant-label 01 02 \
  --nprocs 4 \
  --no-sub

# Group-level report after all participants
mriqc /path/to/bids /path/to/output group
```

### Key IQMs (Image Quality Metrics)
- **SNR** — signal-to-noise ratio
- **CNR** — contrast-to-noise ratio  
- **FWHM** — smoothness estimate
- **EFC** — entropy focus criterion (ghosting)
- **FBER** — foreground-to-background energy ratio
- **fd_mean**, **fd_perc** — framewise displacement (fMRI motion)
- **dvars_std** — DVARS (temporal signal variation)
- **gsr_x/y** — ghost-to-signal ratio (fMRI ghosting)

---

## dcm2niix (DICOM → NIfTI)

### Installation
```bash
# Conda
conda install -c conda-forge dcm2niix

# pip
pip install dcm2niix
```

### Usage
```bash
# Convert DICOM folder to NIfTI + JSON
dcm2niix -f "sub-%n_task-%d_%p" -o /output /path/to/dicom

# Compress output
dcm2niix -z y -f "sub-%n_%p" -o /output /path/to/dicom
```

The `-f` format string generates BIDS-compatible filenames.
Still requires manual review of entity order and suffix correctness.

---

## HeuDiConv (DICOM → BIDS)

### Purpose
Converts DICOM to BIDS format using heuristic rules you define.

### Installation
```bash
pip install heudiconv
```

### Basic workflow
```bash
# Step 1: dry run to see what sequences exist
heudiconv -d /data/{subject}/*.dcm -o /output -f convertall \
  -s sub-01 -ss 1 -c none --overwrite

# Step 2: write heuristic file (see heudiconv docs for format)
# Step 3: convert
heudiconv -d /data/{subject}/*.dcm -o /output \
  -f /path/to/heuristic.py -s sub-01 -c dcm2niix -b --overwrite
```
