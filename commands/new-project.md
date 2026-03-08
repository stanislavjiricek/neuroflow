---
description: Scaffold a new neuroscience research project with BIDS directory structure, team configuration, and project documentation. Creates all necessary folders and files for a reproducible study.
argument-hint: [project-name] [modality]
allowed-tools: [Bash, Write, Read]
---

# /new-project — Initialize New Neuroscience Project

You are helping a neuroscience team set up a new research project. The user has invoked this command with:

**Arguments**: $ARGUMENTS

## Your Task

Create a complete, BIDS-compliant project scaffold for a new neuroscience study.

### Step 1: Gather Information

If arguments were not provided or are incomplete, ask the researcher:

1. **Project name** (will become the directory name, use kebab-case)
2. **Primary modality**: EEG / iEEG / fMRI / Eye tracking / Multimodal
3. **Paradigm type**: ERP / oscillatory / resting-state / BCI / other
4. **Programming language**: Python / MATLAB
5. **Target journal** (optional)

### Step 2: Create Project Structure

Create the following directory structure:

```
{project-name}/
├── dataset_description.json     ← BIDS required
├── participants.tsv              ← BIDS required
├── participants.json
├── README.md
├── CHANGES.md
├── .gitignore
├── config/
│   ├── team.json                ← filled with user info
│   └── recording_params.json
├── paradigm/
│   ├── main.py                  ← PsychoPy main script placeholder
│   ├── config.py
│   └── README.md
├── analysis/
│   ├── 01_preprocessing.py
│   ├── 02_analysis.py
│   └── README.md
├── sourcedata/                  ← raw data before BIDS conversion
├── derivatives/                 ← processed outputs
│   └── preprocessing/
└── sub-01/                      ← example BIDS subject folder
    └── {modality}/
```

### Step 3: Create Key Files

**`dataset_description.json`**:
```json
{
  "Name": "{project-name}",
  "BIDSVersion": "1.9.0",
  "License": "CC0",
  "Authors": [],
  "ReferencesAndLinks": []
}
```

**`participants.tsv`**:
```
participant_id	age	sex	handedness
sub-01
```

**`config/team.json`**: Fill with values from the researcher's answers.

**`analysis/01_preprocessing.py`**: Add stub preprocessing script with imports (mne, pandas, numpy) and TODO comments.

### Step 4: Confirm and Report

Print a summary of:
- Project location created
- Number of files/folders created
- Next steps for the researcher (what to do next)
- Key commands to run (`/paradigm` to create paradigm, `/interview` to scope the study)
