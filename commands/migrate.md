---
name: migrate
description: Convert a neuroflow project to the current project-memory contract — project_config.md frontmatter, JSON Lines reasoning logs, merge-safe .gitattributes, local-only .gitignore lines and the static instruction block. Shows the plan first and writes only after you agree.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/reasoning/
  - .claude/CLAUDE.md
  - .gitattributes
  - .gitignore
  - ~/.neuroflow/user.yaml
  - ~/.claude/CLAUDE.md                   # report only
  - .github/copilot-instructions.md       # report only
  - AGENTS.md                             # report only
writes:
  - .neuroflow/project_config.md
  - .neuroflow/reasoning/
  - .neuroflow/sessions/YYYY-MM-DD.md
  - .claude/CLAUDE.md
  - .gitattributes
  - .gitignore
  - ~/.neuroflow/user.yaml                # personal fields, only after the person agrees
lifecycle: light
produces:
  - .neuroflow/project_config.md
next:
  - phase
  - git
---

# /migrate

Bring an older neuroflow project up to the current project-memory contract (`neuroflow:neuroflow-core` → **project_config.md — the config contract**, **Reasoning log**, **Merge safety**, **Sharing tiers**, **Project instruction block**). Nothing is written until the person has seen the plan and agreed.

Read the `neuroflow:neuroflow-core` skill first: the script ships in its `scripts/` folder, and Claude Code shows the skill's base directory when it loads.

---

## When to run it

- `/neuroflow`, `/phase` or another command reported a legacy `project_config.md` dialect (no `nf_schema` frontmatter)
- reasoning logs are still JSON arrays (`reasoning/*.json`)
- `.claude/CLAUDE.md` holds an older neuroflow block that names a phase
- after a plugin update, to check whether the project needs anything

---

## Step 1 — Dry run

```bash
python <neuroflow-core base dir>/scripts/migrate.py --root .
```

Use `python3` where `python` is not on the PATH. The script walks up to the project root, writes nothing, and prints the plan: a diff of `project_config.md`, the reasoning conversions, the `.gitattributes` / `.gitignore` lines to add, the instruction-block fix, the decisions it needs, personal fields, and report-only findings. Add `--json` when you need the plan as data.

| Exit code | Meaning | What to do |
|---|---|---|
| `0` | Already current, nothing to report | Say so and stop. |
| `1` | Findings | Continue with Step 2. |
| `2` | Refused or failed — `nf_schema` newer than this plugin knows, no project found, unreadable file, bad argument | Show the message and stop. A newer schema means: update the plugin — never edit the file by hand to get past it. |

**If Python is unavailable**, do the same conversion by hand, following the contract sections named above: show each change as an edit (Claude Code's own diff is the preview) and ask before each file.

---

## Step 2 — Show the plan and collect decisions

Show the plan in short form — the config diff as printed, then one line per other change. Then settle what the script cannot decide, each with `AskUserQuestion`:

1. **Needs a decision** — e.g. a phase value that is not a phase id (`active development`, `writing / review`). Offer the likeliest canonical phases (`neuroflow:neuroflow-core` → **Phase taxonomy**) as options; "Other" takes any phase id. Each answer becomes a `--set` argument: `--set active_phase=paper`, `--set recommended_phases=ideation,data,paper`.
2. **Personal fields** (`auto_issue_reporting`, researcher name, `writing_style`, notification or wellbeing settings) — they belong in `~/.neuroflow/user.yaml`, not in the shared project file. Ask: **Move them to my user.yaml** / **Leave them**. Moving never overwrites a value already in `user.yaml`; the plan says which values are kept.
3. **Apply?** — **Apply these changes** / **Cancel**.

---

## Step 3 — Apply

```bash
python <neuroflow-core base dir>/scripts/migrate.py --root . --apply [--move-personal] [--set key=value ...]
```

The script writes nothing while a decision is still open. It keeps every old reasoning array as `*.json.bak`, keeps the notes body of `project_config.md`, keeps CRLF files CRLF, and is idempotent. Run the dry run again to confirm: exit `0`, or exit `1` with only report-only items left.

---

## Step 4 — Report-only findings

The script edits only the project's own memory, git files and instruction block. It reports — never edits — neuroflow blocks in:

- `~/.claude/CLAUDE.md` — written there by older versions; it pushes one project's phase into every session on the machine
- `.github/copilot-instructions.md` and `AGENTS.md` — mirrors neuroflow no longer writes (it is a Claude Code plugin)

For each one, show the exact block (the script prints it) and ask with `AskUserQuestion` (**Remove the block** / **Keep it**). On yes, delete only that block — from `## neuroflow` to the next level-1 or level-2 heading, or the end of the file — and nothing else. Delete a mirror file only if the block was its only content and the person agrees.

---

## At end

- When something was written, append `## HH:MM — [migrate] Project memory migrated to nf_schema 1: {what changed}` to `.neuroflow/sessions/YYYY-MM-DD.md`.
- Add a line to `reasoning/general.jsonl` for each decision the person made in Step 2 (for example the phase chosen for a legacy value).
- Suggest committing the migration on its own (`/neuroflow:git`), so collaborators see one clean change. Collaborators on an older neuroflow should update the plugin before they write to `.neuroflow/` again.
- Close with `Next: /neuroflow:phase`.
