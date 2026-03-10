---
name: neuroflow-core
description: Core rules and lifecycle for all neuroflow commands and agents. Read this whenever running any neuroflow command to understand the .neuroflow/ folder structure and the required behaviour at the start and end of every command.
---

# neuroflow-core

Defines the shared structure and lifecycle that every neuroflow command and agent must follow.

## .neuroflow/ folder

`.neuroflow/` is project memory — plans, reports, configs, indexes, decisions, QC notes. It lives at the root of the user's project repo.

### Root files

| File | Purpose |
|---|---|
| `project_config.md` | Short dense overview: current phase(s), research question, modality, tools, key decisions, output paths. Must include `plugin_version` — always mirrors the neuroflow plugin version from `plugin.json`. Read this first. Update when phase changes. |
| `flow.md` | Index of all subfolders: one row per folder with name, description, date of last change. |
| `decisions.md` | Legacy markdown decisions log. New decisions go to `.neuroflow/reasoning/{phase}.json`. |
| `linked_flows.md` | Paths to other `.neuroflow/` folders (sibling projects, shared datasets, parent projects). |
| `sentinel.md` | Sentinel's last audit report. If all clear: last run date + "all clear". |
| `team.md` | Project members, roles, contacts. |
| `timeline.md` | Milestones and deadlines. |

### Root folders

| Folder | Purpose |
|---|---|
| `sessions/` | One `.md` per day (`YYYY-MM-DD.md`). Local only — add to `.gitignore`. |
| `reasoning/` | Structured per-phase decision logs (JSON files with `statement`, `source`, `reasoning`). Has its own `flow.md`. Created on first use. |
| `ethics/` | IRB documents, consent forms. |
| `preregistration/` | Pre-registration documents (OSF, AsPredicted). |
| `finance/` | Grant documents, expense tracking. |
| `{phase}/` | One subfolder per pipeline command (e.g. `ideation/`, `experiment/`, `data/`). Each has its own `flow.md` and at least one `.md` memory file written by the command. |

**Rule: only command names may be used as phase subfolder names.** Skills must never create their own named subfolders inside `.neuroflow/`. All skill memory must be written to the active command's phase subfolder (`.neuroflow/{phase}/`). Creating a subfolder named after a skill (e.g. `.neuroflow/review-neuro/`) is a structural error.

### flow.md format

Every subfolder must contain a `flow.md` with this format:

```
| File / Folder | Description | Last changed |
|---|---|---|
| filename.md | One sentence. | YYYY-MM-DD |
```

Phase subfolders that produce external outputs must also include an `output_path` line at the top:

```
output_path: ../scripts/analysis
| File / Folder | Description | Last changed |
|---|---|---|
| analysis-plan.md | Analysis plan and statistical approach. | YYYY-MM-DD |
```

`output_path` is relative to the repo root and points to where this phase writes code, results, figures, or manuscripts. Set by `/start` — never write it manually unless `/start` was not run.

---

## Memory vs outputs

**`.neuroflow/` holds memory only.** Never write code, computed results, figures, or manuscripts inside `.neuroflow/`. All real outputs go to the phase `output_path`.

| What it is | Where it goes |
|---|---|
| Plans, QC reports, summaries, configs | `.neuroflow/{phase}/` |
| Analysis scripts, preprocessing code, tool code | `output_path` |
| Computed results, figures, tables | `output_path` |
| Manuscript drafts, grant documents | `output_path` |
| Paradigm scripts | `output_path` |

Default output paths (used when the repo has no existing structure):

| Phase | Default output_path |
|---|---|
| `experiment` | `paradigm/` |
| `tool-build` / `tool-validate` | `tools/` |
| `data-preprocess` | `scripts/preprocessing/` |
| `data-analyze` | `scripts/analysis/` (code) + `results/` (outputs) + `figures/` |
| `paper-write` | `manuscript/` |
| `paper-review` | `manuscript/review/` |
| `grant-proposal` | `grant/` |

---

## Command lifecycle

Every command must follow this order:

**At start:**
1. Read `.neuroflow/project_config.md`
2. Read `.neuroflow/flow.md`
3. If the command has a phase subfolder: read `.neuroflow/{phase}/flow.md`
4. If the phase has an `output_path` in its `flow.md`: note it — external outputs go there

**At end:**
1. Write external outputs (code, results, figures, manuscripts) to `output_path` — not inside `.neuroflow/`
2. Write at least one `.md` memory file to `.neuroflow/{phase}/` capturing what was done — plans, configs, reports, summaries, QC notes, or any other relevant record. Format is free; use whatever structure fits the content. Every `.md` file written to the subfolder must be listed in `.neuroflow/{phase}/flow.md`.
3. Append to `.neuroflow/sessions/YYYY-MM-DD.md` — what was done, decisions made, open items
4. If a significant decision was made during the session, append a new JSON object to `.neuroflow/reasoning/{phase}.json` (use `general.json` for project-level decisions). Each object must have exactly three fields:
   - `"statement"` — what was decided (one clear sentence)
   - `"source"` — where the decision originated (e.g. `"command:paper-write | 2026-03-10"`)
   - `"reasoning"` — why this choice was made over alternatives
5. Update `.neuroflow/{phase}/flow.md` if new files were created in the phase subfolder
6. Update `.neuroflow/flow.md` if new subfolders were created
7. Update `.neuroflow/project_config.md` if the active phase changed
8. Update `.claude/CLAUDE.md` if the active phase changed

**What counts as a significant decision:**
- Analysis approach chosen (e.g. reference scheme, epoch length, statistical test)
- Paradigm or design choice (e.g. block vs event-related, stimulus duration)
- Deviation from a pre-registered plan
- Tool or library selected when alternatives were considered
- Phase change or scope change
- Any choice the user explicitly flags as a decision

Do not log routine actions (saving files, running scripts, fixing bugs) — only choices that affect the scientific or technical direction of the project.

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
