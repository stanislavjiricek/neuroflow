---
name: phase-data
description: Phase guidance for the neuroflow /data command. Loaded automatically when /data is invoked to orient agent behavior, relevant skills, and workflow hints for the data intake phase.
user-invocable: false
---

# phase-data

The data phase locates raw data, validates BIDS structure, and runs conversion scripts to get data ready for preprocessing.

## Approach

- Follow the three-step sequence in order: inventory → validate → convert — do not skip ahead
- Confirm data location and expected modality before doing anything
- For your own participants' data, check the ethics gate and `ai_processing` first (`/data` → Before you start)
- Raw folders (`raw_roots`) are read-only — the rule and the BrainVision renaming trap are in `/data` step 3
- BIDS compliance is the target; note deviations but do not block progress for minor issues
- Summarize what was found, what passed, and what needs fixing before moving on

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules
- `neuroflow:bids` — invoke whenever BIDS structure, validation, conversion, or sidecar metadata is relevant; provides full entity ordering, required files per modality, tool usage (bids-validator, pybids, MNE-BIDS), and conversion examples

## Workflow hints

- Save `data-inventory.md` to `.neuroflow/data/` listing datasets, paths, storage location type, and BIDS status
- Conversion scripts and outputs go to `output_path`, not inside `.neuroflow/`
- Log any structural data issues that affect analysis choices downstream in `.neuroflow/reasoning/data.jsonl`

## Scripts

- `scripts/erasure_sweep.py` — finds every place a participant ID reached (project files, git history, Claude Code's local transcripts and caches, `~/.neuroflow/`) and reports paths and counts; never deletes and never prints contents. Used by `/ethics --erase`; the person runs it in their own terminal: `python <skill base dir>/scripts/erasure_sweep.py --id sub-07`. Exit 0 = nothing found, 1 = occurrences found, 2 = usage error.

## Slash command

`/neuroflow:data` — runs this workflow as a slash command.
