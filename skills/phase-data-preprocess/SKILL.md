---
name: phase-data-preprocess
description: Phase guidance for the neuroflow /data-preprocess command. Loaded automatically when /data-preprocess is invoked to orient agent behavior, relevant skills, and workflow hints for the data-preprocess phase.
user-invocable: false
---

# phase-data-preprocess

The data-preprocess phase filters, cleans, epochs, and quality-checks raw data to produce analysis-ready datasets.

## Approach

- Read `.neuroflow/data/` inventory first — understand the dataset before choosing methods
- Confirm the modality; preprocessing steps differ significantly between EEG, fMRI, ECG, eye-tracking
- Document every parameter choice (filter cutoffs, epoch windows, rejection thresholds) before running
- Read the power-line frequency and sampling rate from `raw.info` (`line_freq`, `sfreq`) or the BIDS sidecars (`PowerLineFrequency`, `SamplingFrequency`); never hardcode 50/60 Hz or the sampling rate
- QC plots and rejection summaries are required outputs — not optional. QC numbers come from code (*QC JSON and the QC table*), never transcribed by hand
- A QC flag is a prompt to look, not an exclusion: exclude subjects or data only by criteria fixed before the outcome is known (preregistration, or `preprocess-config.md` written first), and log each exclusion decision

## QC JSON and the QC table

The pipeline writes one QC file per subject (and session or run) at the end of that subject — `sub-01_qc.json`, next to the preprocessed data (e.g. `derivatives/<pipeline>/qc/`):

```json
{"nf_qc": 1, "subject": "sub-01", "session": "ses-01", "task": "oddball",
 "metrics": {"n_channels": 64, "n_bad_channels": 3, "pct_bad_channels": 4.7, "n_ica_excluded": 2,
             "n_epochs": 240, "n_epochs_rejected": 31, "pct_epochs_rejected": 12.9},
 "details": {"bad_channels": ["Fp1", "T7", "O2"], "ica_excluded": [0, 3]},
 "notes": ""}
```

- `subject` is required; `session`, `task`, `run` are optional and form the row key with it
- `metrics` is flat: numbers or `null` only, percentages as 0–100. Use the names above where they apply (other modalities add their own, e.g. `mean_fd_mm`, `pct_volumes_censored`); lists and text go to `details` and `notes`
- One file per subject keeps reruns and parallel jobs from overwriting each other

Build the table: `python <skill base dir>/scripts/qc_table.py <qc folder> --markdown .neuroflow/data-preprocess/qc-table.md --csv <qc folder>/qc-table.csv --threshold "pct_bad_channels>20" --threshold "pct_epochs_rejected>25"`. Pass the preregistered or a-priori criteria as `--threshold` (without it, those two defaults apply as placeholders); `--robust-z 3.5` adds outlier flags (needs at least 5 subjects, skips metrics whose spread is zero).

| Exit | Meaning | Do |
|---|---|---|
| 0 | table built, nothing flagged | include it in `preprocess-report.md` |
| 1 | table built, rows flagged | look at each flagged subject (plots, logs); decide by the fixed criteria; log each decision in `reasoning/data-preprocess.jsonl` |
| 2 | malformed QC file or bad arguments | fix the listed file or the command; rerun |

## ICA decisions

- The person decides in MNE's own interactive views (`ica.plot_sources(raw)`, `ica.plot_components()` — click to mark), optionally with mne-icalabel probabilities; never decide from a text summary alone
- Record the decision per subject in a components file the pipeline reads — `sub-01_ica_components.tsv` next to the ICA output, columns `component`, `status` (`good`/`bad`), `status_description` (e.g. `blink`, `ECG`, `ICLabel eye 0.97`), `decided_by` (`person`/`auto`). The apply step excludes `status == bad` from this file — never from free text in `preprocess-config.md`
- The count goes into the QC JSON (`n_ica_excluded`); the rule used (e.g. "ICLabel eye or heart > 0.8, confirmed by inspection") is a reasoning entry

## Blind preprocessing (optional)

For decisions that group or condition knowledge could steer — bad channels, ICA, epoch rejection, subject exclusion. It blinds the person and the model alike.

1. `python <skill base dir>/scripts/blind_labels.py blind --bids-root <bids root> --out <coded copy, e.g. derivatives/blinded> --key <path outside the project> --participants-column group --plan .neuroflow/data-preprocess/preprocess-config.md --log .neuroflow/data-preprocess/blinding.md` (events column defaults to `trial_type`; add `--events-column` per further label column). The person picks the key path and keeps the key — never read, print or commit it
2. Exit 0: done. Exit 1: a remaining column still reveals the labels (named in the warning) — blind or `--drop-column` it and rerun with `--force` (the coded copy and the key are replaced together). Exit 2: nothing was written — fix the command
3. Preprocess with labels from the coded copy only. A loader that attaches the original events (e.g. `mne_bids.read_raw_bids`) gets its annotations replaced from the coded events file before anything prints them; leave the JSON sidecars (`participants.json`, `*_events.json`) closed while blinded
4. Unblind only after the preprocessing decisions are final and recorded: the person runs `blind_labels.py unblind --key <key> --input <coded table> --column trial_type --out <decoded table> --plan <same plan file> --log .neuroflow/data-preprocess/blinding.md`; exit 1 means the plan changed after blinding — say why in `preprocess-report.md`

Subject IDs are not recoded: anyone who knows which IDs belong to which group is not blind.

## Provenance, long runs and HPC

- Copy `<skill base dir>/../phase-data-analyze/scripts/nf_provenance.py` once into `scripts/preprocessing/`, commit it, and call it from the pipeline (`neuroflow:phase-data-analyze` → *Provenance*) — it writes `environment.md` and one run record per run next to the script
- Runs longer than ~10 minutes follow `<skill base dir>/../phase-brain-run/references/long-runs.md`; the registry is `.neuroflow/data-preprocess/runs.md`
<!-- nf-rule: LOGIN-NODE -->
- **Never preprocess on an HPC login node** (fMRIPrep, MNE over a cohort, anything longer than about a minute): submit a job or run inside an interactive one (`neuroflow:phase-brain-run` → *Long runs and HPC*)
- Notebooks: strip outputs before committing; their outputs are never the results of record (`neuroflow:phase-data-analyze` → *Notebooks*)

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules
- `neuroflow:bids` — invoke when loading BIDS-organized data; covers `BIDSLayout` querying, `mne_bids.read_raw_bids()`, sidecar metadata fields, and writing preprocessed derivatives back to BIDS

## Workflow hints

- All scripts and processed data go to `output_path` (`scripts/preprocessing/`), not inside `.neuroflow/`
- Save `preprocess-config.md` to `.neuroflow/data-preprocess/` with the full parameter set used
- Log any deviation from a pre-registered preprocessing plan in `.neuroflow/preregistration/deviations.md` (append-only) and in `.neuroflow/reasoning/data-preprocess.jsonl`
- `qc-table.md` (generated), `blinding.md` (append-only log, when blinding is used) and `runs.md` live in `.neuroflow/data-preprocess/` — list each in the phase `flow.md`

## Slash command

`/neuroflow:data-preprocess` — runs this workflow as a slash command.
