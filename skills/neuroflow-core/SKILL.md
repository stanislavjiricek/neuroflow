---
name: neuroflow-core
description: Core rules and lifecycle for all neuroflow commands and agents. Read this whenever running any neuroflow command to understand the .neuroflow/ folder structure and the required behaviour at the start and end of every command.
---

# neuroflow-core

Defines the shared structure and lifecycle that every neuroflow command and agent must follow.

## .neuroflow/ folder

`.neuroflow/` is project memory. It lives at the root of the user's project repo.

**Rule: `.neuroflow/` root contains only the files and folders explicitly listed in the tables below — nothing else.** Never place any file or folder directly in `.neuroflow/` unless it appears in the "Root files" or "Root folders" tables. All workflow content belongs in the appropriate phase subfolder (`.neuroflow/{phase}/`). External deliverables, polished reports, or any user-facing outputs go in the project root or `report/`.

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
| `fails/` | Dissatisfaction log — three fixed files: `core.md` (plugin behavior problems), `science.md` (scientific quality problems), `ux.md` (interaction quality problems). Created on first `/fails` run. |
| `output/` | Output log — one `.md` per export run recording scope, format, destination, and excluded files. Created on first `/output` run. |
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

**`.neuroflow/` holds memory and internal tooling only.** Never write project deliverables (analysis scripts, computed results, figures, or manuscripts) inside `.neuroflow/`. All project outputs go to the phase `output_path`. The one exception is utility/helper scripts that are internal tools used solely to generate or transform an output file — these belong in `.neuroflow/{phase}/tools/`.

| What it is | Where it goes |
|---|---|
| Plans, QC reports, summaries, configs | `.neuroflow/{phase}/` |
| Analysis scripts, preprocessing code, tool code | `output_path` (outside `.neuroflow/`) |
| Computed results, figures, tables | `output_path` (outside `.neuroflow/`) |
| Manuscript drafts, grant documents | `output_path` (outside `.neuroflow/`) |
| Paradigm scripts | `output_path` (outside `.neuroflow/`) |
| Utility/helper script (internal tool, e.g. markdown→docx converter) | `.neuroflow/{phase}/tools/` |

**Utility scripts vs project deliverables:**

| Script type | Where it goes |
|---|---|
| Project deliverable (analysis pipeline, preprocessing script, paradigm) | `output_path` or `scripts/` — always outside `.neuroflow/` |
| Utility/helper script that produces an output (e.g. markdown→docx converter, report renderer) | `.neuroflow/{phase}/tools/` |

Never place utility scripts in the project root. If a script is an internal tool used to generate or transform an output file, it belongs in `.neuroflow/{phase}/tools/` — not alongside the project's main code. Data analysis scripts are project deliverables and must always go to `output_path` (outside `.neuroflow/`).

Default output paths (used when the repo has no existing structure):

| Phase | Default output_path |
|---|---|
| `experiment` | `paradigm/` |
| `tool-build` / `tool-validate` | `tools/` |
| `data-preprocess` | `scripts/preprocessing/` |
| `data-analyze` | `scripts/analysis/` (code) + `results/` (outputs) + `figures/` |
| `paper` | `manuscript/` |
| `review` | `reviews/` |
| `grant-proposal` | `grant/` |

---

## Command lifecycle

Every command must follow this order:

**At start:**
1. Read `.neuroflow/project_config.md`
2. Read `.neuroflow/flow.md`
3. If the command has a phase subfolder: read `.neuroflow/{phase}/flow.md`
4. If the phase has an `output_path` in its `flow.md`: note it — external outputs go there
5. **If `.neuroflow/fails/` exists: read `core.md`, `science.md`, and `ux.md`.** These files record past dissatisfaction with plugin behavior, science quality, and interaction experience. Read them silently at the start of every command so that known problems stay in context and the same mistakes are not repeated.

**At end:**
1. Write external outputs (code, results, figures, manuscripts) to `output_path` — not inside `.neuroflow/`
2. Write at least one `.md` memory file to `.neuroflow/{phase}/` capturing what was done — plans, configs, reports, summaries, QC notes, or any other relevant record. Format is free; use whatever structure fits the content. Every `.md` file written to the subfolder must be listed in `.neuroflow/{phase}/flow.md`.
3. Append to `.neuroflow/sessions/YYYY-MM-DD.md` — do this at **each meaningful milestone** during the session (new output file created, significant correction made, new tool or approach used), not only once at the start or end
4. Write to `.neuroflow/reasoning/{phase}.json` at natural decision points **during** the session — not only at the end. Use `general.json` for project-level decisions. Append a new JSON object with exactly three fields:
   - `"statement"` — what was decided (one clear sentence)
   - `"source"` — where the decision originated (e.g. `"command:paper | 2026-03-10"`)
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

## When a skill is invoked without a slash command

If a phase skill is invoked by Claude directly — without the user running the corresponding slash command — run the full workflow as normal. Apply the full command lifecycle (read `project_config.md`, write to `.neuroflow/{phase}/`, update `flow.md`, log to `sessions/`, etc.).

At the end of the interaction, mention the slash command once:

> 💡 You can also run `/neuroflow:<command-name>` to start this workflow directly as a slash command next time.

Each phase skill declares its slash command in a `## Slash command` section. Use that to determine the correct command name.

---

## End-of-command checklist

Run through these before closing any command:

- [ ] Appended to `sessions/YYYY-MM-DD.md` at each meaningful milestone
- [ ] Wrote decisions to `reasoning/{phase}.json` at natural decision points during the session
- [ ] Updated `{phase}/flow.md` immediately as each new file was created
- [ ] Updated root `flow.md` if new folders were created
- [ ] Checked that active phase in `project_config.md` is still accurate — if not, asked user
- [ ] Confirmed no utility scripts were placed in the project root
- [ ] Confirmed no files or folders were placed directly in `.neuroflow/` unless they are listed in the "Root files" or "Root folders" tables in neuroflow-core
- [ ] Verified `.claude/CLAUDE.md` exists in the **project root** (created if missing)
- [ ] If invoked without a slash command: mention the slash command at the end

## Default agent behavior

These rules apply to every neuroflow command and agent at all times. They define how the agent communicates and what it does by default — not just what it knows.

### Scientific honesty

Be scientifically correct. Do not soften findings, overstate certainty, or make the work sound better than it is.

- If the sample size is too small, say so.
- If the statistical approach is questionable, say so.
- If the result is null, describe it as null — not "trending toward significance".
- If a method has known limitations, name them.

Do not sugar-coat. A researcher needs accurate information to make good decisions, not reassurance.

### Tone — dry English humor

Be dry. Not sarcastic, not performative, not forced. Think understated observation — the kind of humor that works precisely because it does not try to be funny.

- A deadpan comment about a 14-participant study being underpowered is fine. Exclamation marks and emoji are not.
- Understatement is the tool. Overstatement is not.
- One dry remark per interaction is plenty. More than that is effort, and effort kills it.
- When the stakes are high (clinical data, patient safety, ethics), keep it straight.

### Conservative by default — do not add new functionality

Follow neuroflow-core. Follow the active command. Do not extend, modify, or add new functionality beyond what the current command requires unless the user explicitly asks for it.

- If something is not broken, do not touch it.
- If a new feature seems useful, mention it — do not implement it unless asked.
- New skills, commands, agents, or hooks are only added when the user has requested them.
- When in doubt, do less.
## Behavioral flags

Behavioral flags are keywords that, when present anywhere in the user's prompt (as a word, phrase, or clear synonym), change how Claude behaves for the **entire duration of that command invocation**. Scan for these flags at the start of every command before taking any action.

| Flag | Aliases | Behavior |
|---|---|---|
| `nomistake` | `hardcode`, `no-mistake`, `no mistake` | **Aggressive evaluation loop.** Never stop at the first pass. After producing any output, self-critique it against the user's intent, fix any gaps, then repeat until the output meets a high-quality threshold or no further improvement is found. Report each iteration briefly: what changed and why. Use the most thorough available approach at every step. |
| `snowflake` | `careful`, `careful-mode`, `be careful`, `handle with care` | **Clarify-first mode.** Before acting on any ambiguous instruction, ask targeted clarifying questions. Confirm key assumptions explicitly. Proceed incrementally — complete one step, show it, and wait for approval before continuing. Flag any uncertainty before rather than after acting. Never assume; always ask. |

**Detection rules:**
- Flag detection is case-insensitive and substring-aware (`NOMISTAKE`, `NoMistake`, and `nomistake` all trigger the flag)
- Both flags may be active simultaneously if both keywords are present
- A flag stays active for the entire command session — it is not reset between steps
- If a flag is detected, announce it at the start: e.g. *"🔁 nomistake mode active — after producing any output I will self-critique and iterate until it meets a high-quality threshold."* or *"❄️ snowflake mode active — I will ask clarifying questions before acting on any ambiguous instruction and proceed step-by-step."*

---

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
  - .neuroflow/fails/core.md      # read if exists — past behavior problems
  - .neuroflow/fails/science.md   # read if exists — past science quality problems
  - .neuroflow/fails/ux.md        # read if exists — past UX problems
  - .neuroflow/{phase}/flow.md    # only if command has a phase subfolder
writes:
  - .neuroflow/sessions/YYYY-MM-DD.md
  - .neuroflow/{phase}/           # only if command has a phase subfolder
  - .neuroflow/{phase}/flow.md    # only if command has a phase subfolder
---
```

Valid phase values: `ideation`, `preregistration`, `grant-proposal`, `finance`, `experiment`, `tool-build`, `tool-validate`, `data`, `data-preprocess`, `data-analyze`, `paper`, `review`, `notes`, `write-report`, `brain-build`, `brain-optimize`, `brain-run`, `output`, `utility`
