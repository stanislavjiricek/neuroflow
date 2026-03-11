---
title: /brain-build
---

# `/neuroflow:brain-build`

**Assemble a computational brain model — neuron models, network topology, connectivity, and simulation framework setup.**

`/brain-build` covers the full model construction pipeline, from choosing a neuron model and simulation framework to defining network topology and connectivity rules.

---

## When to use it

- You want to build a new spiking network, mean-field model, or whole-brain model from scratch
- You are continuing development of an existing model
- You need help choosing between simulation frameworks (NEURON, Brian2, NetPyNE, NEST, tvb-library)
- You want to define neuron types, synapse models, and connectivity matrices

---

## What it does

Claude determines whether this is a new model or an existing one, then guides you through the full construction pipeline.

### If starting a new model

Claude asks:

1. What brain region or circuit? (cortex, hippocampus, basal ganglia, full brain, custom)
2. What level of abstraction? (single compartment, multi-compartment, point neuron, mean-field / population model, spiking network)
3. What neuron model? (Hodgkin-Huxley, integrate-and-fire, AdEx, Izhikevich, custom)
4. What simulation framework? (NEURON, Brian2, NetPyNE, NEST, tvb-library, custom)
5. How many neurons / populations?
6. What connectivity structure? (random, topographic, small-world, empirical connectome, custom)
7. What inputs drive the model? (current injection, Poisson noise, sensory input, empirical LFP/EEG)
8. What outputs are needed? (spike trains, membrane potentials, LFP, population firing rate)

### If continuing an existing model

Claude reads `.neuroflow/brain-build/flow.md` and any existing model spec to understand where things left off, then asks what you want to work on next.

---

## Steps

1. Write `model-spec.md` — target circuit, abstraction level, neuron model, connectivity rules, input/output description, and definition of a successful model
2. Plan the implementation: compartment definitions, synapse types, connectivity matrices, parameter ranges
3. Build the model iteratively — write code, run a minimal test (single neuron fires, small network connects), refine
4. Apply domain best practices for the chosen framework (`NEURON .hoc/.py`, `Brian2 NeuronGroup/Synapses`, `NetPyNE netParams/simConfig`, etc.)

Model code is saved to your `models/` folder (or the path set in `.neuroflow/brain-build/flow.md`). Specs and notes go to `.neuroflow/brain-build/`.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/brain-build/flow.md` |
| Writes | `.neuroflow/brain-build/`, `.neuroflow/brain-build/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md`, `models/` (code output) |

---

## Related commands

- [`/brain-optimize`](brain-optimize.md) — run a parameter search or fit the model to data after building
- [`/brain-run`](brain-run.md) — launch a full simulation run of the assembled model
