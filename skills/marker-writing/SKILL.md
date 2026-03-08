---
name: marker-writing
description: Use when writing event markers or triggers to EEG, fMRI, or physiological signals — via parallel port, serial port, LSL, BrainProducts trigger, TTL pulse, or audio trigger. Triggers on "send markers", "write triggers", "parallel port EEG", "TTL trigger", "marker timing", "trigger latency", "event code", "how to mark stimulus onset", "trigger box", "MMBT trigger".
version: 1.0.0
---

# Marker / Trigger Writing for Neuroscience Recordings

## Purpose

Ensure precise, low-latency event marking in neuroscience recording systems. Markers encode the timing and type of experimental events (stimulus onsets, responses, block boundaries) into the recorded data stream.

## Trigger Methods Overview

| Method | Latency | Reliability | Common systems |
|---|---|---|---|
| **Parallel port (LPT)** | < 1 ms | Very high | BrainProducts, EEGLAB legacy |
| **TTL pulse (hardware)** | < 1 ms | Very high | Any amplifier with TTL input |
| **LSL marker stream** | < 5 ms | High (software clock) | Any LSL-compatible system |
| **Serial port (COM)** | 1–5 ms | High | Older systems |
| **Audio trigger** | ± 1 ms (sound card) | High | g.tec, some BioSemi |
| **USB trigger box** | 1–5 ms | High | MMBT, ioLabs, TriggerBox |

---

## Parallel Port (LPT) – Windows

```python
import ctypes
import time

# Load DLLs (requires inpout32.dll or inpoutx64.dll)
# Place inpout32.dll in the script directory or system32
dll = ctypes.WinDLL("inpoutx64.dll")

LPT_ADDRESS = 0x0378   # Standard LPT1 address (check Device Manager)

def send_trigger(code, duration_ms=5):
    dll.Out32(LPT_ADDRESS, code)       # Set trigger
    time.sleep(duration_ms / 1000)
    dll.Out32(LPT_ADDRESS, 0)          # Reset to 0

# Usage
send_trigger(1)   # Stimulus onset – condition 1
send_trigger(10)  # Response
```

**Important:**
- Trigger value range: 0–255 (8-bit parallel port)
- Always reset to 0 after trigger (pulse, not sustained)
- Test latency with oscilloscope before data collection

---

## LSL Marker Stream (Cross-Platform)

```python
from pylsl import StreamInfo, StreamOutlet, local_clock, IRREGULAR_RATE

info = StreamInfo('Markers', 'Markers', 1, IRREGULAR_RATE, 'string', 'my_paradigm')
outlet = StreamOutlet(info)

def send_marker(label):
    outlet.push_sample([label], timestamp=local_clock())

# Usage
send_marker('stimulus_onset_standard')
send_marker('response_correct')
```

See `lsl-integration` skill for full LSL setup.

---

## USB Trigger Box (MMBT / TriggerBox)

```python
import serial   # pip install pyserial

port = serial.Serial('COM3', baudrate=115200, timeout=1)

def send_trigger(code):
    port.write(bytes([code]))  # Single byte 0–255

send_trigger(1)
```

Common devices: **Brain Products BrainAmp MMBT**, **ioLabs**, **Cedrus StimTracker**

---

## PsychoPy Integration

### Parallel Port in PsychoPy

```python
from psychopy import parallel

# Initialize (Windows: address; Linux: /dev/parport0)
p = parallel.ParallelPort(address=0x0378)

def send_trigger(code, duration=0.005):
    p.setData(code)
    core.wait(duration)
    p.setData(0)
```

### LSL in PsychoPy

```python
# In "Before Experiment" tab:
from pylsl import StreamInfo, StreamOutlet, IRREGULAR_RATE, local_clock
info = StreamInfo('PsychoPy', 'Markers', 1, IRREGULAR_RATE, 'string', 'pp1')
outlet = StreamOutlet(info)

# In "Each Routine Begin" or "Each Frame":
outlet.push_sample([f'trial_{trial_n}_{condition}'], timestamp=local_clock())
```

---

## Timing Best Practices

1. **Send trigger BEFORE `win.flip()`** — the flip() call blocks until screen refresh
2. **For stimulus onset**: send trigger immediately after flip to match first frame
3. **Never use `time.sleep()`** for precise timing — use `core.wait()` in PsychoPy
4. **Jitter**: measure actual onset times with photodiode or audio device
5. **Log all triggers** to a local file alongside the stream

---

## fMRI Markers

fMRI uses the **scanner TTL pulse** to mark the start of each TR:
```python
# Wait for scanner trigger (key press 's' from MRI room)
keys = event.waitKeys(keyList=['s'])
send_marker('scan_start')
```

Within the task, use stimulus onset markers as in EEG.

---

## Marker Verification Checklist

- [ ] All marker codes documented before recording
- [ ] Trigger pulse duration set to 5–10 ms (not sustained)
- [ ] Trigger resets to 0 after each event
- [ ] Pilot recording checked: markers appear at correct latency in raw signal
- [ ] Marker names are unique and human-readable
- [ ] Events file (`_events.tsv`) generated from markers after session
