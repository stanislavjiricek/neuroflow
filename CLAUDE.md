# neuroflow — contributor guide

neuroflow is a **Claude Code plugin, and only that**, for agentic neuroscience research: slash commands, skills and agents that carry a project from hypothesis to publication, plus an optional mod layer (a Claude Code hooks module). This file is for developing the plugin itself with Claude Code. To use neuroflow in a research project, install it and run `/neuroflow:neuroflow` there (see `docs/`).

---

## Repository layout

```
neuroflow/
├── commands/              ← slash commands, one .md per command
├── skills/                ← one folder per skill, each with a SKILL.md (name = folder name)
│   ├── neuroflow-core/    ← the normative core: project memory contract, shared formats, lifecycle, rule markers
│   │   └── scripts/       ← scaffold.py (/neuroflow), migrate.py (/neuroflow:migrate)
│   ├── neuroflow-develop/ ← development guide: overlap audit, adding files, release workflow
│   └── phase-{name}/      ← guidance skill for each command
├── agents/                ← specialist sub-agent definitions
├── hooks/                 ← hooks.json (shell hooks) and the mod layer
├── docs/                  ← MkDocs site; docs/commands/<name>.md for every command
├── tests/scripts/         ← stdlib unittest tests for the skill scripts
├── scripts/automation/    ← CI and maintenance scripts (validate_pr.py, sentinel_check.py, …)
└── .claude-plugin/        ← plugin.json (version) and marketplace.json
```

---

## Ground rules

| Rule | What it means |
|---|---|
| **Claude Code only** | No instructions, mirrors or promises for other agent hosts. A user project gets one static neuroflow block in its own `.claude/CLAUDE.md` — never in `~/.claude/CLAUDE.md`, and no `AGENTS.md` or `.github/copilot-instructions.md` mirrors. |
| **Prose is the source of truth** | Every duty is stated in skill or command prose and works without the mod (mod off, hooks disabled, older builds, headless `-p`). The mod adds speed, visibility and guard-rails; it enforces only rules marked `<!-- nf-rule: ID -->` and never rewrites skill text. |
| **Contracts live in neuroflow-core** | `project_config.md` frontmatter, the personal layer (`~/.neuroflow/user.yaml`), reasoning logs (JSON Lines), integrity markers, merge safety, sharing tiers, lifecycle profiles, rule markers, mod-written lines. Other files point to the section by name; never restate or fork a format. |
| **English and neutral** | All repo content is in English. No country-, institution- or vendor-local names; examples use placeholders ("University of Example", "my-gateway"). Signals and aliases are detected by the model in any language — never through English-only keyword lists. |
| **Conservative** | Extend before adding: a new command, skill or agent only when nothing existing covers more than half of its scope (overlap audit in `neuroflow-develop`). |

---

## Conventions

- **Commands** — frontmatter `name` (= filename), `description`, `phase` (canonical list: neuroflow-core → Phase taxonomy), `reads`, `writes`, `lifecycle` (`full` / `light` / `quiet`), and optional `requires` / `produces` / `next`. Every command has a page at `docs/commands/<name>.md`; a new command also needs a `mkdocs.yml` nav entry, a node in `docs/javascripts/mind.js` and a row in the README commands table.
- **Skills** — `skills/<folder>/SKILL.md`, frontmatter `name` equal to the folder name. Installed skills are namespaced `neuroflow:<folder>`. A skill writes only into the active command's phase folder, never into a folder named after itself.
- **Session lines** — one format everywhere: `## HH:MM — [phase] what was accomplished`.
- **Fixed-choice questions** — `AskUserQuestion` (2–4 options, recommended first; the tool adds "Other").
- **Scripts** — `skills/<owner-skill>/scripts/<name>.py`: Python 3.10+, stdlib first, `argparse` with `--help` and `--json`, exit codes `0` clean / `1` findings / `2` usage or runtime error. One executable home per check. Prose that uses a script says exactly how to run it and what to do with each exit code.
- **Tests** — `tests/scripts/test_<name>.py`, stdlib `unittest`, self-contained (temporary folders, no network); import scripts by path with `importlib.util.spec_from_file_location`.
- **Hooks** — shell hook commands end with `; true` or `|| true`, so a failing hook never blocks the user.

---

## How the plugin behaves in a user project

- **Project memory** is `.neuroflow/` at the user's project root; commands find it by walking up from the working directory. Per-person preferences and consents live in `~/.neuroflow/user.yaml`, never in the project.
- **Lifecycle** — every command reads `project_config.md` and `flow.md` first, then follows its `lifecycle` profile: session milestones, decision entries in `reasoning/{phase}.jsonl`, `flow.md` updates (`quiet` commands such as `/idk` write nothing).
- **Personality modes** — `teacher`, `executor`, `critic`; switched only by an explicit `mode: <name>` or `--mode <name>` prefix, with personal and team defaults.
- **Passive issue monitoring** — the model notices problem signals in any language and logs a paraphrased line to `.neuroflow/fails/`; with the person's opt-in it drafts an issue and opens it only after their yes.

neuroflow-core (`skills/neuroflow-core/SKILL.md`) is the authoritative text for all of this.

---

## Before you open a PR

```bash
python scripts/automation/validate_pr.py
python -m unittest discover -s tests -p "test_*.py" -v
```

Substantive changes need a version bump in `.claude-plugin/plugin.json`, kept in sync with `marketplace.json` and `mkdocs.yml` — follow the release workflow in the `neuroflow-develop` skill.

---

## This repo's own memory

`.neuroflow/` at the repo root is the maintainer's project memory for the plugin (development decisions, sentinel reports). It is not a template; do not edit it as part of a feature change.
