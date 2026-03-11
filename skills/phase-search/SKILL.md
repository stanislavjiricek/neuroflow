---
name: phase-search
description: Lightweight search skill for the /search command. Instructs the agent to use flow.md files as a fast index, scope the search by tag (project or memory), and return a concise summary to the main agent.
---

# phase-search

Fast, minimal search of the project. Use this skill when running `/search`. Do not do deep exploration — read the index first, search only what is needed, and return a brief summary.

---

## Tag-based scoping

Every search invocation carries a scope tag. Recognise these two tags:

| Tag | Scope | What to search |
|---|---|---|
| `memory` | Inside `.neuroflow/` only | All `.neuroflow/` files: `project_config.md`, `flow.md`, phase subfolders, sessions, reasoning |
| `project` | Outside `.neuroflow/` | Source files, scripts, notebooks, data files, config files in the repo root and subdirectories — everything except `.neuroflow/` |

If no tag is provided, default to `memory` and inform the user.

---

## Search strategy — use flow.md as the index

### For `memory` searches

1. Read `.neuroflow/flow.md` — this is the root index. Note which phase subfolders exist and their descriptions.
2. For each phase subfolder relevant to the query, read its `flow.md` — this lists the files and their one-line descriptions.
3. If the query term appears in a description or filename in the index, open that specific file for a targeted read.
4. Only read the full content of files that the index points to as relevant — do not read every file.

### For `project` searches

1. Read `.neuroflow/flow.md` first — it lists `output_path` values for each phase, pointing to where scripts, results, and manuscripts live.
2. Use the `output_path` entries to quickly locate the relevant directories.
3. Search those directories for files matching the query (by filename or targeted content search).
4. Do not recurse into directories that are clearly unrelated.

---

## Response format

Return a compact summary, not a full report. Structure:

```
🔍 Search: "<query>" [scope: memory | project]

Found in:
  • <file-path> — <one-line reason why it matches>
  • <file-path> — <one-line reason why it matches>

Summary: <2–4 sentences synthesising what was found>
```

If nothing is found:

```
🔍 Search: "<query>" [scope: memory | project]

No matches found. Checked: <list of flow.md files consulted>

Suggestion: <one-line suggestion — try a different tag, different term, or check if the phase has been started>
```

---

## Rules

- **Be fast**: consult the flow.md index before opening any other file. Never open a file that the index does not point to as relevant.
- **Be brief**: the summary is for the main agent, not the user. Keep it to the essential finding.
- **Do not modify anything**: this skill is read-only. Never write to `.neuroflow/` or any project file.
- **Do not recurse blindly**: if the query matches nothing in the flow.md indices, report not-found rather than scanning all files.
