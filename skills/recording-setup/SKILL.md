---
name: recording-setup
description: Use when planning a neuroscience recording session — what to record, sampling rates, electrode placement, impedance thresholds, file format, channel naming, reference scheme, or data storage structure. Triggers on "how to set up recording", "what sampling rate", "electrode placement", "reference electrode", "impedance check", "how many channels", "recording parameters", or "what to save during EEG/fMRI session".
version: 1.0.0
---

# Recording Setup Guide

## Purpose

Define all recording parameters before a neuroscience data collection session to ensure data quality, reproducibility, and compatibility with downstream analysis pipelines.

## EEG Recording Setup

### Sampling Rate

| Use case | Recommended Fs |
|---|---|
| ERP (P300, N200, MMN) | 500–1000 Hz |
| Oscillatory (alpha, gamma) | 1000–2000 Hz |
| High-frequency (HFO, iEEG) | 2000–10000 Hz |
| BCI / real-time | 250–500 Hz (latency optimized) |

**Rule:** Nyquist ≥ 2× max frequency of interest. Always oversample by ≥ 2×.

### Electrode Placement

- **Standard systems**: 10-20, 10-10, 10-5
- **Common montages**: 32ch, 64ch, 128ch, 256ch
- **Always document**: cap size, gel/saline type, electrode IDs, channel order in the amplifier

### Reference Electrode

| Reference | When to use |
|---|---|
| Linked mastoids (A1+A2) | General ERP, good for laterality studies |
| Cz | Motor studies |
| Average reference | High-density arrays (≥64ch), EEGLAB default |
| Nose tip | Face/emotion studies |
| REST (Reference Electrode Standardization Technique) | Converting between references offline |

**Best practice**: Record with a stable reference, re-reference offline.

### Impedance Thresholds

| System type | Target impedance |
|---|---|
| Active electrodes (g.tec, BioSemi) | < 50 kΩ |
| Passive electrodes (BrainProducts) | < 10 kΩ |
| iEEG | System-dependent |

### Ground Electrode

Separate from reference. Common: AFz, forehead, leg.

### Amplifier Settings

- **High-pass filter (hardware)**: 0.01–0.1 Hz (as low as possible, filter offline)
- **Low-pass filter (hardware)**: ≥ 0.5× Fs (anti-aliasing)
- **Gain**: Check for clipping during setup

---

## Physiological Co-recordings

| Signal | Electrode placement | Sampling rate |
|---|---|---|
| **ECG** | Lead II (right clavicle − left rib) | 500–1000 Hz |
| **EMG** | Bilateral over muscle (e.g., masseter, deltoid) | 1000–2000 Hz |
| **EOG** | Above/below and lateral to eye | Same as EEG |
| **EDA / GSR** | Index + middle finger (non-dominant) | 32–256 Hz |
| **Respiration** | Chest/abdominal belt | 50–200 Hz |

---

## Eye Tracker Setup

- **Calibration**: Always 5- or 9-point before each block; validate afterward
- **Sampling rate**: 250 Hz (standard), 1000–2000 Hz (microsaccades, pupil)
- **Distance from screen**: 60–70 cm; chin rest recommended
- **Send LSL markers**: same events as EEG stimulus markers

---

## fMRI Recording

- **TR (repetition time)**: 2 s (standard), 0.7–1 s (multiband)
- **Field strength**: 3T (standard), 7T (high-res, subcortical)
- **MR-compatible EEG**: Use appropriate cap + balun filters; gradient artifact removal pipeline required
- **Trigger timing**: Scanner TTL pulse → stimulus system → EEG (sub-ms accuracy critical)

---

## File Format & Storage

### Recommended formats

| Modality | Format | Notes |
|---|---|---|
| EEG | `.fif` (MNE), `.bdf` (BioSemi), `.xdf` (LSL) | BIDS-compatible |
| fMRI | `.nii.gz` (NIfTI) | BIDS default |
| Eye tracking | `.edf` (SR Research), `.tsv` (BIDS) | Convert to BIDS |
| Physio | `.tsv.gz` + `.json` sidecar (BIDS) | |

### BIDS Storage Structure

```
project/
├── sub-01/
│   ├── ses-01/
│   │   ├── eeg/
│   │   │   ├── sub-01_ses-01_task-oddball_eeg.fif
│   │   │   └── sub-01_ses-01_task-oddball_eeg.json
│   │   └── func/ (fMRI)
│   └── ses-02/
└── sub-02/
```

### What to always save alongside raw data

- [ ] Electrode positions file (`.elc` or `_electrodes.tsv`)
- [ ] Recording log / experiment notes
- [ ] Participant metadata (age, sex, handedness, exclusion notes)
- [ ] Marker/event file (`.vmrk`, `_events.tsv`)
- [ ] Hardware settings screenshot / export
- [ ] Session start/end timestamps
