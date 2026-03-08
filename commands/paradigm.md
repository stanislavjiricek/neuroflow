---
description: Generate a complete neuroscience experimental paradigm — PsychoPy script, LSL marker stream, configuration file, and marker documentation. Supports oddball, N-back, checkerboard, resting state, go/no-go, motor imagery, and custom designs.
argument-hint: [paradigm-type] [modality]
allowed-tools: [Read, Write, Bash]
---

# /paradigm — Generate Experimental Paradigm

You are generating a complete, runnable neuroscience experimental paradigm.

**Arguments**: $ARGUMENTS

## Your Task

Create a production-ready paradigm with PsychoPy + LSL integration, based on the specified paradigm type and modality.

## Step 1: Determine Requirements

If not specified in arguments, ask:
1. **Paradigm type**: oddball / N-back / checkerboard / resting-state / go-no-go / motor-imagery / custom
2. **Modality**: EEG / fMRI / EEG+Eye / multimodal
3. **Number of conditions**: (e.g., standard vs. deviant for oddball)
4. **Trial count per condition**
5. **Response required**: yes/no — which key(s)?
6. **Trigger method**: LSL / parallel port / none

## Step 2: Check for Existing Config

Check if `config/team.json` or `project_brief.md` exist in the current directory. If yes, read them and use the values (modality, paradigm_type, programming_language) to prefill parameters.

## Step 3: Generate Files

Create the following in `paradigm/`:

### `paradigm/config.py`
All parameters centralized:
```python
# Participant
PARTICIPANT_ID = "sub-01"
SESSION = "ses-01"

# Display
SCREEN_SIZE = [1920, 1080]
FULLSCREEN = True
BACKGROUND_COLOR = 'gray'

# Timing (all in seconds)
FIXATION_DURATION = 0.5
STIMULUS_DURATION = 0.2
ISI_MEAN = 1.0
ISI_JITTER = 0.2

# Trials
N_STANDARDS = 80
N_DEVIANTS = 20
N_BLOCKS = 4

# Triggers
USE_LSL = True
USE_PARALLEL_PORT = False
LPT_ADDRESS = 0x0378

# Markers (document each)
MARKER_STANDARD = 1
MARKER_DEVIANT = 2
MARKER_RESPONSE = 10
MARKER_BLOCK_START = 20
MARKER_BLOCK_END = 21
```

### `paradigm/main.py`
Complete PsychoPy experiment script with:
- Proper setup (Window, Clock, Logging)
- LSL marker outlet (if USE_LSL)
- Trial loop with jittered ISI
- Correct trigger timing (after win.flip())
- Response collection
- Data saving to CSV
- Emergency quit (Ctrl+Q)
- BIDS-compatible output filename

### `paradigm/markers.md`
Complete marker documentation table.

### `paradigm/README.md`
- Dependencies to install
- How to run
- Expected output

## Step 4: Validate and Report

After generating:
- List all files created
- Show the marker table
- Remind user to: pilot test timing, verify markers in recording software, check BIDS output format
- Suggest running `/check-bids` after first test recording
