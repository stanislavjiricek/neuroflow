---
description: Launch an analysis pipeline for a neuroscience dataset. Guides through preprocessing, feature extraction, and statistical analysis based on the detected modality and study type.
argument-hint: [data-path] [modality]
allowed-tools: [Read, Write, Bash, Glob]
---

# /analyze — Launch Analysis Pipeline

You are setting up and running a neuroscience data analysis pipeline.

**Arguments**: $ARGUMENTS

## Your Task

Analyze the dataset at the specified path, or the current directory if no path is provided.

## Step 1: Detect Dataset

1. Check if argument provides a path; otherwise use the current directory
2. Look for BIDS structure:
   - `dataset_description.json` → BIDS dataset
   - `*.fif`, `*.bdf`, `*.edf` → raw EEG files
   - `*.nii.gz` → fMRI
   - `derivatives/` → already preprocessed
3. If `config/team.json` exists, read modality and analysis tools preferences
4. List detected subjects and sessions

Report findings to the user:
> "I found a BIDS dataset with N subjects. Modality detected: EEG. Preferred tools: MNE-Python. Should I proceed with the standard pipeline for [modality]?"

## Step 2: Choose Pipeline

Ask if not clear:
1. **What analysis**: ERP / time-frequency / connectivity / classification / fMRI GLM / resting-state
2. **Preprocessing needed**: yes / no (already done)
3. **Statistical analysis**: permutation test / t-test / ANOVA / correlation
4. **Output needed**: figures / stats table / paper-ready numbers

## Step 3: Generate Analysis Script

Based on detected modality and requested analysis, generate a Python script at `analysis/run_analysis.py` with:

**For EEG ERP analysis:**
- Load all subjects from BIDS
- Preprocessing (filter, ICA, epoch, baseline)
- ERP computation per condition
- Grand average computation
- Time window feature extraction (per hypothesis)
- Permutation t-test between conditions
- Figure generation (ERP waveform, topography)
- Save results table (CSV with amplitude/latency per subject per condition)

**For EEG Time-Frequency:**
- Morlet wavelet transform
- Band power extraction
- ERD/ERS computation
- Permutation cluster test across time-frequency space

**For fMRI:**
- Load fMRIPrep outputs
- Build first-level GLM
- Compute contrasts
- Run second-level group analysis
- Threshold and cluster

**For Classification:**
- Cross-validation pipeline (scikit-learn)
- Temporal generalization decoder
- Permutation test for chance level

## Step 4: Run and Report

After generating the script:
1. Show the user the script structure
2. Ask: "Should I run this script now, or do you want to review it first?"
3. If approved, run: `python analysis/run_analysis.py`
4. Monitor output and report results summary
5. List all output files created

Suggest next step: `/write-paper` to incorporate results into a manuscript.
