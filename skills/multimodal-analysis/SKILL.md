---
name: multimodal-analysis
description: Use when analyzing non-EEG neuroscience signals including iEEG (cortical EEG, SEEG, ECoG), ECG (heart rate, HRV), eye tracking (fixations, saccades, pupillometry), EMG, EDA, or when combining multiple physiological signals. Triggers on "iEEG analysis", "ECoG", "SEEG", "HRV analysis", "heart rate variability", "eye tracking analysis", "fixations saccades", "pupillometry", "gaze analysis", "ECG preprocessing", "physiological signal analysis".
version: 1.0.0
---

# Multimodal Physiological Signal Analysis

## 1. iEEG (Cortical EEG / SEEG / ECoG)

### Key Differences from Scalp EEG
- **Spatial resolution**: mm (local field potentials)
- **Frequency range**: DC–1000+ Hz (HFO: 80–500 Hz)
- **No volume conduction**: signals reflect local activity only
- **Clinical population**: typically epilepsy patients

### iEEG Preprocessing (MNE)
```python
import mne

raw = mne.io.read_raw_fif('sub-01_ieeg.fif', preload=True)
raw.set_channel_types({ch: 'seeg' for ch in raw.ch_names})

# Reference: bipolar (adjacent contacts) or common average
raw_bip = mne.set_bipolar_reference(raw, anode=anodes, cathode=cathodes)

# High gamma / HFO extraction
raw_hg = raw.copy().filter(70, 150)  # High gamma band
raw_hfo = raw.copy().filter(80, 500)  # HFO range
```

### High-Frequency Oscillations (HFO)
```python
# Envelope of high-gamma as proxy for neural firing rate
from scipy.signal import hilbert
import numpy as np

data_hg = raw_hg.get_data(picks='seeg')
analytic_signal = hilbert(data_hg, axis=1)
envelope = np.abs(analytic_signal)

# Z-score normalize per channel
z_envelope = (envelope - envelope.mean(axis=1, keepdims=True)) / envelope.std(axis=1, keepdims=True)
```

---

## 2. ECG / Heart Rate / HRV Analysis

### Loading and R-peak Detection
```python
import mne
import neurokit2 as nk  # pip install neurokit2

# Load ECG
ecg_data, times = raw['ECG']
ecg_data = ecg_data.squeeze()
fs = raw.info['sfreq']

# Clean and detect R-peaks
ecg_cleaned = nk.ecg_clean(ecg_data, sampling_rate=int(fs))
rpeaks, info = nk.ecg_peaks(ecg_cleaned, sampling_rate=int(fs))
r_times = times[info['ECG_R_Peaks']]
```

### HRV Features
```python
# RR intervals
rr_intervals = np.diff(r_times) * 1000  # in ms

hrv = nk.hrv(info, sampling_rate=int(fs), show=False)

# Key HRV metrics:
# Time domain: RMSSD, SDNN, pNN50
# Frequency domain: LF power (0.04–0.15 Hz), HF power (0.15–0.4 Hz), LF/HF ratio
# Non-linear: SD1, SD2, DFA α1
print(hrv[['HRV_RMSSD', 'HRV_SDNN', 'HRV_LF', 'HRV_HF', 'HRV_LFHF']])
```

### Cardiac Cycle Phase Effects on EEG
```python
# Systole = ~250 ms after R-peak; Diastole = ~600 ms after
systole_times = r_times + 0.250
diastole_times = r_times + 0.600
```

---

## 3. Eye Tracking Analysis

### Loading Data
```python
import pandas as pd
import mne

# From TSV (BIDS eye tracking format)
et_df = pd.read_csv('sub-01_task-oddball_eyetrack.tsv', sep='\t')
# Columns: time, x_gaze, y_gaze, pupil_diameter, blink

# From EDF (SR Research Eyelink)
# Use pyedfread or mne.preprocessing.eyetracking
```

### Fixation & Saccade Detection
```python
import mne

# MNE eye tracking preprocessing
raw_et = mne.preprocessing.eyetracking.read_eyelink('sub-01.asc')
mne.preprocessing.eyetracking.interpolate_blinks(raw_et, buffer=0.05)

# Detect fixations and saccades
fixations = mne.preprocessing.eyetracking.get_fixation_df(raw_et)
saccades = mne.preprocessing.eyetracking.get_saccade_df(raw_et)

# Key fixation features:
# duration (ms), x_mean, y_mean, dispersion
# Key saccade features:
# amplitude (deg), peak_velocity (deg/s), duration (ms)
```

### Pupillometry
```python
# Pupil diameter as cognitive load / arousal proxy
pupil = et_df['pupil_diameter'].values

# 1. Detect and interpolate blinks
blinks = et_df['blink'].astype(bool)
pupil_clean = pupil.copy()
pupil_clean[blinks] = np.nan
# Interpolate NaN with cubic spline
from scipy.interpolate import CubicSpline
valid = ~np.isnan(pupil_clean)
cs = CubicSpline(et_df.index[valid], pupil_clean[valid])
pupil_interp = cs(et_df.index)

# 2. Low-pass filter (< 10 Hz)
from scipy.signal import butter, filtfilt
b, a = butter(2, 10 / (fs/2), btype='low')
pupil_filtered = filtfilt(b, a, pupil_interp)

# 3. Baseline correction (per trial)
pupil_bl = pupil_filtered - pupil_filtered[:int(0.2*fs)].mean()
```

---

## 4. EDA (Skin Conductance)

```python
eda_data = raw['EDA'][0].squeeze()

eda_signals, info = nk.eda_process(eda_data, sampling_rate=int(fs))

# SCR (skin conductance response) features:
# SCR_Peaks, SCR_Amplitude, SCR_RiseTime, SCR_RecoveryTime
# Tonic: SCL (skin conductance level)
```

---

## Multimodal Alignment

When combining modalities recorded simultaneously via LSL:
```python
import pyxdf

streams, header = pyxdf.load_xdf('recording.xdf')

# Align all streams to LSL clock
# Each stream['time_stamps'] is already in the shared LSL clock
eeg_stream = [s for s in streams if s['info']['type'][0] == 'EEG'][0]
marker_stream = [s for s in streams if s['info']['type'][0] == 'Markers'][0]
et_stream = [s for s in streams if s['info']['type'][0] == 'Gaze'][0]

# Interpolate all to common time grid if needed
from scipy.interpolate import interp1d
```
