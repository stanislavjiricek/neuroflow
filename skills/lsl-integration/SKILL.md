---
name: lsl-integration
description: Use when working with Lab Streaming Layer (LSL), creating LSL outlets or inlets, sending markers via LSL, synchronizing multiple recording streams, using pylsl, liblsl, or integrating LSL with EEG amplifiers, eye trackers, or PsychoPy. Triggers on "LSL", "lab streaming layer", "pylsl", "create outlet", "push marker", "stream synchronization", "XDF format", "multi-stream recording", "liblsl".
version: 1.0.0
---

# Lab Streaming Layer (LSL) Integration

## Purpose

LSL is the standard protocol for synchronized, real-time streaming of neuroscience data and event markers across devices and software. It enables precise multi-stream synchronization for EEG, eye tracking, ECG, and stimulus markers.

## Core Concepts

- **Outlet**: Pushes data into the LSL network (e.g., PsychoPy sending markers)
- **Inlet**: Receives data from the LSL network (e.g., recording software receiving markers)
- **Stream**: Named, typed data channel with metadata
- **XDF**: Cross-platform file format for recorded LSL streams (`.xdf`)
- **LabRecorder**: Records all LSL streams simultaneously to `.xdf`

## Marker Stream (Event Outlet)

### Python – Sending Markers
```python
from pylsl import StreamInfo, StreamOutlet
import pylsl

# Create a marker stream (1 channel, string type)
info = StreamInfo(
    name='Markers',
    type='Markers',
    channel_count=1,
    nominal_srate=pylsl.IRREGULAR_RATE,
    channel_format='string',
    source_id='neuroflow_markers'
)
outlet = StreamOutlet(info)

# Send a marker
outlet.push_sample(['stimulus_onset_oddball'])

# Send a marker with timestamp
outlet.push_sample(['response_correct'], timestamp=pylsl.local_clock())
```

### Marker Naming Convention

Use structured, descriptive marker names:
```
stimulus_onset_<condition>
stimulus_offset
response_<type>_<outcome>       # e.g., response_button_correct
block_start_<block_id>
block_end
trial_start
trial_end
rest_start
rest_end
```

## Data Stream Outlet (Continuous Signal)

```python
from pylsl import StreamInfo, StreamOutlet
import numpy as np

# EEG-like stream: 64 channels, 1000 Hz, float32
info = StreamInfo('BioSemi', 'EEG', 64, 1000, 'float32', 'biosemi_amp_1')
outlet = StreamOutlet(info)

# Push chunk of samples
samples = np.random.randn(64).tolist()
outlet.push_sample(samples)
```

## Receiving Data (Inlet)

```python
from pylsl import StreamInlet, resolve_stream

# Find and connect to a marker stream
streams = resolve_stream('type', 'Markers')
inlet = StreamInlet(streams[0])

# Pull sample (blocking with timeout)
sample, timestamp = inlet.pull_sample(timeout=1.0)
print(f"Marker: {sample[0]} at t={timestamp:.4f}")
```

## Integration with PsychoPy

```python
from pylsl import StreamInfo, StreamOutlet
import pylsl

# In PsychoPy experiment script (Before Experiment tab):
lsl_info = StreamInfo('PsychoPy_Markers', 'Markers', 1,
                       pylsl.IRREGULAR_RATE, 'string', 'psychopy')
lsl_outlet = StreamOutlet(lsl_info)

# At stimulus onset (Each Frame / Routine Begin):
lsl_outlet.push_sample([f'stim_{condition}_{trial_n}'])
```

## Multi-Stream Synchronization

LSL handles clock synchronization automatically via:
- **Continuous time correction**: Each stream tracks drift relative to LSL clock
- **Unified timestamps**: All streams share `pylsl.local_clock()` reference
- **XDF stores** all streams + timestamps → synchronization preserved offline

**Recording all streams:**
Use **LabRecorder** (standalone app) or `mne_realtime` / `pyxdf` to record.

## Reading XDF Files (Offline)

```python
import pyxdf

streams, header = pyxdf.load_xdf('recording.xdf')

# List stream names
for s in streams:
    print(s['info']['name'][0], s['info']['type'][0])

# Get marker stream
markers = [s for s in streams if s['info']['type'][0] == 'Markers'][0]
marker_times = markers['time_stamps']
marker_values = markers['time_series']
```

## Common Issues

| Issue | Solution |
|---|---|
| No stream found | Check firewall, both devices on same subnet |
| Timestamp drift | Ensure LSL clock sync is enabled; use `pylsl.local_clock()` for all pushes |
| Dropped samples | Increase buffer size in StreamOutlet (max_buffered) |
| Wrong channel count | Re-create outlet with correct `channel_count` |
| PsychoPy marker delay | Push marker before `win.flip()` for best timing |
