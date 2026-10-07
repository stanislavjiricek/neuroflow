---
name: tool-validate
description: Create a comprehensive testing pipeline to verify that a tool or paradigm works correctly — timing, markers, data output, edge cases.
phase: tool-validate
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/tool-build/flow.md
  - .neuroflow/experiment/flow.md
  - .neuroflow/tool-validate/flow.md
  - skills/phase-tool-validate/SKILL.md
writes:
  - .neuroflow/tool-validate/
  - .neuroflow/tool-validate/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
  - tools/tests/
lifecycle: full
produces:
  - .neuroflow/tool-validate/validation-plan.md
  - .neuroflow/tool-validate/validation-results.md
next:
  - data
---

# /tool-validate

Read the `neuroflow:phase-tool-validate` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/tool-validate/flow.md` before starting. Also check `.neuroflow/tool-build/` and `.neuroflow/experiment/` for relevant specs and code.

## What this command does

Creates a testing pipeline to verify a tool or paradigm is working correctly before real data collection begins.

Ask:
1. What needs to be validated? (paradigm timing, marker accuracy, LSL streaming, data output format, hardware integration, edge cases)
2. What is the tool / paradigm under test? (point to the relevant file or folder)
3. What does "correct" look like — what are the pass/fail criteria?

---

## Steps

1. Write a `validation-plan.md` — what is being tested, how, and what the pass criteria are (as numbers: e.g. p95 marker-to-photodiode latency ≤ 20 ms, jitter ≤ 2 ms, 0 missing markers, 0 dropped frames)
2. Build the test scripts or procedures
3. Run the validation and record results
4. For paradigm-specific checks (timing, markers, edge cases), run the static audit first, then read the script for what it cannot see (design logic, response handling, block transitions, early exits):
   `python <phase-experiment base dir>/scripts/psychopy_audit.py paradigm/` — exit 0 = no warnings, 1 = warnings, 2 = unreadable. Its marker map is the list of codes the recording must contain.

Write test scripts to `output_path` (default `tools/tests/`) — tests are deliverables that live with the tool they validate, never inside `.neuroflow/`. Save the validation plan and results record (`validation-plan.md`, `validation-results.md`) in `.neuroflow/tool-validate/`.

## Timing and recording checks

Run these on the real stimulus and recording PCs during a pilot (a photodiode on the screen, the experimenter or a test signal instead of a participant). Each script lives in this skill's `scripts/` folder (`<phase-tool-validate base dir>`), needs no AI agent at the rig, and exits 0 = pass, 1 = findings, 2 = usage error (for example a missing optional package).

| Check | Command | What it reports |
|---|---|---|
| Stimulus onset timing | `timing_check.py --xdf pilot.xdf --markers <marker stream> --photodiode <stream> --channel <n> --refresh-hz 60 --max-latency-ms 20 --max-jitter-ms 2 --record` (or `--marker-csv` + `--photodiode-csv`) | marker-to-photodiode latency p50 / p95 / max, jitter, missing markers, one-frame offsets, photodiode signal quality |
| Recording integrity | `xdf_check.py pilot.xdf --expect <stream> --expect-markers <n>` | streams present, nominal vs effective rate, gaps, marker counts per code |
| Frame timing in software | `psychopy_audit.py --csv <frame-interval log or trial CSV> --refresh-hz 60` (phase-experiment scripts) | dropped frames, vsync problems, durations off by a frame |
| LSL health | `lsl_check.py --stream <name> --duration 30 [--budget-ms <n>]` | rate, gaps, clock offset, latency for the named streams |

- Paste the block that `timing_check.py --record` prints into `validation-results.md`; `timing_check.py --verify-record .neuroflow/tool-validate/validation-results.md` recomputes it from the recorded files and fails if a number was edited. Report failures as failures.
- A clean software frame log does not replace the photodiode: frame intervals say nothing about when the screen actually changed.
- A weak photodiode signal (the script says so) makes every latency number unreliable — fix sensor placement or patch brightness first.
- Hardware-free tests: replay a recorded file as a live stream, named so it cannot be mistaken for real data — for files MNE can read, `mne_lsl.player.PlayerLSL(fname, name="EEG-REPLAY", source_id="replay-<file>").start()` — and run the tool's tests against it in CI. The name and source_id travel into LabRecorder and the XDF header, so a replayed recording stays recognisable.

## Rules

- **Participants only ever see validated software.** A paradigm or tool goes in front of participants only after it passed its `validation-plan.md` on the stimulus PC; it runs in PsychoPy or the tool itself, never inside Claude Code.
- **No agent on the acquisition PC during a recording.** Validation runs with an agent are fine; participant sessions run without one.
- **No software check is a stimulation-safety interlock.** None of these scripts, and no hook or guard, protects anyone from stimulation hardware; the device's limits, the approved protocol and the lab's procedures do.

---

## At end

- Update `.neuroflow/tool-validate/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `active_phase` in `project_config.md` if the phase changed
