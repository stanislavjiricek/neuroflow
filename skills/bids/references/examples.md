# BIDS Examples

## Complete MRI/fMRI dataset

```
my_fmri_study/
├── dataset_description.json
├── participants.tsv
├── participants.json
├── README
├── CHANGES
│
├── sub-01/
│   ├── anat/
│   │   ├── sub-01_T1w.nii.gz
│   │   └── sub-01_T1w.json
│   ├── func/
│   │   ├── sub-01_task-rest_bold.nii.gz
│   │   ├── sub-01_task-rest_bold.json
│   │   ├── sub-01_task-rest_events.tsv
│   │   ├── sub-01_task-nback_run-1_bold.nii.gz
│   │   ├── sub-01_task-nback_run-1_bold.json
│   │   ├── sub-01_task-nback_run-1_events.tsv
│   │   ├── sub-01_task-nback_run-2_bold.nii.gz
│   │   ├── sub-01_task-nback_run-2_bold.json
│   │   └── sub-01_task-nback_run-2_events.tsv
│   ├── fmap/
│   │   ├── sub-01_dir-AP_epi.nii.gz
│   │   ├── sub-01_dir-AP_epi.json
│   │   ├── sub-01_dir-PA_epi.nii.gz
│   │   └── sub-01_dir-PA_epi.json
│   └── scans.tsv
│
├── sub-02/
│   └── [same structure]
│
└── derivatives/
    └── fmriprep/
        ├── dataset_description.json
        └── sub-01/
            ├── anat/
            │   ├── sub-01_space-MNI152NLin2009cAsym_res-2_T1w.nii.gz
            │   └── sub-01_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz
            └── func/
                ├── sub-01_task-rest_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz
                ├── sub-01_task-rest_desc-confounds_timeseries.tsv
                ├── sub-01_task-nback_run-1_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz
                └── sub-01_task-nback_run-1_desc-confounds_timeseries.tsv
```

### dataset_description.json
```json
{
  "Name": "Cognitive Control fMRI Study",
  "BIDSVersion": "1.11.1",
  "DatasetType": "raw",
  "License": "CC-BY-4.0",
  "Authors": [{"name": "Jane Doe", "email": "jane@example.com"}],
  "Funding": [{"Funder": "NIH", "Grant": "R01DA123456"}],
  "EthicsApprovals": [{"Name": "IRB", "Reference": "IRB00012345"}]
}
```

### func/sub-01_task-rest_bold.json
```json
{
  "TaskName": "rest",
  "RepetitionTime": 2.0,
  "EchoTime": 0.03,
  "FlipAngle": 90,
  "SliceTiming": [0.0, 0.0625, 0.125, 0.1875, 0.25, 0.3125, 0.375, 0.4375,
                  0.5, 0.5625, 0.625, 0.6875, 0.75, 0.8125, 0.875, 0.9375],
  "PhaseEncodingDirection": "j-",
  "TotalReadoutTime": 0.0474,
  "MagneticFieldStrength": 3.0,
  "Manufacturer": "Siemens",
  "ManufacturersModelName": "Prisma",
  "TaskDescription": "5-minute resting state with eyes open",
  "Instructions": "Please keep your eyes open and fixate on the cross"
}
```

### fmap/sub-01_dir-AP_epi.json
```json
{
  "PhaseEncodingDirection": "j",
  "TotalReadoutTime": 0.0474,
  "IntendedFor": [
    "func/sub-01_task-rest_bold.nii.gz",
    "func/sub-01_task-nback_run-1_bold.nii.gz",
    "func/sub-01_task-nback_run-2_bold.nii.gz"
  ]
}
```

---

## Complete EEG dataset (multi-session)

```
my_eeg_study/
├── dataset_description.json
├── participants.tsv
│
├── sub-01/
│   ├── ses-01/
│   │   └── eeg/
│   │       ├── sub-01_ses-01_task-rest_eeg.edf
│   │       ├── sub-01_ses-01_task-rest_eeg.json
│   │       ├── sub-01_ses-01_task-rest_channels.tsv
│   │       ├── sub-01_ses-01_task-rest_events.tsv
│   │       ├── sub-01_ses-01_task-rest_coordsystem.json
│   │       ├── sub-01_ses-01_task-faces_run-1_eeg.edf
│   │       ├── sub-01_ses-01_task-faces_run-1_eeg.json
│   │       ├── sub-01_ses-01_task-faces_run-1_channels.tsv
│   │       └── sub-01_ses-01_task-faces_run-1_events.tsv
│   └── ses-02/
│       └── eeg/
│           └── [same structure]
└── sub-02/
```

### eeg/sub-01_ses-01_task-rest_eeg.json
```json
{
  "TaskName": "rest",
  "TaskDescription": "5-minute eyes-open resting state",
  "Instructions": "Sit still and look at the fixation cross",
  "SamplingFrequency": 1000,
  "PowerLineFrequency": 50,
  "EEGReference": "FCz",
  "EEGGround": "AFz",
  "EEGChannelCount": 64,
  "EOGChannelCount": 4,
  "ECGChannelCount": 1,
  "EMGChannelCount": 0,
  "MiscChannelCount": 0,
  "TriggerChannelCount": 1,
  "RecordingDuration": 300.0,
  "RecordingType": "continuous",
  "Manufacturer": "Brain Products",
  "ManufacturersModelName": "actiCHamp Plus",
  "CapManufacturer": "EasyCap",
  "EEGPlacementScheme": "10-20"
}
```

### eeg/sub-01_ses-01_task-rest_channels.tsv
```tsv
name	type	units	sampling_frequency	low_cutoff	high_cutoff	reference	status
Fp1	EEG	µV	1000	0.016	250	FCz	good
Fp2	EEG	µV	1000	0.016	250	FCz	good
F3	EEG	µV	1000	0.016	250	FCz	good
...
VEOG	EOG	µV	1000	0.016	250	FCz	good
HEOG	EOG	µV	1000	0.016	250	FCz	good
ECG	ECG	µV	1000	0.016	250	FCz	good
Trigger	STIM	V	1000	n/a	n/a	n/a	good
```

---

## MEG dataset

```
my_meg_study/
├── dataset_description.json
├── participants.tsv
│
└── sub-01/
    └── meg/
        ├── sub-01_task-auditory_meg.fif
        ├── sub-01_task-auditory_meg.json
        ├── sub-01_task-auditory_channels.tsv
        ├── sub-01_task-auditory_events.tsv
        └── sub-01_task-auditory_coordsystem.json
```

### meg/sub-01_task-auditory_meg.json
```json
{
  "TaskName": "auditory",
  "TaskDescription": "Auditory oddball paradigm",
  "SamplingFrequency": 600,
  "PowerLineFrequency": 50,
  "MEGChannelCount": 102,
  "MEGREFChannelCount": 0,
  "EEGChannelCount": 0,
  "EOGChannelCount": 1,
  "ECGChannelCount": 1,
  "RecordingDuration": 600.0,
  "RecordingType": "continuous",
  "Manufacturer": "Elekta",
  "ManufacturersModelName": "Neuromag VectorView",
  "DigitizedLandmarks": true,
  "DigitizedHeadPoints": true
}
```

---

## iEEG dataset

```
my_ieeg_study/
├── dataset_description.json
├── participants.tsv
│
└── sub-01/
    └── ieeg/
        ├── sub-01_task-rest_ieeg.edf
        ├── sub-01_task-rest_ieeg.json
        ├── sub-01_task-rest_channels.tsv
        ├── sub-01_task-rest_events.tsv
        ├── sub-01_space-Talairach_electrodes.tsv
        └── sub-01_space-Talairach_coordsystem.json
```

### ieeg/sub-01_task-rest_ieeg.json
```json
{
  "TaskName": "rest",
  "SamplingFrequency": 30000,
  "PowerLineFrequency": 60,
  "iEEGReference": "intracranial",
  "SEEGChannelCount": 128,
  "ECGChannelCount": 1,
  "RecordingDuration": 3600.0,
  "RecordingType": "continuous",
  "Manufacturer": "Blackrock Neurotech",
  "ManufacturersModelName": "Neuroport"
}
```

### ieeg/sub-01_space-Talairach_electrodes.tsv
```tsv
name	x	y	z	size	hemisphere	type	group
LAH1	-22.3	-8.1	-12.4	1.5	L	seeg	LAH
LAH2	-22.1	-6.2	-11.8	1.5	L	seeg	LAH
LAH3	-21.8	-4.3	-11.2	1.5	L	seeg	LAH
RAH1	22.5	-7.9	-12.1	1.5	R	seeg	RAH
```

---

## Python: full BIDS workflow snippet

```python
"""
End-to-end BIDS workflow: inventory → validate → load → analyze
"""
import subprocess
import pandas as pd
import nibabel as nib
from bids import BIDSLayout
from pathlib import Path

bids_root = Path('/path/to/bids_dataset')

# 1. Validate
result = subprocess.run(
    ['bids-validator', str(bids_root), '--json'],
    capture_output=True, text=True
)
import json
validation = json.loads(result.stdout)
errors = [i for i in validation.get('issues', {}).get('errors', [])]
if errors:
    for e in errors:
        print(f"ERROR {e['key']}: {e['reason']}")
else:
    print("Dataset is BIDS-valid")

# 2. Build layout
layout = BIDSLayout(bids_root, derivatives=True)
print(f"Subjects: {layout.get_subjects()}")
print(f"Tasks: {layout.get_tasks()}")
print(f"Total BOLD files: {len(layout.get(suffix='bold'))}")

# 3. Load participants
participants = pd.read_csv(bids_root / 'participants.tsv', sep='\t')
controls = participants[participants['group'] == 'control']['participant_id'].tolist()
control_subs = [s.replace('sub-', '') for s in controls]

# 4. Load BOLD + confounds for controls
for sub in control_subs:
    bold_files = layout.get(
        subject=sub, task='rest', suffix='bold',
        space='MNI152NLin2009cAsym', desc='preproc', extension='nii.gz'
    )
    if not bold_files:
        print(f"Warning: no preprocessed BOLD for sub-{sub}")
        continue

    bold_img = nib.load(bold_files[0].path)
    meta = layout.get_metadata(bold_files[0].path)
    tr = meta.get('RepetitionTime', 2.0)

    confounds_files = layout.get(
        subject=sub, task='rest', suffix='timeseries',
        desc='confounds', extension='tsv'
    )
    if confounds_files:
        confounds = pd.read_csv(confounds_files[0].path, sep='\t')
        # Select motion + WM + CSF confounds
        motion_params = [c for c in confounds.columns
                         if any(x in c for x in ['trans', 'rot', 'framewise'])]
        noise_params = ['white_matter', 'csf', 'global_signal']
        regressor_cols = [c for c in motion_params + noise_params if c in confounds.columns]
        regressors = confounds[regressor_cols].fillna(0)

    print(f"sub-{sub}: BOLD shape={bold_img.shape}, TR={tr}s, "
          f"confound regressors={len(regressor_cols)}")

# 5. Load EEG with MNE-BIDS
from mne_bids import BIDSPath, read_raw_bids

for sub in layout.get_subjects():
    eeg_files = layout.get(subject=sub, datatype='eeg', suffix='eeg')
    if not eeg_files:
        continue
    f = eeg_files[0]
    entities = f.get_entities()
    bp = BIDSPath(
        subject=entities.get('subject'),
        session=entities.get('session'),
        task=entities.get('task'),
        run=entities.get('run'),
        datatype='eeg',
        root=bids_root
    )
    raw = read_raw_bids(bids_path=bp)
    print(f"sub-{sub}: EEG sfreq={raw.info['sfreq']}Hz, "
          f"n_chan={raw.info['nchan']}, "
          f"duration={raw.times[-1]:.1f}s")
```

---

## Conversion: BrainVision → BIDS EEG

```python
"""
Convert a folder of BrainVision files to BIDS-compliant EEG dataset.
Assumes: /raw_data/sub-01_task-rest.vhdr, sub-02_task-rest.vhdr, ...
"""
from pathlib import Path
import mne
from mne_bids import write_raw_bids, BIDSPath, make_dataset_description

RAW_DIR = Path('/raw_data')
BIDS_DIR = Path('/bids_output')
TASK = 'rest'
MONTAGE = 'standard_1020'
CHANNEL_TYPES = {'VEOG': 'eog', 'HEOG': 'eog', 'ECG': 'ecg', 'Trigger': 'stim'}

BIDS_DIR.mkdir(exist_ok=True)
make_dataset_description(
    path=BIDS_DIR,
    name='Resting State EEG',
    bids_version='1.11.1',
    dataset_type='raw',
    license='CC-BY-4.0',
    overwrite=True
)

for vhdr in sorted(RAW_DIR.glob('sub-*_task-*.vhdr')):
    # Parse subject from filename
    parts = vhdr.stem.split('_')
    sub = next(p.replace('sub-', '') for p in parts if p.startswith('sub-'))
    task = next(p.replace('task-', '') for p in parts if p.startswith('task-'))

    raw = mne.io.read_raw_brainvision(str(vhdr), preload=False, verbose=False)
    raw.set_channel_types({k: v for k, v in CHANNEL_TYPES.items() if k in raw.ch_names})
    try:
        raw.set_montage(MONTAGE, on_missing='warn')
    except Exception:
        pass

    bids_path = BIDSPath(subject=sub, task=task, datatype='eeg', root=BIDS_DIR)
    write_raw_bids(raw, bids_path=bids_path, overwrite=True, verbose=False)
    print(f"Wrote sub-{sub} task-{task}")

print(f"Done. Validate with: bids-validator {BIDS_DIR}")
```

---

## Conversion: DICOM folder → BIDS MRI (using dcm2niix + pybids)

```bash
#!/bin/bash
# Converts DICOM to BIDS-compatible NIfTI+JSON using dcm2niix
# Requires: dcm2niix, manual rename of output to BIDS conventions

DICOM_ROOT="/raw_dicoms"
BIDS_ROOT="/bids_output"
SUBJECT="01"
SESSION="01"

# Convert structural
mkdir -p "$BIDS_ROOT/sub-$SUBJECT/ses-$SESSION/anat"
dcm2niix -z y -f "sub-${SUBJECT}_ses-${SESSION}_T1w" \
  -o "$BIDS_ROOT/sub-$SUBJECT/ses-$SESSION/anat" \
  "$DICOM_ROOT/sub-$SUBJECT/T1"

# Convert functional
mkdir -p "$BIDS_ROOT/sub-$SUBJECT/ses-$SESSION/func"
dcm2niix -z y -f "sub-${SUBJECT}_ses-${SESSION}_task-rest_bold" \
  -o "$BIDS_ROOT/sub-$SUBJECT/ses-$SESSION/func" \
  "$DICOM_ROOT/sub-$SUBJECT/BOLD_rest"

# After conversion, manually review JSONs and add TaskName + RepetitionTime to BOLD JSON
echo "Done — validate with: bids-validator $BIDS_ROOT"
```
