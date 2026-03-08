---
name: feature-extraction
description: Use when extracting features from EEG, iEEG, or other neural signals — ERP components (amplitude, latency), spectral power (alpha, beta, gamma bands), time-frequency analysis (STFT, wavelets, Morlet), functional connectivity, phase-amplitude coupling, or preparing feature matrices for classification. Triggers on "extract features", "ERP amplitude", "alpha power", "time-frequency analysis", "wavelet transform", "functional connectivity", "coherence", "PLV", "feature matrix for classification", "ERN amplitude", "N200 latency".
version: 1.0.0
---

# Neural Feature Extraction

## Purpose

Extract meaningful, interpretable features from preprocessed neural signals for statistical analysis, visualization, or machine learning classification.

## 1. ERP Features (Time Domain)

```python
import mne
import numpy as np

# Load preprocessed epochs
epochs = mne.read_epochs('sub-01_task-oddball_epo.fif')

# Compute ERP (average across trials)
erp = epochs['deviant'].average()
erp.plot()

# Extract component amplitude at specific electrode and time window
times = epochs.times
eeg_data = epochs['deviant'].get_data(picks='Pz')  # shape: (n_epochs, 1, n_times)

# Mean amplitude in time window (e.g., P300: 300–600 ms)
p300_window = (times >= 0.3) & (times <= 0.6)
p300_amp = eeg_data[:, 0, p300_window].mean(axis=1)  # per epoch

# Peak amplitude and latency
peak_amp = eeg_data[:, 0, p300_window].max(axis=1)
peak_idx = eeg_data[:, 0, p300_window].argmax(axis=1)
peak_lat = times[p300_window][peak_idx]
```

### Standard ERP Components

| Component | Latency | Location | Cognitive function |
|---|---|---|---|
| **P100** | ~100 ms | Oz | Visual processing |
| **N200 (N2)** | 150–250 ms | Fz, FCz | Conflict, inhibition |
| **P300 (P3)** | 300–600 ms | Pz, CPz | Target detection, WM update |
| **N400** | 300–500 ms | Centro-parietal | Semantic processing |
| **LRP** | −200 to 0 ms (resp-locked) | C3/C4 | Motor preparation |
| **ERN (Ne)** | 0–100 ms post-error | FCz, Cz | Error monitoring |
| **MMN** | 100–200 ms | Fz (difference wave) | Auditory deviance detection |

---

## 2. Spectral Power (Frequency Domain)

```python
# Power spectral density (Welch)
psds, freqs = mne.time_frequency.psd_welch(
    epochs, fmin=1, fmax=100, n_fft=2048, n_overlap=512
)

# Band power extraction
def band_power(psds, freqs, fmin, fmax):
    mask = (freqs >= fmin) & (freqs <= fmax)
    return psds[:, :, mask].mean(axis=-1)

alpha = band_power(psds, freqs, 8, 13)    # shape: (n_epochs, n_channels)
beta  = band_power(psds, freqs, 13, 30)
gamma = band_power(psds, freqs, 30, 80)
theta = band_power(psds, freqs, 4, 8)
delta = band_power(psds, freqs, 1, 4)
```

### Standard Frequency Bands

| Band | Range | Associations |
|---|---|---|
| Delta | 1–4 Hz | Sleep, deep anesthesia |
| Theta | 4–8 Hz | Memory encoding, drowsiness |
| Alpha | 8–13 Hz | Relaxation, inhibition, visual suppression |
| Beta | 13–30 Hz | Active cognition, motor, anxiety |
| Low gamma | 30–60 Hz | Binding, local processing |
| High gamma | 60–150 Hz | Neural firing proxy (iEEG) |

---

## 3. Time-Frequency Analysis

```python
# Morlet wavelet transform
freqs_tf = np.logspace(np.log10(4), np.log10(80), 30)
n_cycles = freqs_tf / 2.  # adaptive cycles

power, itc = mne.time_frequency.tfr_morlet(
    epochs, freqs=freqs_tf, n_cycles=n_cycles,
    picks='Pz', return_itc=True, decim=5
)

power.plot(['Pz'], baseline=(-0.2, 0), mode='logratio')
```

### Event-Related (De)Synchronization (ERD/ERS)

```python
# ERD: power decrease during task (e.g., mu/beta during motor)
# ERS: power increase
baseline = (-0.5, -0.1)
power.apply_baseline(baseline, mode='percent')  # % change from baseline
```

---

## 4. Functional Connectivity

```python
# Phase Locking Value (PLV) – phase synchrony
from mne.connectivity import spectral_connectivity_epochs

con = spectral_connectivity_epochs(
    epochs, method='plv',
    fmin=8, fmax=13,  # alpha band
    faverage=True
)
# con.get_data() → connectivity matrix (n_channels × n_channels)

# Coherence
con_coh = spectral_connectivity_epochs(epochs, method='coh', fmin=8, fmax=13, faverage=True)

# Graph metrics (optional, via networkx)
import networkx as nx
adj = con.get_data(output='dense')[..., 0]
G = nx.from_numpy_array(adj)
print(nx.average_clustering(G))
```

---

## 5. Feature Matrix for Classification

```python
# Combine features into sklearn-ready matrix
feature_dict = {}
feature_dict['p300_Pz'] = p300_amp
feature_dict['alpha_Pz'] = alpha[:, picks_idx].mean(axis=1)
feature_dict['beta_Fz'] = beta[:, fz_idx].mean(axis=1)

import pandas as pd
X = pd.DataFrame(feature_dict)   # shape: (n_epochs, n_features)
y = epochs.events[:, 2]           # labels

# Standardize
from sklearn.preprocessing import StandardScaler
X_scaled = StandardScaler().fit_transform(X)
```

---

## Common Mistakes

- Extracting features from un-baselined data → inflated/deflated estimates
- Using overlapping time windows without correction
- Circular feature selection (selecting features that correlate with labels before cross-validation)
- Not reporting exact time windows and frequency bands in Methods section
