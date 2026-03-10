---
name: phase-data
description: Phase guidance for the neuroflow /data command. Loaded automatically when /data is invoked to orient agent behavior, relevant skills, and workflow hints for the data intake phase.
---

# phase-data

The data phase locates raw data, validates BIDS structure, and runs conversion scripts to get data ready for preprocessing.

## Approach

- Follow the three-step sequence in order: inventory → validate → convert — do not skip ahead
- Confirm data location and expected modality before doing anything
- BIDS compliance is the target; note deviations but do not block progress for minor issues
- Summarize what was found, what passed, and what needs fixing before moving on

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Workflow hints

- Save `data-inventory.md` to `.neuroflow/data/` listing datasets, paths, and BIDS status
- Conversion scripts and outputs go to `output_path`, not inside `.neuroflow/`
- Log any structural data issues that affect analysis choices downstream in `.neuroflow/reasoning/data.json`
