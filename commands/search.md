---
name: search
description: Lightweight search across the project or neuroflow memory. Use a tag to scope the search — `memory` searches inside .neuroflow/ only, `project` searches the codebase outside .neuroflow/. Returns a fast summary of what was found.
phase: utility
tags:
  - memory
  - project
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
writes: []
---

# /search

Read the `neuroflow:phase-search` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` and `flow.md` if they exist.

---

## What this command does

Performs a lightweight, scoped search across either the project's neuroflow memory (`.neuroflow/`) or the broader project codebase. Uses `flow.md` files as a fast index to avoid reading every file. Returns a brief summary.

---

## Syntax

```
/search <tag>:<query>
```

**Tags:**

| Tag | Scope |
|---|---|
| `memory` | Search inside `.neuroflow/` only — plans, summaries, session logs, reasoning |
| `project` | Search the project codebase outside `.neuroflow/` — scripts, notebooks, results, config |

**Examples:**

```
/search memory:ICA artifact rejection
/search project:bandpass filter
/search memory:analysis plan
/search project:preprocessing pipeline
```

If no tag is supplied, default to `memory` and inform the user.

---

## Steps

### Step 1 — Parse the invocation

Extract the tag and query from the user's input:

- If the input matches `<tag>:<query>`, use the tag to determine scope and the rest as the search term.
- If no tag prefix is found, default scope to `memory` and tell the user: *"No tag specified — searching memory. Use `project:` to search the codebase."*

### Step 2 — Check for .neuroflow/

If `.neuroflow/` does not exist and the scope is `memory`, stop and tell the user to run `/neuroflow` first.

For `project` scope, `.neuroflow/` is optional — proceed if the working directory contains any project files.

### Step 3 — Run the search using the phase-search skill

Follow the `neuroflow:phase-search` skill instructions exactly:

- Read `flow.md` as the index first
- Search only what the index points to as relevant
- Do not open files that the index gives no reason to open

### Step 4 — Return the summary

Present the compact result format defined in the `phase-search` skill:

```
🔍 Search: "<query>" [scope: memory | project]

Found in:
  • <file-path> — <one-line reason why it matches>

Summary: <2–4 sentences>
```

Do not write anything to `.neuroflow/` or anywhere else — this command is read-only.
