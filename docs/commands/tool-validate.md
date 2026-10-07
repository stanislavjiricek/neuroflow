---
title: /tool-validate
---

# `/neuroflow:tool-validate`

**Create a comprehensive testing pipeline to verify a tool or paradigm works correctly.**

`/tool-validate` helps you build test scripts and procedures to verify timing accuracy, marker integrity, data output format, hardware integration, and edge cases — before real data collection begins.

---

## When to use it

- After building a paradigm with `/experiment` — validate timing and markers
- After building a tool with `/tool-build` — verify it meets its spec
- Before starting data collection — confirm the whole acquisition pipeline works

---

## What it does

Claude asks:

1. **What needs to be validated?** (paradigm timing, marker accuracy, LSL streaming, data output format, hardware integration, edge cases)
2. **What is the tool / paradigm under test?** (point to the file or folder)
3. **Pass/fail criteria** — what does "correct" look like?

---

## Validation areas

| Area | What is checked |
|---|---|
| **Paradigm timing** | Trial duration, ISI, SOA, jitter range |
| **Marker accuracy** | Correct codes sent, timing relative to stimulus onset |
| **LSL streaming** | Stream info, sampling rate stability, chunk integrity |
| **Data output** | File format, BIDS naming, sidecar JSON completeness |
| **Hardware integration** | Amplifier connection, trigger box wiring, device sync |
| **Edge cases** | Missing responses, early exits, hardware disconnects |

---

## Steps

**1. Write a `validation-plan.md`**

Defines what is being tested, how, and the pass/fail criteria.

**2. Build test scripts or procedures**

Claude writes automated tests where possible and step-by-step manual procedures where automation is not feasible.

**3. Run validation and record results**

Claude runs the tests and records outcomes in a `validation-results.md` document.

**4. PsychoPy script audit (if applicable)**

Claude first runs `psychopy_audit.py` — a static check of the `.py` or `.psyexp` file that needs no PsychoPy installation — and then reads the script for what a static check cannot see:
- Trial timing matches the design spec, in frames rather than `core.wait()`
- Marker codes are correct for each event type and sent with `win.callOnFlip()`
- Response handling covers all cases
- Edge cases (no response, early exit, block transitions) are handled

---

## Timing and recording checks

Run during a pilot on the real stimulus and recording PCs. Each script exits 0 = pass, 1 = findings, 2 = usage error, and needs no AI agent at the rig.

| Script | What it checks |
|---|---|
| `timing_check.py` | Marker-to-photodiode latency from an XDF or CSV recording: p50, p95, max, jitter, missing markers, one-frame offsets, photodiode signal quality. `--record` writes a block for `validation-results.md`; `--verify-record` recomputes it, so an edited number is caught. |
| `xdf_check.py` | Streams present, nominal vs effective sampling rate, gaps, marker counts per code — right after each run, while it can still be repeated. |
| `psychopy_audit.py --csv` | A run's frame-interval log or trial CSV: dropped frames, vsync problems, durations off by a frame. |
| `lsl_check.py` | LSL streams on the network; rate, gaps, clock offset and latency for the streams you name. |

A clean software frame log does not replace the photodiode — only the photodiode sees when the screen actually changed. For hardware-free tests, a recorded file can be replayed as a stream named `…-REPLAY` (mne-lsl's `PlayerLSL`), so it cannot be mistaken for real data.

## Rules

- Participants only ever see software that passed its validation plan — never Claude Code.
- No agent runs on the acquisition PC during participant recordings; validation runs are fine.
- No script, hook or guard here is a stimulation-safety interlock.

---

## Example session

```
/neuroflow:tool-validate
```

```
Claude: What needs to be validated?

You: The oddball paradigm in paradigm/oddball.py — timing and markers.

Claude: I'll check the PsychoPy script for:
        ✓ ISI jitter: expected 800–1200ms
        ✓ Stimulus duration: expected 50ms
        ✓ Marker codes: S=standard (1), T=target (2)
        ✓ LSL outlet initialization
        ✓ Block transitions

        Running psychopy_audit.py on paradigm/oddball.py...

        Issues found:
        ⚠ PSY003 line 58: LSL marker pushed after win.flip(), not via
          win.callOnFlip() — it trails stimulus onset by up to a frame.
        ⚠ ISI jitter drawn in seconds — every ISI is rounded to whole
          frames (16.7 ms at 60 Hz). Draw it in frames, or log the
          realised ISI from the flip times.
        ✓ Stimulus duration: 3 frames at 60 Hz — correct
        ✓ Marker codes: S=1, T=2 — match the marker map
        ✓ LSL outlet: initialized before trial loop — correct
```

---

## Output

All validation output is saved in `.neuroflow/tool-validate/`:
- `validation-plan.md` — what is tested and the numeric pass criteria
- `validation-results.md` — results, failures included, with the `timing_check.py` record blocks

Test scripts go to `tools/tests/`, next to the tool they validate.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/tool-build/flow.md`, `.neuroflow/experiment/flow.md`, `.neuroflow/tool-validate/flow.md` |
| Writes | `.neuroflow/tool-validate/`, `.neuroflow/tool-validate/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md`, `tools/tests/` (test scripts) |

---

## Related commands

- [`/tool-build`](tool-build.md) — build the tool before validating it
- [`/experiment`](experiment.md) — design the paradigm being validated
- [`/data`](data.md) — the next step after validation passes
