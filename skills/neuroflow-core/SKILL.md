---
name: neuroflow-core
description: Core rules and lifecycle for all neuroflow commands and agents. Read this whenever running any neuroflow command to understand the .neuroflow/ folder structure and the required behaviour at the start and end of every command.
---

# neuroflow-core

Defines the shared structure and lifecycle that every neuroflow command and agent must follow.

## .neuroflow/ folder

All neuroflow output lives in `.neuroflow/` at the root of the user's project repo. Never write neuroflow output anywhere else.

### Root files

| File | Purpose |
|---|---|
| `project_config.md` | Short dense overview: current phase(s), research question, modality, tools, key decisions. Read this first. Update when phase changes. |
| `flow.md` | Index of all subfolders: one row per folder with name, description, date of last change. |
| `decisions.md` | Log of key scientific and technical decisions with date and rationale. Git-tracked. |
| `linked_flows.md` | Paths to other `.neuroflow/` folders (sibling projects, shared datasets, parent projects). |
| `sentinel.md` | Sentinel's last audit report. If all clear: last run date + "all clear". |
| `team.md` | Project members, roles, contacts. |
| `timeline.md` | Milestones and deadlines. |

### Root folders

| Folder | Purpose |
|---|---|
| `sessions/` | One `.md` per day (`YYYY-MM-DD.md`). Local only — add to `.gitignore`. |
| `references/` | Papers, URLs, dataset paths used in the project. Has its own `flow.md`. |
| `ethics/` | IRB documents, consent forms. |
| `preregistration/` | Pre-registration documents (OSF, AsPredicted). |
| `finance/` | Grant documents, expense tracking. |
| `{phase}/` | One subfolder per pipeline command (e.g. `ideation/`, `experiment/`, `data/`). Each has its own `flow.md`. |

### flow.md format

Every subfolder must contain a `flow.md` with this format:

```
| File / Folder | Description | Last changed |
|---|---|---|
| filename.md | One sentence. | YYYY-MM-DD |
```

## Command lifecycle

Every command must follow this order:

**At start:**
1. Read `.neuroflow/project_config.md`
2. Read `.neuroflow/flow.md`
3. If the command has a phase subfolder: read `.neuroflow/{phase}/flow.md`

**At end:**
1. Append to `.neuroflow/sessions/YYYY-MM-DD.md` — what was done, decisions made, open items
2. Update `.neuroflow/{phase}/flow.md` if new files were created in the phase subfolder
3. Update `.neuroflow/flow.md` if new subfolders were created
4. Update `.neuroflow/project_config.md` if the active phase changed
5. Update `.claude/CLAUDE.md` if the active phase changed

## Command frontmatter standard

Every command file must declare these fields:

```yaml
---
name: command-name
description: one-line description
phase: <phase-name>        # matches command name, or "utility" for /sentinel and /phase
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/{phase}/flow.md    # only if command has a phase subfolder
writes:
  - .neuroflow/sessions/YYYY-MM-DD.md
  - .neuroflow/{phase}/           # only if command has a phase subfolder
  - .neuroflow/{phase}/flow.md    # only if command has a phase subfolder
---
```

Valid phase values: `ideation`, `grant-proposal`, `experiment`, `tool-build`, `tool-validate`, `data`, `data-preprocess`, `data-analyze`, `paper-write`, `paper-review`, `notes`, `write-report`, `utility`
