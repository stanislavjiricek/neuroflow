---
name: data
description: Data intake — locate data, validate BIDS structure, and run conversion scripts to get raw data ready for preprocessing.
phase: data
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/data/flow.md
writes:
  - .neuroflow/data/
  - .neuroflow/data/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /data

Follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/data/flow.md` before starting.

## What this command does

Takes raw recorded data and gets it ready for preprocessing. Three steps — work through them in order:

1. **Locate and inventory** — find the data, understand what is there
2. **Validate structure** — check BIDS compliance or document the current structure
3. **Convert** — run conversion scripts if needed (raw → BIDS, BrainVision → MNE, EDF → FIF, etc.)

---

## Steps

### 1 — Locate and inventory

Ask the user where the data is. Use Glob and Read to inspect the directory. Document:
- How many subjects / sessions / runs
- File formats present
- Whether it looks BIDS-compliant already

Save a `data-inventory.md` in `.neuroflow/data/`.

### 2 — Validate BIDS structure

Use the `neuroflow:bids-structure` skill to check naming conventions, required files, and sidecar JSONs. Document any violations.

If the data is not in BIDS format, ask whether the user wants to convert it or proceed as-is.

### 3 — Convert

Run or write conversion scripts as needed. Common cases:
- BrainVision (`.vhdr`/`.vmrk`/`.eeg`) → MNE Raw → FIF
- EDF → MNE Raw → FIF
- Raw folder → BIDS structure

Save conversion scripts in the project repo. Document the conversion in `data-intake.md` in `.neuroflow/data/`.

---

## At end

- Update `.neuroflow/data/flow.md`
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `project_config.md` if phase changed
