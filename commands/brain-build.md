---
name: brain-build
description: Assemble a computational brain model or continue working on one — neuron models, network topology, connectivity, and simulation framework setup.
phase: brain-build
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/brain-build/flow.md
  - skills/phase-brain-build/SKILL.md
writes:
  - .neuroflow/brain-build/
  - .neuroflow/brain-build/flow.md
  - .neuroflow/brain-build/smoke-record.json
  - .neuroflow/sessions/YYYY-MM-DD.md
lifecycle: full
produces:
  - .neuroflow/brain-build/model-spec.md
  - .neuroflow/brain-build/smoke-record.json
next:
  - brain-run
  - brain-optimize
---

# /brain-build

Read the `neuroflow:phase-brain-build` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` (and open with the version notice when the project's `plugin_version` is missing or older than the running neuroflow's version in `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` — **Command lifecycle**, step 3), `flow.md`, and `.neuroflow/brain-build/flow.md` before starting.

## What this command does

Helps the user assemble a new computational brain model or continue developing an existing one. Covers the full model construction pipeline — from choosing a neuron model and simulation framework to defining network topology and connectivity rules.

Ask to determine the current state:
1. Is this a new model or continuing an existing one?
2. If continuing — read `.neuroflow/brain-build/flow.md` and any existing model spec to understand where things left off.

---

## If starting a new model

Ask:
1. What brain region or circuit is being modelled? (e.g. cortex, hippocampus, basal ganglia, full brain, custom)
2. What level of abstraction? (single compartment, multi-compartment, point neuron, mean-field / population model, spiking network)
3. What neuron model? (Hodgkin-Huxley, integrate-and-fire, AdEx, Izhikevich, custom)
4. What simulation framework? (NEURON, Brian2, NetPyNE, NEST, tvb-library, custom)
5. How many neurons / populations?
6. What connectivity structure? (random, topographic, small-world, empirical connectome, custom)
7. What inputs drive the model? (current injection, Poisson noise, sensory input, empirical LFP/EEG)
8. What outputs are needed? (spike trains, membrane potentials, LFP, population firing rate)

---

## Steps

1. Write a `model-spec.md` — target circuit, abstraction level, neuron model, connectivity rules, input/output description, and definition of a successful model
2. Plan the implementation: compartment definitions, synapse types, connectivity matrices, parameter ranges
3. Build the model iteratively — write code, run a minimal test (single neuron fires, small network connects), refine
4. Apply domain best practices for the chosen framework (NEURON `.hoc`/`.py`, Brian2 `NeuronGroup`/`Synapses`, NetPyNE `netParams`/`simConfig`, etc.)
5. Before handing the model to `/brain-run` or `/brain-optimize`: pass the smoke test with `smoke_test.py` (skill → *Smoke test*) — it writes `.neuroflow/brain-build/smoke-record.json`, tied to a hash of the model code

Save specs and notes (`model-spec.md`, connectivity notes) in `.neuroflow/brain-build/`. Write the actual model code to `output_path` (from `.neuroflow/brain-build/flow.md`, default: `models/`) — not inside `.neuroflow/`.

---

## At end

- Update `.neuroflow/brain-build/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `active_phase` in `project_config.md` if the phase changed
