---
name: eeg-preprocessing
description: Use when preprocessing EEG or iEEG data — filtering, re-referencing, ICA artifact removal, epoch creation, baseline correction, channel rejection, bad segment marking, or preparing EEG data for analysis. Triggers on "preprocess EEG", "EEG pipeline", "ICA artifacts", "artifact rejection", "epoch EEG", "filter EEG", "re-reference", "bad channels", "MNE preprocessing", "EEGLAB", "ERP preprocessing".
version: 1.0.0
---

# EEG Preprocessing Pipeline

## Purpose

Define a reproducible, standards-compliant EEG preprocessing pipeline using MNE-Python (primary) or EEGLAB. Covers raw data loading through clean epochs ready for analysis.

## Recommended Pipeline (MNE-Python)

```python
import mne
from mne.preprocessing import ICA

# 1. Load raw data
raw = mne.io.read_raw_fif('sub-01_task-oddball_eeg.fif', preload=True)
# Or: mne.io.read_raw_brainvision(), read_raw_edf(), read_raw_bdf()

# 2. Set channel types
raw.set_channel_types({'EOG_L': 'eog', 'EOG_R': 'eog', 'ECG': 'ecg'})

# 3. Set montage (electrode positions)
montage = mne.channels.make_standard_montage('standard_1020')
raw.set_montage(montage)

# 4. High-pass filter (remove slow drifts)
raw.filter(l_freq=1.0, h_freq=None, picks='eeg')

# 5. Notch filter (power line)
raw.notch_filter(freqs=[50, 100])

# 6. Mark bad channels (manual or automatic)
raw.info['bads'] = ['Fp1', 'AF7']   # Visual inspection
# Interpolate later after ICA

# 7. Re-reference
raw.set_eeg_reference('average', projection=True)
raw.apply_proj()

# 8. ICA artifact removal
ica = ICA(n_components=20, method='fastica', random_state=42)
ica.fit(raw, picks='eeg', reject={'eeg': 150e-6})  # Fit on high-pass filtered

# Find components correlated with EOG/ECG
eog_idx, eog_scores = ica.find_bads_eog(raw)
ecg_idx, ecg_scores = ica.find_bads_ecg(raw)
ica.exclude = eog_idx + ecg_idx
ica.apply(raw)

# 9. Interpolate bad channels
raw.interpolate_bads(reset_bads=True)

# 10. Low-pass filter (for ERP)
raw.filter(l_freq=None, h_freq=40.0, picks='eeg')

# 11. Create epochs
events, event_id = mne.events_from_annotations(raw)
epochs = mne.Epochs(
    raw, events, event_id={'standard': 1, 'deviant': 2},
    tmin=-0.2, tmax=0.8,
    baseline=(-0.2, 0),
    reject={'eeg': 100e-6},   # Peak-to-peak threshold
    preload=True
)

# 12. Save
epochs.save('sub-01_task-oddball_epo.fif', overwrite=True)
```

## Filter Parameters Reference

| Use case | High-pass | Low-pass |
|---|---|---|
| ERP (P300, N200, N400) | 0.1–1 Hz | 30–40 Hz |
| Mu/beta oscillations (8–30 Hz) | 1 Hz | 45 Hz |
| Gamma (30–80 Hz) | 1 Hz | 100 Hz |
| Slow cortical potentials | 0.01 Hz | 10 Hz |
| iEEG / HFO | 1 Hz | 500+ Hz |
| BCI real-time | 0.5 Hz | 40 Hz |

## Artifact Types & Solutions

| Artifact | Appearance | Solution |
|---|---|---|
| **Eye blinks** | Large positive at Fp1/Fp2 | ICA (EOG component) |
| **Eye movements** | Slow drift + step | ICA (EOG) |
| **Muscle (EMG)** | High-freq noise, temporal channels | ICA, low-pass ≤45 Hz, epoch rejection |
| **ECG artifact** | Regular QRS in EEG | ICA (ECG component) |
| **50/60 Hz line noise** | Sharp peak in spectrum | Notch filter |
| **Electrode pop** | Large transient spike | Mark bad channel, interpolate |
| **Motion artifact** | Slow drift, movement correlated | Epoch rejection, bad segment marking |

## ICA Best Practices

- Fit ICA on data high-passed at ≥1 Hz (recommended by MNE)
- Use `n_components=0.999` (variance-based) or `n_components=n_channels-1`
- Always visually inspect removed components: `ica.plot_components()`, `ica.plot_properties(raw, picks=eog_idx)`
- Document which components were removed and why
- Never remove more than 3–5 components without strong justification

## Epoch Rejection

```python
# Automatic peak-to-peak rejection
epochs.drop_bad(reject={'eeg': 100e-6, 'eog': 150e-6})

# Check drop log
print(epochs.drop_log)

# Target: keep ≥70% of epochs per condition
print(f"Kept: {len(epochs)}/{len(events)} epochs")
```

## Preprocessing Checklist (per participant)

- [ ] Raw data loaded and channel types set
- [ ] Electrode positions verified (montage match)
- [ ] Power spectrum inspected for gross artifacts
- [ ] Bad channels identified and marked
- [ ] Filters applied (report exact parameters)
- [ ] ICA fitted and artifact components removed (document component IDs)
- [ ] Bad channels interpolated
- [ ] Epochs created with correct time window and baseline
- [ ] Epoch rejection applied (report threshold and % kept)
- [ ] Final epoch count ≥ threshold per condition
- [ ] Preprocessed file saved (BIDS derivatives)

## Reporting (Methods Section)

Template sentence:
> "EEG was preprocessed using MNE-Python (v{version}). Data were high-pass filtered at {hp} Hz and low-pass filtered at {lp} Hz. Independent component analysis (ICA; FastICA, {n} components) was applied to remove ocular and cardiac artifacts. Epochs were extracted from {tmin} to {tmax} s relative to stimulus onset, baseline-corrected using the {baseline} ms pre-stimulus interval, and rejected if peak-to-peak amplitude exceeded {threshold} µV. On average, {pct_kept}% of trials were retained per participant."
