---
name: phase-output
description: Phase guidance for the neuroflow /output command. Orients agent approach for outputting project memory or the whole project safely and with correct exclusions.
---

# phase-output

The `/output` command packages and moves project data out of the workspace. Its job is to give the user a clean, portable snapshot without accidentally including sensitive files.

## Approach

- Clarify the user's intent before choosing scope — "sharing with a collaborator" suggests memory-only; "handing off the full repo" suggests whole project
- Always exclude `sessions/` (local-only, can be large) and `integrations.json` (API credentials — must never be shared)
- Prefer zip over folder copy for sharing — it is a single file and preserves timestamps
- Use Python's `zipfile` module first; fall back to system `zip`/`tar` only if Python is unavailable
- If the user asks about Notion integration or other cloud destinations, acknowledge it is planned but not yet implemented — offer zip as the portable alternative for now
- Do not modify the project or `.neuroflow/` state during export — the command is read-only except for writing the export log

## Scope guidance

| Scope | Best for |
|---|---|
| Project memory (`.neuroflow/` minus exclusions) | Sharing context with a collaborator who has their own codebase; supervision meetings; archiving project decisions and reasoning |
| Whole project (git-tracked + `.neuroflow/`) | Full handoff, long-term archiving, submitting to a data repository |
| Single phase | Focused handoff — e.g. sending only the `data-analyze/` memory to a statistician |

## Exclusions — always enforce

| Excluded | Reason |
|---|---|
| `.neuroflow/sessions/` | Local-only operation log — large, personal, not meaningful to external recipients |
| `.neuroflow/integrations.json` | API credentials (PubMed email, Miro token) — must never leave the local machine |

If the user explicitly asks to include sessions or credentials, explain why that is inadvisable and confirm they still want to before proceeding.

## File naming convention

Default names for export outputs:

```
output-[project-slug]-[YYYY-MM-DD].zip
output-[project-slug]-[YYYY-MM-DD]/     (folder copy)
output-[phase]-[project-slug]-[YYYY-MM-DD].zip   (single-phase)
```

Where `project-slug` is the project name from `project_config.md`, lowercased with spaces replaced by hyphens.

## What to suggest if the user asks "what else can I export?"

- **Manuscript draft** — if `paper-write/` exists, offer to run `/write-report` to generate a summary first, then include it in the export alongside any manuscript files from the `paper-write` output path
- **Analysis report** — run `/write-report` first to generate a summary, then include it in the export
- **Reasoning log** — mention that `.neuroflow/reasoning/` is included in the memory export and contains all documented decisions

Do not suggest Notion or other cloud integrations — they are not implemented yet.

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules
