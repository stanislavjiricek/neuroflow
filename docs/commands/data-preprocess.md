---
title: /data-preprocess
---

# `/neuroflow:data-preprocess`

**Build and run a preprocessing pipeline on your raw data.**

`/data-preprocess` guides you through creating and running a preprocessing pipeline: from loading raw data to cleaned, epoched, and quality-checked datasets ready for analysis.

---

## When to use it

- After `/data` — you have inventoried and validated your raw data
- You need to filter, re-reference, run ICA, or epoch your EEG data
- You want a documented preprocessing config and QC report

---

## What it does

Claude asks:

1. **What modality?** (EEG, iEEG, fMRI, other)
2. **Where is the data?**
3. **What preprocessing steps are needed?** Or should it apply a standard pipeline for the modality?

---

## Standard EEG pipeline

For EEG data, Claude follows this pipeline using MNE-Python:

| Step | What happens |
|---|---|
| **1. Load** | `mne.io.read_raw_*()` — supports FIF, BrainVision, EDF, EEGLAB |
| **2. Filter** | Bandpass (e.g. 1–40 Hz) + notch (50 Hz or 60 Hz) |
| **3. Re-reference** | Average reference, linked mastoids, or REST |
| **4. Bad channels** | Mark bad channels manually or via automated detection |
| **5. ICA** | Fit ICA, inspect components, remove EOG and ECG artifacts |
| **6. Interpolate** | Interpolate marked bad channels using spherical spline |
| **7. Epoch** | Create epochs around event markers |
| **8. Baseline** | Apply baseline correction |
| **9. Reject** | Reject epochs above amplitude threshold |
| **10. Save** | Save preprocessed epochs as `.fif` |

!!! tip "Custom pipelines"
    Not using EEG? Just tell Claude your modality and what steps you need — it adapts the pipeline to fMRI (nilearn), iEEG, eye tracking, or any other modality.

---

## Example session

```
/neuroflow:data-preprocess
```

```
Claude: I see from your project config that you're working with EEG data
        (BrainProducts, 64 channels). Data is in data/bids/.

        Should I apply the standard EEG preprocessing pipeline?

You: Yes, with these parameters: bandpass 0.5–45 Hz, notch 50 Hz, 
     average reference, ICA for ocular artifacts, epochs -200 to 800ms 
     around stimulus onset.

Claude: Parameters noted. I'll write a preprocessing script:

        scripts/preprocessing/preprocess.py
        ─────────────────────────────────────
        - Load: MNE read_raw_brainvision
        - Filter: 0.5–45 Hz bandpass, 50 Hz notch
        - Reference: average
        - ICA: FastICA, 40 components, EOG detection
        - Epochs: -0.2 to 0.8s, stimulus event codes [1, 2]
        - Rejection: peak-to-peak > 150 µV

        [generates the script and preprocess-config.md]
```

---

## Output

| File | Where | What it contains |
|---|---|---|
| `preprocess.py` (or equivalent) | `scripts/preprocessing/` | The preprocessing pipeline code |
| `preprocess-config.md` | `.neuroflow/data-preprocess/` | All parameters used |
| `preprocess-report.md` | `.neuroflow/data-preprocess/` | QC results: bad channels, ICA components removed, epoch rejection rates, per-subject notes |

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/data/flow.md`, `.neuroflow/data-preprocess/flow.md` |
| Writes | `.neuroflow/data-preprocess/`, `.neuroflow/data-preprocess/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md`, `scripts/preprocessing/` (code output) |

---

## Related commands

- [`/data`](data.md) — get your data organized and converted first
- [`/data-analyze`](data-analyze.md) — the next step after preprocessing
