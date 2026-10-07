---
name: phase-brain-build
description: Phase guidance for the neuroflow /brain-build command. Loaded automatically when /brain-build is invoked to orient agent behavior, relevant skills, and workflow hints for assembling computational brain models.
user-invocable: false
---

# phase-brain-build

The brain-build phase covers the design and implementation of a computational brain model — neuron model selection, network topology, connectivity rules, and simulation framework setup.

## Approach

- Clarify the target circuit, abstraction level, and simulation framework before writing any code
- Write `model-spec.md` first; get user confirmation before implementation begins
- Start minimal: get a single neuron firing correctly before connecting a network
- Apply framework-specific best practices (NEURON `.hoc`/`.py` conventions, Brian2 `NeuronGroup`/`Synapses` patterns, NetPyNE `netParams`/`simConfig` structure, NEST `Create`/`Connect` idioms)
- Scale up (full network, long simulation, sweep) only behind a passing smoke test of the current code — see *Smoke test*

## Smoke test

A short simulation (seconds, small network) whose metrics are checked in code. Its record carries a hash of the model code, so it goes stale the moment the code changes — `/brain-run` and `/brain-optimize` check it before full runs.

1. Give the model a smoke entry point that writes a metrics JSON (or prints it as the last stdout line): `{"populations": {"E": {"n_spikes": 412, "rate_hz": 10.3}, "I": {"n_spikes": 240, "rate_hz": 24.0}}}`. Keys named `rate_hz` (or ending in `_rate_hz`) get the runaway and silence checks; `n_spikes`/`spike_count` the silence check when there are no rates; any key ending in `_ok` set to `false` fails (own checks — e.g. `bounded_ok` for a mean-field model, which has no spikes). Everything is checked for NaN and infinity.
2. Run it: `python <skill base dir>/scripts/smoke_test.py run --record .neuroflow/brain-build/smoke-record.json --model-dir models --metrics models/smoke/metrics.json -- python models/run_sim.py --duration 500 --out models/smoke` (`--max-rate` sets the runaway limit, default 300 Hz; `--allow-silence` when no input is applied)
3. Exit 0: passed — list `smoke-record.json` in the phase `flow.md`. Exit 1: a check failed (named in the output) — fix the model, rerun; never scale up on a failed record. Exit 2: the command or arguments are wrong.
4. Before a full run: `python <skill base dir>/scripts/smoke_test.py status --record .neuroflow/brain-build/smoke-record.json` — exit 1 means stale, failing or missing: rerun step 2.

Spike counts and rates mean nothing for some models (mean-field, TVB); state in `model-spec.md` which checks apply and use `_ok` keys for the rest.

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Workflow hints

- All model code goes to `output_path` (`models/`), not inside `.neuroflow/`
- Save `model-spec.md` to `.neuroflow/brain-build/` before writing any implementation
- Note key architecture decisions (neuron model chosen, connectivity rule, library selected) in `.neuroflow/reasoning/brain-build.jsonl`
- Common frameworks: NEURON, Brian2, NetPyNE, NEST, tvb-library, Custom Python/Julia

## Slash command

`/neuroflow:brain-build` — runs this workflow as a slash command.
