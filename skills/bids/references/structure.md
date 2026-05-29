# BIDS Structure Reference

## Complete folder hierarchy

```
dataset/
├── dataset_description.json            ← REQUIRED
├── participants.tsv                     ← REQUIRED
├── participants.json                    ← recommended
├── README                               ← recommended (plain text or markdown)
├── CHANGES                              ← recommended (version history)
├── .bidsignore                          ← optional (like .gitignore)
│
├── sub-<label>/                         ← one per participant
│   ├── scans.tsv                        ← optional; lists files + timestamps
│   ├── scans.json                       ← optional; column descriptions
│   │
│   ├── [ses-<label>/]                   ← optional; omit for single-session
│   │   │
│   │   ├── anat/                        ← anatomical MRI
│   │   │   ├── sub-XX_T1w.nii.gz
│   │   │   ├── sub-XX_T1w.json
│   │   │   ├── sub-XX_T2w.nii.gz
│   │   │   ├── sub-XX_T2w.json
│   │   │   ├── sub-XX_FLAIR.nii.gz
│   │   │   ├── sub-XX_FLAIR.json
│   │   │   ├── sub-XX_T2star.nii.gz
│   │   │   ├── sub-XX_PD.nii.gz
│   │   │   ├── sub-XX_PDw.nii.gz
│   │   │   ├── sub-XX_PDT2.nii.gz
│   │   │   ├── sub-XX_inplaneT1.nii.gz
│   │   │   ├── sub-XX_inplaneT2.nii.gz
│   │   │   ├── sub-XX_angio.nii.gz
│   │   │   └── sub-XX_defacemask.nii.gz
│   │   │
│   │   ├── func/                        ← functional MRI
│   │   │   ├── sub-XX_task-<label>_bold.nii.gz
│   │   │   ├── sub-XX_task-<label>_bold.json        ← REQUIRED (TaskName, TR)
│   │   │   ├── sub-XX_task-<label>_events.tsv       ← highly recommended
│   │   │   ├── sub-XX_task-<label>_events.json
│   │   │   ├── sub-XX_task-<label>_physio.tsv.gz    ← optional
│   │   │   ├── sub-XX_task-<label>_physio.json
│   │   │   ├── sub-XX_task-<label>_stim.tsv.gz      ← optional
│   │   │   └── sub-XX_task-<label>_stim.json
│   │   │
│   │   ├── dwi/                         ← diffusion MRI
│   │   │   ├── sub-XX_dwi.nii.gz        ← REQUIRED
│   │   │   ├── sub-XX_dwi.json          ← REQUIRED
│   │   │   ├── sub-XX_dwi.bval          ← REQUIRED (b-values, space-separated)
│   │   │   ├── sub-XX_dwi.bvec          ← REQUIRED (gradient directions, 3 rows)
│   │   │   └── sub-XX_dwi.sbref.nii.gz  ← optional single-band reference
│   │   │
│   │   ├── fmap/                        ← field maps
│   │   │   ├── sub-XX_dir-AP_epi.nii.gz          ← EPI field map (for DWI/func)
│   │   │   ├── sub-XX_dir-AP_epi.json
│   │   │   ├── sub-XX_magnitude1.nii.gz           ← two-echo magnitude
│   │   │   ├── sub-XX_magnitude2.nii.gz
│   │   │   ├── sub-XX_phasediff.nii.gz
│   │   │   ├── sub-XX_phasediff.json              ← needs EchoTime1, EchoTime2
│   │   │   ├── sub-XX_phase1.nii.gz               ← OR separate phase images
│   │   │   ├── sub-XX_phase2.nii.gz
│   │   │   ├── sub-XX_fieldmap.nii.gz             ← direct fieldmap (Hz)
│   │   │   └── sub-XX_fieldmap.json
│   │   │
│   │   ├── perf/                        ← perfusion (ASL)
│   │   │   ├── sub-XX_asl.nii.gz
│   │   │   ├── sub-XX_asl.json          ← needs ArterialSpinLabelingType, etc.
│   │   │   ├── sub-XX_aslcontext.tsv    ← REQUIRED: volume type per frame
│   │   │   └── sub-XX_m0scan.nii.gz    ← optional M0 image
│   │   │
│   │   ├── eeg/                         ← electroencephalography
│   │   │   ├── sub-XX_task-<label>_eeg.edf         ← or .set/.fif/.vhdr+.vmrk+.eeg
│   │   │   ├── sub-XX_task-<label>_eeg.json        ← REQUIRED
│   │   │   ├── sub-XX_task-<label>_channels.tsv    ← REQUIRED
│   │   │   ├── sub-XX_task-<label>_channels.json
│   │   │   ├── sub-XX_task-<label>_events.tsv      ← recommended
│   │   │   ├── sub-XX_task-<label>_events.json
│   │   │   ├── sub-XX_task-<label>_coordsystem.json ← recommended
│   │   │   └── sub-XX_electrodes.tsv               ← if electrode positions known
│   │   │
│   │   ├── meg/                         ← magnetoencephalography
│   │   │   ├── sub-XX_task-<label>_meg.fif         ← or .ds/.raw.fif/etc.
│   │   │   ├── sub-XX_task-<label>_meg.json        ← REQUIRED
│   │   │   ├── sub-XX_task-<label>_channels.tsv    ← REQUIRED
│   │   │   ├── sub-XX_task-<label>_channels.json
│   │   │   ├── sub-XX_task-<label>_events.tsv      ← recommended
│   │   │   ├── sub-XX_task-<label>_coordsystem.json ← REQUIRED (landmark info)
│   │   │   └── sub-XX_headshape.pos                ← optional digitized points
│   │   │
│   │   ├── ieeg/                        ← intracranial EEG (sEEG, ECoG, DBS)
│   │   │   ├── sub-XX_task-<label>_ieeg.edf        ← or .vhdr/etc.
│   │   │   ├── sub-XX_task-<label>_ieeg.json       ← REQUIRED
│   │   │   ├── sub-XX_task-<label>_channels.tsv    ← REQUIRED
│   │   │   ├── sub-XX_task-<label>_events.tsv
│   │   │   ├── sub-XX_electrodes.tsv               ← REQUIRED (electrode coords)
│   │   │   └── sub-XX_coordsystem.json             ← REQUIRED
│   │   │
│   │   ├── pet/                         ← positron emission tomography
│   │   │   ├── sub-XX_pet.nii.gz
│   │   │   ├── sub-XX_pet.json          ← REQUIRED (tracer, scanner, timing)
│   │   │   ├── sub-XX_blood.tsv         ← optional blood data
│   │   │   └── sub-XX_blood.json
│   │   │
│   │   ├── nirs/                        ← near-infrared spectroscopy
│   │   │   ├── sub-XX_task-<label>_nirs.snirf       ← or .nirs
│   │   │   ├── sub-XX_task-<label>_nirs.json
│   │   │   ├── sub-XX_task-<label>_channels.tsv
│   │   │   ├── sub-XX_task-<label>_events.tsv
│   │   │   ├── sub-XX_optodes.tsv
│   │   │   └── sub-XX_coordsystem.json
│   │   │
│   │   ├── motion/                      ← motion capture
│   │   │   ├── sub-XX_task-<label>_tracksys-<label>_motion.tsv
│   │   │   ├── sub-XX_task-<label>_tracksys-<label>_motion.json
│   │   │   ├── sub-XX_task-<label>_tracksys-<label>_channels.tsv
│   │   │   └── sub-XX_task-<label>_events.tsv
│   │   │
│   │   ├── mrs/                         ← MR spectroscopy
│   │   │   ├── sub-XX_svs.nii.gz        ← single voxel
│   │   │   ├── sub-XX_svs.json
│   │   │   ├── sub-XX_mrsi.nii.gz       ← spectroscopic imaging
│   │   │   └── sub-XX_mrsi.json
│   │   │
│   │   └── beh/                         ← behavioral data (no imaging)
│   │       ├── sub-XX_task-<label>_events.tsv
│   │       ├── sub-XX_task-<label>_events.json
│   │       └── sub-XX_task-<label>_beh.tsv
│   │
│   └── [ses-02/]                        ← additional sessions same structure
│
├── sourcedata/                          ← pre-conversion originals; not validated
├── derivatives/                         ← pipeline outputs
│   ├── dataset_description.json         ← REQUIRED for derivatives; DatasetType: derivative
│   └── sub-<label>/
│       ├── anat/
│       └── func/
└── code/                                ← analysis scripts, notebooks
```

---

## Entity reference table

| Entity | Key | Type | Example | Notes |
|--------|-----|------|---------|-------|
| Subject | `sub` | required | `sub-01` | First entity; alphanumeric only |
| Session | `ses` | optional | `ses-preop` | Omit if single session |
| Task | `task` | required for func/eeg/meg/ieeg | `task-rest` | Alphanumeric, no hyphens inside label |
| Acquisition | `acq` | optional | `acq-highres` | Differentiates protocols |
| Contrast enhanced | `ce` | optional | `ce-gadolinium` | Contrast agent used |
| Reconstruction | `rec` | optional | `rec-norm` | Reconstruction method |
| Direction | `dir` | optional | `dir-AP` | Phase encoding direction |
| Run | `run` | optional | `run-1` | Indexed from 1 |
| Echo | `echo` | optional | `echo-1` | Multi-echo data |
| Flip | `flip` | optional | `flip-1` | Multi flip angle |
| Part | `part` | optional | `part-mag` | mag, phase, real, imag |
| Chunk | `chunk` | optional | `chunk-1` | Broken-up recordings |
| Space | `space` | derivatives | `space-MNI152NLin2009cAsym` | Coordinate space |
| Resolution | `res` | derivatives | `res-2` | Resampled resolution |
| Density | `den` | derivatives | `den-32k` | Surface density |
| Label | `label` | derivatives | `label-GM` | Tissue/ROI label |
| Hemisphere | `hemi` | surfaces | `hemi-L` | Hemisphere |

---

## Required files per modality summary

| Modality | Minimum required files |
|----------|----------------------|
| **Any** | `dataset_description.json`, `participants.tsv` |
| anat | `*_<suffix>.nii.gz`, `*_<suffix>.json` |
| func | `*_bold.nii.gz`, `*_bold.json` (TaskName + RepetitionTime) |
| dwi | `*_dwi.nii.gz`, `*_dwi.json`, `*_dwi.bval`, `*_dwi.bvec` |
| eeg | `*_eeg.<ext>`, `*_eeg.json`, `*_channels.tsv` |
| meg | `*_meg.<ext>`, `*_meg.json`, `*_channels.tsv`, `*_coordsystem.json` |
| ieeg | `*_ieeg.<ext>`, `*_ieeg.json`, `*_channels.tsv`, `*_electrodes.tsv`, `*_coordsystem.json` |
| pet | `*_pet.nii.gz`, `*_pet.json` |
| nirs | `*_nirs.<ext>`, `*_nirs.json`, `*_channels.tsv`, `*_optodes.tsv`, `*_coordsystem.json` |

---

## Derivatives structure

### Standard naming

Derivatives inherit the raw filename and add new entities:
```
# Raw:
sub-01_task-rest_bold.nii.gz

# Derivative (preprocessed, in MNI space):
derivatives/fmriprep/sub-01/func/sub-01_task-rest_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz

# Derivative (brain mask):
derivatives/fmriprep/sub-01/anat/sub-01_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz
```

### Common space labels

| Space | Description |
|-------|-------------|
| `T1w` | Native subject anatomical space |
| `MNI152NLin2009cAsym` | MNI 2009c (asymmetric) — most common for fMRI |
| `MNI152NLin6Asym` | MNI FSL template |
| `fsaverage` | FreeSurfer average surface |
| `fsnative` | Individual FreeSurfer surface |
| `ACPC` | AC-PC aligned (common for iEEG) |
| `Talairach` | Talairach space (legacy) |
| `scannerNative` | Scanner native space |

### Common desc labels

| Label | Meaning |
|-------|---------|
| `preproc` | Preprocessed |
| `brain` | Brain-extracted |
| `smoothed` | Spatially smoothed |
| `confounds` | Confound regressors |
| `carpetplot` | QC carpet plot |
| `boldref` | BOLD reference image |
| `aparcaseg` | Aparc+aseg parcellation |

### derivatives/dataset_description.json

```json
{
  "Name": "My Study — fMRIPrep 22.1.1",
  "BIDSVersion": "1.11.1",
  "DatasetType": "derivative",
  "GeneratedBy": [
    {
      "Name": "fMRIPrep",
      "Version": "22.1.1",
      "CodeURL": "https://github.com/nipreps/fmriprep",
      "Container": {"Type": "docker", "Tag": "nipreps/fmriprep:22.1.1"}
    }
  ],
  "SourceDatasets": [{"URL": "../", "Version": "1.0.0"}]
}
```

---

## Accepted file formats per modality

| Modality | Accepted formats |
|----------|-----------------|
| MRI (anat/func/dwi) | `.nii`, `.nii.gz` |
| EEG | `.edf`, `.bdf`, `.set` (+.fdt), `.vhdr` (+.vmrk+.eeg), `.fif`, `.cnt`, `.mff` |
| MEG | `.fif`, `.ds`, `.raw.fif`, `.sqd`, `.con`, `.kdf`, `.txt`, `.mef` |
| iEEG | `.edf`, `.vhdr` (+.vmrk+.eeg), `.nwb`, `.mef` |
| PET | `.nii`, `.nii.gz` |
| NIRS | `.snirf`, `.nirs` |
| Motion | `.tsv` (+ `.json` sidecar) |

---

## Inheritance principle

Sidecar JSON files apply to all matching files in the same directory and below.
More specific filenames override less specific ones:

```
dataset/
├── task-rest_bold.json          ← applies to ALL subjects' rest BOLD
├── sub-01/
│   └── func/
│       ├── sub-01_task-rest_bold.json   ← overrides dataset-level for sub-01 only
│       └── sub-01_task-rest_bold.nii.gz
```

Use dataset-level sidecars for scanner parameters shared across all subjects,
subject-level overrides for deviations (different TR, different bad channels, etc.).
