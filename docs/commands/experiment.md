---
title: /experiment
---

# `/neuroflow:experiment`

**Full experiment preparation — paradigm design, recording setup, and instrument configuration.**

`/experiment` covers everything you need before data collection starts: designing the experiment structure, specifying recording parameters, and configuring hardware integrations.

---

## When to use it

- You need to design or refine an experimental paradigm
- You want to generate a PsychoPy script
- You need to document your recording setup (electrodes, sampling rate, reference)
- You need to configure LSL streaming, trigger boxes, or multi-device synchronization

---

## Ground rules

- **Ethics gate.** Designing, setting up and bench-testing need no approval. Anything with participants — sessions, pilots with volunteers, allocating participants — waits until [`/ethics`](ethics.md) records an approval you confirmed, still in date.
- **Participants only ever see validated software.** Paradigms, questionnaires and consent run in PsychoPy (or what your protocol names), never in Claude Code.
- **No agent on the acquisition PC during a recording.** Claude Code writes and checks the paradigm; participant sessions run without it.
- **No software check is a stimulation-safety interlock.** For TMS, tES and other stimulators, a person starts stimulation; hardware limits, the approved protocol and the lab's procedures are the protection.

## Three areas

Claude asks which area you want to work on:

=== "1. Paradigm design"

    Design the experiment structure and produce a PsychoPy script.

    **Claude asks:**
    - Paradigm type (oddball, N-back, go/no-go, resting state, custom)
    - Number of trials / blocks / conditions
    - Stimuli type (visual, auditory, tactile)
    - Responses collected
    - Timing requirements (ISI, SOA, jitter)
    - Markers needed — which events must be tagged

    **Output:** `paradigm-[name].py` saved to your `paradigm/` folder (or the path detected by `/neuroflow`), following neuroscience paradigm best practices: visual durations in frames, markers sent with `win.callOnFlip()`, the refresh rate measured at start-up, frame intervals recorded.

    **Checks and helpers:**

    - `psychopy_audit.py` audits the script (Coder `.py` or Builder `.psyexp`) without running it: time-based instead of frame-based timing, markers sent outside `callOnFlip`, trigger codes never reset, hard-coded refresh rates, blocking calls in the frame loop, missing logs. It also prints the marker map that [`/tool-validate`](tool-validate.md) checks against the recording.
    - `allocation.py` builds condition orders (Williams or Latin square, full permutation) or group allocation (randomised blocks) once from a recorded seed, and hands out one slot per participant from an append-only ledger. For non-clinical studies — a clinical trial uses its trial unit's validated randomisation system.
    - An optional `preflight()` block for the top of the paradigm checks refresh rate, disk space, LSL streams, trigger port and ethics expiry before each session and logs the result.

    **Example:**
    ```
    You: Oddball paradigm, 80% standard / 20% target tones. 300 trials, 3 blocks.
         ISI 1000ms ± 200ms jitter. Need LSL markers for every stimulus.

    Claude: I'll generate a PsychoPy script with:
            - Block structure: 3 × 100 trials
            - Standard tone: 1000 Hz, 50ms, 80 dB
            - Target tone: 1500 Hz, 50ms, 80 dB
            - ISI: uniform jitter 800–1200 ms
            - LSL outlet: sends markers 'S' (standard) and 'T' (target)

            [generates paradigm-oddball.py]
    ```

=== "2. Recording setup"

    Define recording parameters and produce a setup checklist.

    **Claude asks:**
    - Modality and hardware (EEG amplifier, eye tracker, etc.)
    - Number of channels and electrode placement
    - Sampling rate, reference, and ground
    - Mains (power-line) frequency and the display's refresh rate
    - File format and storage location

    **Output:** `recording-setup.md` saved to `.neuroflow/experiment/`

    **Example:**
    ```
    You: BrainProducts actiCHamp Plus, 64 channels, 10-20 system.
         Sampling: 1000 Hz. Reference: Cz. Ground: AFz. BrainVision format.

    Claude: [generates recording-setup.md with full checklist including
             impedance targets, cap placement guide, amplifier settings,
             BrainVision Recorder configuration, and a pre-session checklist]
    ```

=== "3. Instrument configuration"

    Configure LSL integration, trigger/marker timing, and hardware connections.

    **Covers:**
    - LSL outlet/inlet setup
    - Trigger box wiring and timing verification
    - Synchronization between multiple streams (EEG + eye tracker, EEG + ECG)
    - Latency measurement and compensation
    - Stream health: `lsl_check.py` lists the LSL streams on the network and measures rate, gaps, clock offset and latency for the ones you name

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/ideation/flow.md`, `.neuroflow/experiment/flow.md`, `.neuroflow/ethics/status.md` |
| Writes | `.neuroflow/experiment/`, `.neuroflow/experiment/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md`, `paradigm/` (code output) |

---

## Related commands

- [`/ideation`](ideation.md) — define the research question before designing the paradigm
- [`/tool-build`](tool-build.md) — build custom tools or real-time systems for the experiment
- [`/tool-validate`](tool-validate.md) — validate paradigm timing and marker accuracy before data collection
- [`/data`](data.md) — the next step after data collection
