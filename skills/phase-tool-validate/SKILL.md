---
name: phase-tool-validate
description: Phase guidance for the neuroflow /tool-validate command. Loaded automatically when /tool-validate is invoked to orient agent behavior, relevant skills, and workflow hints for the tool-validate phase.
user-invocable: false
---

# phase-tool-validate

The tool-validate phase creates and runs a testing pipeline to verify that a tool or paradigm works correctly — timing, markers, data output, and edge cases.

## Approach

- Read `.neuroflow/tool-build/` outputs before planning validation — understand what was built first
- Write a `validation-plan.md` before running any tests, with numeric pass criteria
- Cover timing accuracy, marker integrity, data output format, and known edge cases
- Stimulus timing is measured with a photodiode on the stimulus PC; software frame logs and static audits come first but do not replace it
- Report results objectively — include failures, not just passes
- Keep the `/tool-validate` rules: participants only see validated software, no agent on acquisition PCs during recordings, no software check is a stimulation-safety interlock

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules
- `neuroflow:phase-experiment` — its `scripts/psychopy_audit.py` audits paradigms statically and checks frame-interval logs

## Workflow hints

- Test scripts and logs go to `output_path` (`tools/tests/`), not inside `.neuroflow/`
- Save `validation-results.md` to `.neuroflow/tool-validate/` summarizing pass/fail status, with the `timing_check.py --record` blocks pasted in
- If validation reveals a design flaw, log the finding in `.neuroflow/reasoning/tool-validate.jsonl` and loop back to tool-build

## Scripts

All stdlib Python; run with `python <skill base dir>/scripts/<name>.py`; exit 0 = pass, 1 = findings, 2 = usage error or missing optional package.

- `timing_check.py` — marker-to-photodiode latency (p50, p95, max), jitter, missing markers, one-frame offsets and photodiode signal quality, from XDF (needs `pyxdf`) or CSV; `--record` prints a block for `validation-results.md`, `--verify-record` recomputes it.
- `xdf_check.py` — streams present, nominal vs effective rate, gaps and marker counts in an XDF file, right after a run (needs `pyxdf`).
- `lsl_check.py` — lists LSL streams; with `--stream NAME` measures rate, gaps, clock offset and latency against `--budget-ms` (needs `pylsl`).

## Slash command

`/neuroflow:tool-validate` — runs this workflow as a slash command.
