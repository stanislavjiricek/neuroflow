---
name: phase-output
description: Phase guidance for the neuroflow /output command. Orients agent approach for outputting project memory or the whole project safely and with correct exclusions.
---

# phase-output

The `/output` command packages and moves project data out of the workspace. Its job is to give the user a clean, portable snapshot without accidentally including sensitive files.

## Approach

- Clarify the user's intent before choosing scope — "sharing with a collaborator" suggests memory-only; "handing off the full repo" suggests whole project; "someone takes over the project" suggests `--handoff`
- Export only with `scripts/export.py` — it applies the exclusions before copying and verifies the result. Never pack with `zip`, `tar`, `cp`, `xcopy` or `Compress-Archive`: they skip the exclusions
- Prefer zip over folder copy for sharing — it is a single file and preserves timestamps
- If the user asks about Notion integration or other cloud destinations, acknowledge it is planned but not yet implemented — offer zip as the portable alternative for now
- Do not modify the project or `.neuroflow/` state during export — the command is read-only except for writing the export log

## Scope guidance

| Scope | Best for |
|---|---|
| Project memory (`.neuroflow/` minus exclusions) | Sharing context with a collaborator who has their own codebase; supervision meetings; archiving project decisions and reasoning |
| Whole project (git-tracked + `.neuroflow/`) | Full handoff, long-term archiving, submitting to a data repository |
| Single phase | Focused handoff — e.g. sending only the `data-analyze/` memory to a statistician |

## Exclusions — always enforced (neuroflow-core → Sharing tiers)

`scripts/export.py` is the single home of these rules; the other scripts import them from there.

| Excluded | Reason |
|---|---|
| `.neuroflow/sessions/` | Local tier — personal operation log |
| `.neuroflow/review/` | Local tier — colleagues' manuscripts under confidential peer review |
| `.neuroflow/integrations.json`, `.neuroflow/flowie/` | Local tier — credentials and personal settings |
| `.neuroflow/fails/`, `.neuroflow/finance/` | Never leave the team |
| `.neuroflow/ethics/` files off the allowlist | May identify participants; only `status.md`, `flow.md`, `consent-vN.md` form versions, `protocol*.md`, `amendment*.md` pass. A checked file can be added with `--include-ethics` |
| Credential files anywhere | `.env`, `*.pem`, private SSH keys, `client_secret*.json`, `credentials.json`, `.netrc`, `.pypirc` |

Local-tier paths, `fails/`, `finance/` and credential files have no override. If the person needs one of them elsewhere, they copy it themselves.

## Scripts

All in `scripts/`, stdlib Python, `--json` output, exit codes `0` clean / `1` findings / `2` usage or runtime error. None prints a secret or personal value.

| Script | Used by | What it does |
|---|---|---|
| `export.py` | `/output` | Builds the file list, drops excluded paths, previews (`--dry-run`), writes the zip or folder, verifies it |
| `header_scan.py` | `/output --archive` | De-identification scan of EDF/BDF, BrainVision, NIfTI (and FIF with MNE) headers and `participants.tsv` columns |
| `pii_scan.py` | `/output --archive`, `/sentinel`, pre-commit | Emails, phone numbers, configured ID patterns (none ships for any country), salted-hash participant roster, secrets; `--staged` also flags local-tier and credential files staged for commit |
| `history_audit.py` | `/output --archive` | Whole git history before a repository goes public: sensitive paths, secrets, personal data, recordings, large files |
| `handoff.py` | `/output --handoff` | Read-only handoff dossier: git state, data roots, freeze and ethics status, open tasks by assignee, integrations to replace |

**Pre-commit use of `pii_scan.py`:** a project can call it from its own git pre-commit hook — `python "<phase-output skill base dir>/scripts/pii_scan.py" --staged` — so exit `1` blocks the commit. The plugin path changes when the plugin updates, so the hook must be refreshed after an update. Keep the participant roster (`--build-roster`) outside the project tree and never commit it; the names file it is built from is read only by the script.

## File naming convention

Default names for export outputs:

```
output-[project-slug]-[YYYY-MM-DD].zip
output-[project-slug]-[YYYY-MM-DD]/     (folder copy)
output-[phase]-[project-slug]-[YYYY-MM-DD].zip   (single-phase)
```

Where `project-slug` is `project_name` from the `project_config.md` frontmatter, lowercased with spaces replaced by hyphens. Whole-project exports default to the folder above the project root — a destination inside the exported tree is refused.

## What to suggest if the user asks "what else can I export?"

- **Manuscript draft** — if `paper/` exists, offer to run `/write-report` to generate a summary first, then include it in the export alongside any manuscript files from the `paper` output path
- **Analysis report** — run `/write-report` first to generate a summary, then include it in the export
- **Reasoning log** — mention that `.neuroflow/reasoning/` is included in the memory export and contains all documented decisions
- **Handoff dossier** — when the project changes hands, `/output --handoff`

Do not suggest Notion or other cloud integrations — they are not implemented yet.

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules
- `neuroflow:notebooklm` — when the user wants a podcast, infographic, slide deck, or audio summary generated from exported project materials, invoke the `notebooklm` skill to create a NotebookLM notebook. Uploading exported files to it is outbound data movement: show the exact file list and upload only what the person confirms
