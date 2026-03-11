---
name: phase-brain-build
description: Phase guidance for the neuroflow /brain-build command. Loaded automatically when /brain-build is invoked to orient agent behavior, relevant skills, and workflow hints for assembling computational brain models.
---

# phase-brain-build

The brain-build phase covers the design and implementation of a computational brain model — neuron model selection, network topology, connectivity rules, and simulation framework setup.

## Approach

- Clarify the target circuit, abstraction level, and simulation framework before writing any code
- Write `model-spec.md` first; get user confirmation before implementation begins
- Start minimal: get a single neuron firing correctly before connecting a network
- Apply framework-specific best practices (NEURON `.hoc`/`.py` conventions, Brian2 `NeuronGroup`/`Synapses` patterns, NetPyNE `netParams`/`simConfig` structure, NEST `Create`/`Connect` idioms)

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Workflow hints

- All model code goes to `output_path` (`models/`), not inside `.neuroflow/`
- Save `model-spec.md` to `.neuroflow/brain-build/` before writing any implementation
- Note key architecture decisions (neuron model chosen, connectivity rule, library selected) in `.neuroflow/reasoning/brain-build.json`
- Common frameworks: NEURON, Brian2, NetPyNE, NEST, tvb-library, Custom Python/Julia

## Slash command

`/neuroflow:brain-build` — runs this workflow as a slash command.
