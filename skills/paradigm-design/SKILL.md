---
name: paradigm-design
description: Use when designing or implementing neuroscience experimental paradigms — oddball, checkerboard, N-back, resting state, go/no-go, Stroop, RSVP, steady-state VEP, motor imagery, passive listening, flanker task, or custom event-related designs. Triggers on "design a paradigm", "create an oddball task", "checkerboard stimulus", "ERP paradigm", "how to structure the experiment", "block design vs event-related", "counterbalancing", "trial structure".
version: 1.0.0
---

# Neuroscience Paradigm Design

## Purpose

Design experimentally valid, technically sound paradigms for neuroscience recording sessions, with correct timing, counterbalancing, and marker structure.

## Design Principles

### 1. Event-Related vs. Block Design

| Design | Use when | Modality |
|---|---|---|
| **Event-related** | Single trial resolution needed, overlapping stimuli OK | EEG (ERPs), fMRI (slow) |
| **Block design** | Sustained activation, high SNR fMRI | fMRI (preferred), EEG (state) |
| **Mixed design** | Both transient and sustained components | fMRI |
| **Resting state** | No task, connectivity / spontaneous activity | EEG, fMRI |

### 2. Critical Timing Parameters

| Parameter | EEG recommendation | fMRI recommendation |
|---|---|---|
| **Stimulus duration** | 50–500 ms | 500–2000 ms |
| **ISI (inter-stimulus)** | 500–2000 ms (jittered) | 2–8 s (jittered) |
| **ITI (inter-trial)** | 1000–4000 ms | 4–20 s |
| **Block duration** | 20–60 s | 16–40 s |
| **Rest between blocks** | 10–30 s | 10–20 s |

**Jitter ISI/ITI** to avoid periodicity artifacts and reduce expectation.

### 3. Number of Trials (Power)

- **ERP (signal averaging)**: minimum 30–50 trials per condition (aim 80–100)
- **Resting state EEG**: 2–5 minutes per condition
- **fMRI event-related**: minimum 20–30 events per condition per session
- **Classification**: ≥50 epochs per class for ML (≥100 recommended)

---

## Common Paradigm Templates

### Oddball (P300 / MMN)
```
Standard stimuli: 80% (frequent, no-response)
Deviant stimuli:  20% (rare, target response or passive deviant)
ISI: 600 ms (jittered ±100 ms)
Markers: standard=1, deviant=2, response=10
```

### Checkerboard (SSVEP / VEP)
```
Flickering checkerboard: 8 Hz or 12 Hz (or both eyes different)
Trial duration: 3–5 s
Rest between: 2–3 s
Markers: stim_on=1, stim_off=2
```

### N-Back (Working Memory)
```
1-back, 2-back, 3-back (adaptive or fixed)
Stimulus duration: 500 ms
ISI: 1500–2000 ms
Target rate: 25–33%
Markers: nontarget=1, target=2, response_correct=10, response_error=11
```

### Go / No-Go (Response Inhibition)
```
Go trials: 70–80% (button press)
No-Go trials: 20–30% (withhold response)
SOA: 700–1200 ms
Markers: go=1, nogo=2, response=10, commission_error=11
```

### Motor Imagery (BCI)
```
Cue: arrow left / right / rest (1.5 s)
Imagery period: 4–6 s
Feedback period: optional (0.5–1 s)
Markers: cue_left=1, cue_right=2, cue_rest=3, imagery_start=10, imagery_end=11
```

### Resting State
```
Eyes open: 3 min (fixation cross)
Eyes closed: 3 min (auditory beep at start/end)
Markers: eo_start=1, eo_end=2, ec_start=3, ec_end=4
```

---

## Counterbalancing

- **Latin square** for condition order across participants
- **Randomize** trial order within blocks (seed per participant for reproducibility)
- **Pseudorandomize**: ensure no more than 3 consecutive same-condition trials
- **Record seed** in the data file or marker stream

## Marker Plan Template

Before coding, define all markers:

| Code | Event | Notes |
|---|---|---|
| 1 | Stimulus onset – condition A | e.g., standard |
| 2 | Stimulus onset – condition B | e.g., deviant |
| 10 | Participant response | button press |
| 11 | Incorrect response | |
| 20 | Block start | include block number |
| 21 | Block end | |
| 99 | Session end | |

## Output Checklist

- [ ] Paradigm script runs without errors
- [ ] All critical events send correct markers
- [ ] ISI/ITI jitter is implemented
- [ ] Trial count meets statistical power requirements
- [ ] Counterbalancing logic verified
- [ ] Pilot tested on ≥2 participants before data collection
- [ ] Paradigm version recorded in session log
