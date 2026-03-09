---
name: data-preprocess
description: Run a preprocessing pipeline on ingested data — filtering, ICA, epoch creation, artifact rejection, and QC.
phase: data-preprocess
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/data/flow.md
  - .neuroflow/data-preprocess/flow.md
writes:
  - .neuroflow/data-preprocess/
  - .neuroflow/data-preprocess/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /data-preprocess

Follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/data-preprocess/flow.md` before starting. Also check `.neuroflow/data/flow.md` to understand what data is available.

## What this command does

Builds and runs a preprocessing pipeline on the ingested data.

Ask:
1. What modality? (EEG, iEEG, fMRI, other)
2. What is the path to the data?
3. What preprocessing steps are needed? Or should it be a standard pipeline for the modality?

---

## Standard EEG pipeline

1. Load data (MNE Raw)
2. Filter (bandpass, notch)
3. Re-reference (average, linked mastoids, or REST)
4. Mark bad channels
5. ICA — fit, inspect components, remove artifacts (EOG, ECG)
6. Interpolate bad channels
7. Epoch around events
8. Baseline correction
9. Reject bad epochs
10. Save preprocessed epochs

Document the pipeline parameters in `preprocess-config.md` in `.neuroflow/data-preprocess/`. Write the pipeline as a reusable script in the project repo.

---

## At end

- Save `preprocess-report.md` — parameters used, bad channels, ICA components removed, epoch rejection rate, subject-level QC notes
- Update `.neuroflow/data-preprocess/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `project_config.md` if phase changed
