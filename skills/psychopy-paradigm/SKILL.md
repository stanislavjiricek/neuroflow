---
name: psychopy-paradigm
description: Use when creating, editing, or debugging PsychoPy experiment scripts — timing, visual/auditory stimuli, response collection, loop structures, data saving, parallel port triggers, screen refresh, Builder vs Coder, or PsychoPy-specific best practices. Triggers on "PsychoPy", "psychopy script", "Builder experiment", "PsychoPy timing", "visual stimulus PsychoPy", "collect responses PsychoPy", "PsychoPy error", "core.wait", "win.flip".
version: 1.0.0
---

# PsychoPy Paradigm Development

## Purpose

Best practices and code patterns for building robust, precisely-timed neuroscience paradigms in PsychoPy (Coder mode).

## Project Structure

```
paradigm/
├── main.py              # Main experiment script
├── config.py            # Parameters (editable without touching main.py)
├── stimuli/             # Image, audio, video files
├── data/                # Output data (auto-created)
└── triggers.py          # Trigger/marker logic (parallel port or LSL)
```

## Essential Setup

```python
from psychopy import visual, core, event, data, logging
import psychopy.iohub as io

# Display
win = visual.Window(
    size=[1920, 1080],
    fullscr=True,
    color='gray',           # Neutral background
    colorSpace='rgb',
    units='deg',
    monitor='testMonitor',  # Define in Monitor Center
    screen=0,               # 0=primary, 1=secondary
)

# Clock
globalClock = core.Clock()
logging.setDefaultClock(globalClock)

# Logging
logging.console.setLevel(logging.WARNING)
logFile = logging.LogFile('data/experiment.log', level=logging.EXP)
```

## Stimulus Presentation

### Visual Stimuli

```python
# Text
fixation = visual.TextStim(win, text='+', height=1.0, color='white')

# Image
img = visual.ImageStim(win, image='stimuli/face01.png', size=(5, 5), units='deg')

# Grating / Checkerboard
grating = visual.GratingStim(win, tex='sqrXsqr', mask=None,
                               sf=2, size=10, contrast=1.0)

# Circle / Shape
circle = visual.Circle(win, radius=2, fillColor='red', lineColor=None)
```

### Auditory Stimuli

```python
from psychopy import sound

tone = sound.Sound(value=1000, secs=0.2, stereo=True)
tone.play()
```

## Trial Loop

```python
import random

conditions = ['standard'] * 80 + ['deviant'] * 20
random.shuffle(conditions)

trial_clock = core.Clock()
trial_data = []

for trial_n, cond in enumerate(conditions):
    # Show fixation
    fixation.draw()
    win.flip()
    core.wait(0.5 + random.uniform(-0.05, 0.05))  # Jittered ISI

    # Show stimulus
    trial_clock.reset()
    stim = standard_stim if cond == 'standard' else deviant_stim
    stim.draw()
    win.flip()
    send_trigger(1 if cond == 'standard' else 2)   # Trigger on flip

    # Collect response
    keys = event.waitKeys(maxWait=1.0, keyList=['space', 'escape'],
                          timeStamped=trial_clock)
    win.flip()  # Clear screen

    # Record
    resp = keys[0] if keys else None
    trial_data.append({
        'trial': trial_n,
        'condition': cond,
        'key': resp[0] if resp else None,
        'rt': resp[1] if resp else None,
    })

    if event.getKeys(['escape']):
        break
```

## Timing Best Practices

1. **`win.flip()` synchronizes to screen refresh** (60 Hz = 16.67 ms, 120 Hz = 8.33 ms)
2. **Send trigger AFTER `win.flip()`** (the flip returns after the new frame is shown)
3. **Avoid `time.sleep()`** — use `core.wait()` which is more precise on most systems
4. **Use `core.Clock()`** for RT measurement, not `time.time()`
5. **Measure display latency**: use photodiode or audio click + oscilloscope before study

```python
# Correct trigger timing:
stim.draw()
win.flip()            # <-- blocks until frame is shown
send_trigger(code)    # <-- immediately after flip
```

## Response Collection

```python
# Single keypress
keys = event.waitKeys(maxWait=2.0, keyList=['f', 'j', 'escape'], timeStamped=True)

# Clear event buffer before trial
event.clearEvents(eventType='keyboard')

# Mouse
mouse = event.Mouse(win=win)
mouse.clickReset()
buttons, times = mouse.getPressed(getTime=True)
```

## Data Saving

```python
import pandas as pd

# After experiment
df = pd.DataFrame(trial_data)
df.to_csv(f'data/sub-{sub_id:02d}_task-oddball.csv', index=False)

# PsychoPy DataHandler (alternative)
exp_handler = data.ExperimentHandler(
    name='oddball', version='1.0',
    extraInfo={'participant': sub_id},
    dataFileName=f'data/sub-{sub_id:02d}',
)
```

## Abort / Safety

```python
# At start: emergency quit
event.globalKeys.add(key='q', modifiers=['ctrl'], func=core.quit)

# During loops:
if event.getKeys(['escape']):
    win.close()
    core.quit()
```

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| `pyglet.gl.GLException` | OpenGL driver issue | Update GPU drivers |
| Timing jitter > 1 frame | Background processes | Close all other apps, disable notifications |
| `Stimulus not visible` | Wrong `units` | Match units in Window and stimulus |
| Trigger too late | Trigger before flip | Move trigger after `win.flip()` |
| Response not detected | Event buffer full | Call `event.clearEvents()` before trial |
