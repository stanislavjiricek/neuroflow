---
name: neuroflow-core
description: Core rules and lifecycle for all neuroflow commands and agents. Read this whenever running any neuroflow command to understand the .neuroflow/ folder structure and the required behaviour at the start and end of every command.
---

# neuroflow-core

Defines the shared structure and lifecycle that every neuroflow command and agent must follow.

## .neuroflow/ folder

`.neuroflow/` is project memory — plans, reports, configs, indexes, reasoning logs, QC notes. It lives at the root of the user's project repo.

**Rule: `.neuroflow/` is workflow state only.** Never place deliverables, reports, meta-documents, improvement notes, or any non-workflow output files inside `.neuroflow/`. If unsure where something belongs, default to the project root or `report/`.

### Root files

| File | Purpose |
|---|---|
| `project_config.md` | Short dense overview: current phase(s), research question, modality, tools, output paths. Must include `plugin_version` — always mirrors the neuroflow plugin version from `plugin.json`. Read this first. Update when phase changes. |
| `flow.md` | Index of all subfolders: one row per folder with name, description, date of last change. |
| `linked_flows.md` | Paths to other `.neuroflow/` folders (sibling projects, shared datasets, parent projects). |
| `sentinel.md` | Sentinel's last audit report. If all clear: last run date + "all clear". |
| `team.md` | Project members, roles, contacts. |
| `timeline.md` | Milestones and deadlines. |
| `integrations.json` | MCP integration credentials (PubMed email, Miro token). Written by `/setup`. **Never commit** — add to `.gitignore`. |

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

`output_path` is relative to the repo root and points to where this phase writes code, results, figures, or manuscripts. Set by `/neuroflow` — never write it manually unless `/neuroflow` was not run.

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

**Utility scripts vs project deliverables:**

| Script type | Where it goes |
|---|---|
| Project deliverable (analysis pipeline, preprocessing script, paradigm) | `output_path` or `scripts/` |
| Utility/helper script that produces an output (e.g. markdown→docx converter, report renderer) | `.neuroflow/{phase}/tools/` |

Never place utility scripts in the project root. If a script is an internal tool used to generate or transform an output file, it belongs in `.neuroflow/{phase}/tools/` — not alongside the project's main code.

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
3. Append to `.neuroflow/sessions/YYYY-MM-DD.md` — do this at **each meaningful milestone** during the session (new output file created, significant correction made, new tool or approach used), not only once at the start or end
4. Write to `.neuroflow/reasoning/{phase}.json` at natural decision points **during** the session — not only at the end. Use `general.json` for project-level decisions. Append a new JSON object with exactly three fields:
   - `"statement"` — what was decided (one clear sentence)
   - `"source"` — where the decision originated (e.g. `"command:paper-write | 2026-03-10"`)
   - `"reasoning"` — why this choice was made over alternatives
5. Update `.neuroflow/{phase}/flow.md` **immediately** when each new file is created in the phase subfolder — treat it as a live index, not a one-time snapshot taken at the end
6. Update `.neuroflow/flow.md` if new subfolders were created
7. Update `.neuroflow/project_config.md` if the active phase changed
8. Update `.claude/CLAUDE.md` if the active phase changed
9. **Phase transition check:** if the outputs produced during this session clearly belong to a different (later) phase than the active phase in `project_config.md`, prompt the user: *"The work produced looks like [phase] outputs. Should I update the active phase in project_config.md?"* Do not silently leave the phase wrong.

**What counts as a significant decision:**
- Analysis approach chosen (e.g. reference scheme, epoch length, statistical test)
- Paradigm or design choice (e.g. block vs event-related, stimulus duration)
- Deviation from a pre-registered plan
- Tool or library selected when alternatives were considered
- Phase change or scope change
- Any choice the user explicitly flags as a decision

Do not log routine actions (saving files, running scripts, fixing bugs) — only choices that affect the scientific or technical direction of the project.

---

## End-of-command checklist

Run through these before closing any command:

- [ ] Appended to `sessions/YYYY-MM-DD.md` at each meaningful milestone
- [ ] Wrote decisions to `reasoning/{phase}.json` at natural decision points during the session
- [ ] Updated `{phase}/flow.md` immediately as each new file was created
- [ ] Updated root `flow.md` if new folders were created
- [ ] Checked that active phase in `project_config.md` is still accurate — if not, asked user
- [ ] Confirmed no utility scripts were placed in the project root
- [ ] Confirmed no non-workflow files were placed in `.neuroflow/`
- [ ] Verified `.claude/CLAUDE.md` exists in the **project root** (created if missing)

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
