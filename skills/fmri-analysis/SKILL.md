---
name: fmri-analysis
description: Use when analyzing fMRI data — GLM first/second level, contrast maps, ROI analysis, resting-state connectivity, fMRIPrep preprocessing, MRIQC quality check, or interpreting BOLD signals. Triggers on "fMRI analysis", "GLM fMRI", "BOLD signal", "first level model", "contrast map", "ROI analysis", "fMRIPrep", "resting state fMRI", "functional connectivity fMRI", "SPM", "FSL", "nilearn", "HRF".
version: 1.0.0
---

# fMRI Data Analysis

## Purpose

Guide fMRI analysis from preprocessed data through first-level GLM, second-level group analysis, and connectivity, using Python (nilearn) and standard pipelines (fMRIPrep, SPM, FSL).

## Pipeline Overview

```
Raw DICOM/NIfTI
    ↓ MRIQC (quality control)
    ↓ fMRIPrep (preprocessing)
Preprocessed NIfTI
    ↓ First-level GLM (per subject)
    ↓ Contrast maps (per subject)
    ↓ Second-level GLM (group)
Statistical maps + clusters
    ↓ Permutation / FWE / FDR correction
Publication figures
```

---

## 1. Quality Control with MRIQC

```bash
# Run MRIQC (Docker/Singularity)
docker run -it --rm \
  -v /data/bids:/data:ro \
  -v /output/mriqc:/out \
  nipreps/mriqc:latest /data /out participant \
  --participant-label sub-01 sub-02 \
  --nprocs 8

# Key IQMs (image quality metrics) to check:
# tSNR (temporal SNR) > 40 recommended
# FD (framewise displacement) < 0.5 mm mean
# DVARS (signal variation) spikes
```

---

## 2. Preprocessing with fMRIPrep

```bash
docker run -it --rm \
  -v /data/bids:/data:ro \
  -v /output/fmriprep:/out \
  -v /freesurfer_license:/license \
  nipreps/fmriprep:latest /data /out participant \
  --participant-label sub-01 \
  --fs-license-file /license/license.txt \
  --output-spaces MNI152NLin2009cAsym:res-2 \
  --nprocs 8 --mem 24000
```

Outputs: confound regressors, brain mask, preprocessed BOLD in MNI space.

---

## 3. First-Level GLM (nilearn)

```python
import numpy as np
import pandas as pd
from nilearn.glm.first_level import FirstLevelModel, make_first_level_design_matrix
from nilearn import plotting

# Load preprocessed image
fmri_img = 'derivatives/fmriprep/sub-01/ses-01/func/sub-01_ses-01_task-oddball_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz'

# Load events
events = pd.read_csv('sub-01_ses-01_task-oddball_events.tsv', sep='\t')
# Required columns: onset, duration, trial_type

# Load confounds
confounds = pd.read_csv('..._desc-confounds_timeseries.tsv', sep='\t')
conf_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z',
             'framewise_displacement', 'white_matter', 'csf']
confounds_filtered = confounds[conf_cols].fillna(0)

# Fit GLM
glm = FirstLevelModel(
    t_r=2.0,             # TR in seconds
    hrf_model='spm',     # HRF model
    drift_model='cosine',
    high_pass=0.01,
    noise_model='ar1',
    standardize=False,
    n_jobs=-1,
)
glm.fit(fmri_img, events=events, confounds=confounds_filtered)

# Compute contrast
contrast_map = glm.compute_contrast('deviant - standard', stat_type='t')
plotting.plot_stat_map(contrast_map, threshold=3.0, title='Deviant > Standard')
```

---

## 4. Second-Level GLM (Group)

```python
from nilearn.glm.second_level import SecondLevelModel
import nibabel as nib

# Collect first-level contrast maps across subjects
contrast_imgs = [
    f'derivatives/first_level/sub-{i:02d}_contrast-deviantVsStandard.nii.gz'
    for i in range(1, 21)
]

# One-sample t-test against zero
second_model = SecondLevelModel(n_jobs=-1)
second_model.fit(contrast_imgs)
z_map = second_model.compute_contrast(output_type='z_score')

# Threshold and cluster
from nilearn.reporting import get_clusters_table
from nilearn.image import threshold_img

# FWE via Gaussian random field (SPM-style): threshold at z > 3.1 (p<0.001 unc) + k>20
thresh_map = threshold_img(z_map, threshold=3.1)
table = get_clusters_table(thresh_map, stat_threshold=3.1, cluster_extent_threshold=20)
print(table)
```

---

## 5. ROI Analysis

```python
from nilearn.maskers import NiftiLabelsMasker, NiftiSpheresMasker

# Atlas-based ROI (Schaefer, AAL, Brodmann)
from nilearn import datasets
atlas = datasets.fetch_atlas_schaefer_2018(n_rois=200)
masker = NiftiLabelsMasker(atlas['maps'], labels=atlas['labels'])
roi_timeseries = masker.fit_transform(fmri_img)

# Sphere ROI (coordinates-based)
coords = [(−46, −68, 32)]  # e.g., peak voxel from prior study
sphere_masker = NiftiSpheresMasker(coords, radius=8)
roi_ts = sphere_masker.fit_transform(fmri_img)
```

---

## 6. Resting-State Connectivity

```python
from nilearn.connectome import ConnectivityMeasure
from nilearn.maskers import NiftiLabelsMasker

# Extract ROI time series
masker = NiftiLabelsMasker(atlas.maps, standardize=True)
time_series = masker.fit_transform(rest_img, confounds=confounds_filtered)

# Functional connectivity matrix
correlation_measure = ConnectivityMeasure(kind='correlation')
conn_matrix = correlation_measure.fit_transform([time_series])[0]

# Seed-based correlation
seed_masker = NiftiSpheresMasker([(−1, 51, 27)], radius=8)  # mPFC seed
seed_ts = seed_masker.fit_transform(rest_img)

from nilearn.image import math_img
from nilearn.glm.first_level import compute_regressor

# Correlate seed with whole brain
```

---

## HRF and Temporal Resolution Notes

- **TR = 1–2 s**: standard event-related; convolve with canonical HRF (~6 s peak)
- **TR < 1 s** (multiband): model HRF more precisely; use FIR model for transient events
- **Stimulus duration < TR**: model as impulse (delta function); HRF captures hemodynamics
- **Block design**: model entire block duration; high SNR
