---
name: modality-selection
description: Use when choosing between neuroscience recording modalities (EEG, iEEG, fMRI, eye tracking, ECG, EMG, fNIRS), or when advising which modality best suits a research question. Triggers on "which modality should we use", "EEG vs fMRI", "why EEG not fMRI", "is eye tracking sufficient", "what can we measure with", "modality comparison", or "sensor selection for neuroscience study".
version: 1.0.0
---

# Neuroscience Modality Selection Guide

## Purpose

Help researchers and technical teams select the appropriate recording modality (or combination) for a given research question, based on the required temporal resolution, spatial resolution, ecological validity, and practical constraints.

## Modality Comparison Matrix

| Modality | Temporal res. | Spatial res. | Portability | Cost | Invasiveness |
|---|---|---|---|---|---|
| **Scalp EEG** | ms | cm | High | Low | Non-invasive |
| **iEEG / ECoG** | ms | mm | Low | High | Invasive (surgical) |
| **fMRI** | ~2 s (TR) | mm | None | Very high | Non-invasive |
| **fNIRS** | ~100 ms | cm | High | Medium | Non-invasive |
| **MEG** | ms | cm | None | Very high | Non-invasive |
| **Eye tracking** | ms (250–2000 Hz) | 0.1° visual | High | Low–Med | Non-invasive |
| **ECG / Heart rate** | ms | — | High | Very low | Non-invasive |
| **EMG** | ms | muscle group | High | Low | Non-invasive |

---

## Decision Guide

### Use **Scalp EEG** when:
- Temporal resolution < 10 ms required (ERP, oscillatory dynamics)
- Budget is limited
- Mobile / ecological recording needed
- Studying cognitive ERPs (P300, N200, N400, MMN, LRP…)
- Online / BCI applications
- ⚠️ Limitation: poor spatial resolution, susceptible to muscle/eye artifacts

### Use **iEEG (SEEG / ECoG)** when:
- Sub-mm spatial resolution needed with ms temporal resolution
- Studying local oscillations, high-frequency broadband (HFO)
- Epilepsy patient population (clinical opportunity)
- Single-neuron or laminar dynamics (LFP proxy)
- ⚠️ Limitation: requires neurosurgical patients, invasive, limited coverage

### Use **fMRI** when:
- Spatial localization is primary (subcortical, cortical layers, networks)
- Slow BOLD dynamics acceptable (sluggish hemodynamic response ~4–6 s)
- Connectivity / resting-state networks
- Precise ROI definition needed
- ⚠️ Limitation: MRI-incompatible materials, noise, claustrophobia, expensive

### Use **Eye Tracking** when:
- Reading comprehension, scene perception, visual search
- Pupillometry as cognitive load / arousal proxy
- Gaze-contingent paradigm design
- Complement to EEG/fMRI as behavioral channel
- ⚠️ Limitation: not a direct neural measure

### Use **ECG / HRV** when:
- Autonomic nervous system, stress, or emotion studies
- Supplement to central measures (cardiac cycle phase effects on EEG)
- Neurovisceral integration research
- Real-time stress monitoring

### Use **Multimodal** when:
- Spatial + temporal resolution both needed → **EEG-fMRI**
- Gaze-locked neural activity → **EEG + Eye Tracker**
- Autonomic–central coupling → **EEG + ECG**
- Real-world cognitive monitoring → **Mobile EEG + Eye Tracker + ECG**

---

## Practical Checklist

- [ ] What is the primary DV? → temporal vs. spatial priority
- [ ] Is the population compatible? (MRI contraindications? Pediatric?)
- [ ] What is the available budget and equipment?
- [ ] Is mobility / ecological validity needed?
- [ ] Are there existing datasets in the lab using a specific modality?
- [ ] Does the target journal favor a particular modality?
- [ ] Is multimodal synchronization feasible (LSL, trigger box)?

---

## Synchronization When Multimodal

When combining modalities, always plan:
1. **Common clock**: Use LSL (Lab Streaming Layer) or hardware trigger box
2. **Marker alignment**: Same event markers sent to all recording systems simultaneously
3. **BIDS format**: Ensures organized storage for multi-modal datasets
