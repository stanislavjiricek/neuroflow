---
title: /tool-build
---

# `/neuroflow:tool-build`

**Build a lab tool or software pipeline.**

`/tool-build` helps you design and implement technical infrastructure for your research: real-time EEG feedback systems, data acquisition pipelines, BCI systems, LSL integrations, or any other custom lab software.

---

## When to use it

- You need to build a real-time processing system
- You want to create a data acquisition or streaming pipeline
- You need to implement a BCI (brain-computer interface) system
- You want to build a custom preprocessing or analysis pipeline as a standalone tool

---

## What it does

Claude asks a series of questions to understand the tool:

1. **What kind of tool?** (real-time EEG feedback, acquisition pipeline, BCI, LSL integration, paradigm, preprocessing pipeline, other)
2. **What hardware or software does it interface with?** (amplifier, eye tracker, PsychoPy, BrainFlow, LSL, MNE, other)
3. **What programming language?**
4. **Standalone or integrates with an existing setup?**
5. **Definition of "done"** — what must the tool do to be considered working?

---

## Steps

**1. Write a `tool-spec.md`**

Documents what the tool does, inputs/outputs, hardware requirements, and constraints.

**2. Plan the implementation**

Architecture, key modules, data flow diagram.

**3. Build iteratively**

Write code, test, refine — applying domain best practices:

| Tech stack | Best practices applied |
|---|---|
| LSL | Outlet/inlet setup, stream info, chunk handling |
| PsychoPy | Trial structure, timing, marker integration |
| BrainFlow | Board init, data stream, session management |
| MNE | Raw/Epochs objects, filtering, ICA |
| Real-time EEG | Buffer management, online filtering, latency targets |

---

## Example session

```
/neuroflow:tool-build
```

```
Claude: What kind of tool are you building?

You: A real-time EEG neurofeedback system. It needs to stream alpha power 
     from MNE, compute the bandpower every 500ms, and send feedback 
     to a PsychoPy screen.

Claude: Got it — a closed-loop alpha neurofeedback system.

        Architecture:
        1. LSL inlet → reads from EEG amp
        2. MNE buffer → sliding 2s window, 500ms step
        3. Alpha bandpower → Welch PSD, 8-12 Hz
        4. LSL outlet → sends normalized feedback score
        5. PsychoPy → reads feedback score, updates visual gauge

        Writing tool-spec.md...
        [generates spec and then the implementation code]
```

---

## Output

- `tool-spec.md` — specification document → `.neuroflow/tool-build/`
- Tool code → `tools/` (or the path detected by `/neuroflow`)

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/tool-build/flow.md` |
| Writes | `.neuroflow/tool-build/`, `.neuroflow/tool-build/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md`, `tools/` (code output) |

---

## Related commands

- [`/tool-validate`](tool-validate.md) — test the tool you've built
- [`/experiment`](experiment.md) — integrate the tool into your paradigm
