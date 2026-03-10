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

Claude reads the PsychoPy script directly and checks:
- Trial timing matches the design spec
- Marker codes are correct for each event type
- Response handling covers all cases
- Edge cases (no response, early exit, block transitions) are handled

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

        Reading paradigm/oddball.py...

        Issues found:
        ⚠ ISI jitter implementation uses clock.getTime() — rounding to frame
          boundaries could produce actual ISI of 800 ± 16.7ms at 60Hz.
          Suggest using core.wait() with precise timing.
        ✓ Stimulus duration: correct
        ✓ Marker codes: correct
        ✓ LSL outlet: initialized before trial loop — correct
```

---

## Output

All validation output is saved in `.neuroflow/tool-validate/`:
- `validation-plan.md`
- `validation-results.md`

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/tool-build/flow.md`, `.neuroflow/experiment/flow.md`, `.neuroflow/tool-validate/flow.md` |
| Writes | `.neuroflow/tool-validate/`, `.neuroflow/tool-validate/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md` |

---

## Related commands

- [`/tool-build`](tool-build.md) — build the tool before validating it
- [`/experiment`](experiment.md) — design the paradigm being validated
- [`/data`](data.md) — the next step after validation passes
