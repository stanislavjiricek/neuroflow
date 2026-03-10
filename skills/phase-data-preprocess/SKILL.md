---
name: phase-data-preprocess
description: Phase guidance for the neuroflow /data-preprocess command. Loaded automatically when /data-preprocess is invoked to orient agent behavior, relevant skills, and workflow hints for the data-preprocess phase.
---

# phase-data-preprocess

The data-preprocess phase filters, cleans, epochs, and quality-checks raw data to produce analysis-ready datasets.

## Approach

- Read `.neuroflow/data/` inventory first — understand the dataset before choosing methods
- Confirm the modality; preprocessing steps differ significantly between EEG, fMRI, ECG, eye-tracking
- Document every parameter choice (filter cutoffs, epoch windows, rejection thresholds) before running
- QC plots and rejection summaries are required outputs — not optional

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Workflow hints

- All scripts and processed data go to `output_path` (`scripts/preprocessing/`), not inside `.neuroflow/`
- Save `preprocess-config.md` to `.neuroflow/data-preprocess/` with the full parameter set used
- Log any deviation from a pre-registered preprocessing plan in `decisions.md`
