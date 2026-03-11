---
title: /search
---

# `/neuroflow:search`

**Lightweight scoped search across project memory or the codebase.**

`/search` lets you quickly find information without leaving your current workflow. It uses `flow.md` files as a fast index so it only reads what is relevant — no full directory scans.

---

## Syntax

```
/search <tag>:<query>
```

### Tags

| Tag | Scope |
|---|---|
| `memory` | Search inside `.neuroflow/` only — plans, summaries, session logs, analysis notes, reasoning |
| `project` | Search the project codebase outside `.neuroflow/` — scripts, notebooks, results, config files |

If no tag is supplied, the search defaults to `memory` and notifies you.

---

## When to use it

- You want to find where a decision was recorded without reading every file
- You remember working on something (e.g. "ICA artifact rejection") and want to locate the relevant notes quickly
- You want to find a script or notebook somewhere in the codebase
- Another agent or command needs a quick answer about what the project memory contains

---

## Examples

```
/neuroflow:search memory:ICA artifact rejection
```

```
🔍 Search: "ICA artifact rejection" [scope: memory]

Found in:
  • .neuroflow/data-preprocess/preprocessing-notes.md — ICA run and artifact components manually rejected
  • .neuroflow/reasoning/data-preprocess.json — decision: kept 58/64 components after visual inspection

Summary: ICA artifact rejection was completed during the data-preprocess phase. Notes are in
preprocessing-notes.md; the reasoning log records the decision and the number of components kept.
```

---

```
/neuroflow:search project:bandpass filter
```

```
🔍 Search: "bandpass filter" [scope: project]

Found in:
  • scripts/preprocessing/preprocess_eeg.py — apply_bandpass() function, 1–40 Hz
  • scripts/preprocessing/config.py — bandpass_low=1, bandpass_high=40 defined here

Summary: The bandpass filter is implemented in preprocess_eeg.py and its parameters are set in config.py.
```

---

## How it works

1. Parses the tag and query from your invocation
2. Reads `flow.md` as a fast index — no full directory scans
3. For `memory`: navigates `.neuroflow/` phase subfolders guided by the index
4. For `project`: uses `output_path` entries from `flow.md` to locate relevant directories, then searches there
5. Returns a compact summary: matched files with one-line reasons + a 2–4 sentence synthesis

This command is **read-only** — it never writes to `.neuroflow/` or any project file.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md` (and phase sub-`flow.md` files as needed) |
| Writes | *(nothing — read-only command)* |

---

## Related commands

- [`/neuroflow`](neuroflow.md) — full project status
- [`/phase`](phase.md) — show current phase and switch
- [`/sentinel`](sentinel.md) — full audit of `.neuroflow/` for consistency issues
