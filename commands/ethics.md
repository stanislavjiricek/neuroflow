---
name: ethics
description: Ethics and IRB workflow — track protocol submissions and amendments, version consent forms, monitor approval status and expiry dates. The hard gate before any human data collection.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/ethics/
  - .neuroflow/timeline.md
writes:
  - .neuroflow/ethics/
  - .neuroflow/timeline.md
  - .neuroflow/sessions/YYYY-MM-DD.md
lifecycle: full
produces:
  - .neuroflow/ethics/status.md
next:
  - experiment
  - data
---

# /ethics

Follow the `neuroflow:neuroflow-core` lifecycle — open with its version notice when the project's `plugin_version` is behind the running neuroflow, whose version is in `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` (**Command lifecycle**, step 3). Ethics approval is a **hard gate** for human neuroscience — no data collection may begin before it, and expired approvals invalidate ongoing collection. This command makes that gate visible.

Everything lives in the standard `.neuroflow/ethics/` root folder, with a `status.md` as the single source of truth.

## Modes

| Mode | What it does |
|---|---|
| *(none)* / `--status` | Show the approval dashboard (below); offer the frontmatter for a legacy table-only `status.md` |
| `--protocol` | Draft or update the ethics protocol; log amendments |
| `--consent` | Create or revise a consent form — always as a new version |
| `--approved` | Record an approval: committee, reference number, approval date, **expiry date**, and whether participant data may be read by the AI model (`ai_processing`) |
| `--erase` | A participant asked for erasure: record it, run the sweep, work the checklist (below) |

## `ethics/status.md` — the source of truth

The gate state lives in the frontmatter (integrity contract C2 in `neuroflow-core`); the tables below it are for people.

```markdown
---
nf_schema: 1
status: approved                  # none | pending | approved | expired | withdrawn
approval_id: EC-2026-014          # optional — the committee's reference
expires: 2027-06-30               # optional ISO date
ai_processing: none               # none | pseudonymised | identifiable
set_by: person                    # person | model
set_at: 2026-09-12T09:00:00Z
---
# Ethics status

| Item | Value |
|---|---|
| Committee | {name of IRB / ethics committee} |
| Protocol reference | {number} |
| Approved | YYYY-MM-DD |
| Consent form version | v{N} (consent-v{N}.md) |

## Amendments
| # | Date | What changed | Status |
|---|---|---|---|
```

- **`status`** — `none` (nothing submitted or approved yet), `pending` (submitted, awaiting a decision), `approved`, `expired`, `withdrawn` (approval suspended or withdrawn). A pending amendment does not change `status`; it gets its own row.
- **`set_by: person`** only when the person confirmed the values in this turn ("yes, record it") right before the write; otherwise write `set_by: model`. Readers treat `approved` with `set_by: model` as not approved, so the gate stays closed until a person confirms. `set_at` is the UTC time of the write.
- **Legacy `status.md`** (table only, no frontmatter): its `Status` and `Expires` rows still count — the old format had no `set_by`, and a person recorded it. On any mode, show the frontmatter derived from the table (`draft` → `none`, `submitted` → `pending`, `amendment-pending` → `approved`; `approved` and `expired` unchanged; `Expires` → `expires`) and write it only after the person confirms. Never rewrite it silently.

## The gate

<!-- nf-rule: ETHICS-GATE -->
**No data collection steps before ethics status is approved.** The gate is open only when the frontmatter says `status: approved` with `set_by: person` (or a legacy table says `approved`) and `expires` is empty or not yet past. `/experiment` (participant sessions, pilots with volunteers, allocating participants) and `/data` (intake of your own participants' data) read it before those steps and stop with the reason when it is closed. A project that needs no approval tracked here (public de-identified datasets, simulations) notes `ethics: not-applicable` in the `project_config.md` frontmatter; the gate and sentinel's ethics check then stay silent.

## AI processing of participant data

Every file the model reads, and every command output it sees, is sent to the model provider (directly or through a gateway) and kept in plain text in Claude Code's local transcripts (`~/.claude/projects/`, deleted after `cleanupPeriodDays`, 30 days by default). Under applicable data-protection law (e.g. GDPR or HIPAA), the provider then processes participant data as a data processor. Whether that is allowed, and on which route, is decided by the approved protocol, the consent form and your data-protection officer, not by neuroflow. `ai_processing` records that decision:

| Value | The model may read |
|---|---|
| `none` — also when the field is missing or `set_by: model` | No participant-level data. Technical metadata without participant values (sidecar JSON, channel lists, column names) and the aggregate output of scripts the person runs (counts, group statistics, QC summaries without IDs). |
| `pseudonymised` | Pseudonymised data (`sub-XX` files, `participants.tsv` without direct identifiers). Never the identity key, signed consent forms, or files carrying names, birth dates or contact details (e.g. raw headers with patient fields). |
| `identifiable` | Identifiable data, as far as the approval covers this provider and route. Still only what the task needs. |

<!-- nf-rule: PARTICIPANT-ROUTE -->
**Participant data is read by the model only if `ai_processing` allows it.** A project marked `ethics: not-applicable` declares that it holds no participant data to protect, so the rule (and the mod's PARTICIPANT-ROUTE guard) does not apply there — the flag is for public de-identified data and simulations only. When reading is not allowed, write the script, let the person run it, and work from its aggregate output. With `none`, offer to add the raw folders (e.g. `Read(./sourcedata/**)`) to `permissions.deny` in the project's `.claude/settings.json`: a seatbelt for the Read tool, not a vault, because shell commands and scripts can still print rows.

## Participant erasure (`--erase`)

Excluding a withdrawn participant from analyses is not erasure. When a participant asks for their data to be erased:

1. **Record the request.** Append to `.neuroflow/ethics/erasure-log.md`: date, pseudonymous ID, request reference — never a name or contact details. Check what the consent and protocol require you to keep, and who holds the identity key.
2. **Sweep.** Give the person the full command and ask them to run it in their own terminal, outside Claude Code, so the ID and the hit list do not land in a new transcript: `python <phase-data base dir>/scripts/erasure_sweep.py --id sub-07 [--id <other codes for the same person>] [--extra <export or server folder>]` (`<phase-data base dir>` is the `skills/phase-data/` folder of the neuroflow plugin). It finds and reports paths and counts, never contents, and never deletes. Exit 0 = nothing found, 1 = occurrences listed, 2 = usage error.
3. **Work the checklist.** The person deletes; the model never does. Log each location with what was done:

| Location | What to do |
|---|---|
| Raw recordings, `sourcedata/`, the BIDS tree (`sub-<id>/`, the `participants.tsv` row, `scans.tsv`) | Delete as the protocol allows |
| Derivatives, results, figures, caches | Delete, or regenerate without the participant |
| `.neuroflow/` (wiki pages, reasoning, sessions, meetings, tasks, QC reports) | Remove the participant's entries; keep the erasure log |
| Git history (all branches, tags, stashes) | Rewriting history (e.g. `git filter-repo`) is a separate step agreed with collaborators; the remote and their clones keep copies until then |
| Claude Code's local data (`~/.claude/projects/` transcripts, `history.jsonl`, `file-history/`, `paste-cache/`, temp scratchpads) | Delete the files the sweep lists, or the project's whole state with `claude purge <project path>` (`--dry-run` first; `claude project purge` before v2.1.288) — that removes every transcript of the project, not single lines |
| `~/.neuroflow/` (flowie wiki and tasks, hive caches) and their remotes | Edit locally, push, ask hive maintainers to do the same |
| Exports, cloud drives, external services, backups | Check by hand — the sweep cannot reach them |
| The model provider | Copies held by the provider follow your organisation's agreement with it; neuroflow cannot certify their erasure |

4. **Close.** Log the date and what remains outside reach. The erasure log itself is never deleted.

## Rules

1. **Consent forms are versioned, never edited in place.** A change to `consent-v2.md` becomes `consent-v3.md` — participants signed a specific version, and that version must remain retrievable exactly as signed. Record which version was in force for which date range in `status.md`.
2. **Protocol amendments are append-only** — every change to an approved protocol gets an amendment row with its own status. Amendments that change data collection also trigger a `reasoning/general.jsonl` entry (mandatory trigger: scope change).
3. **Expiry goes on the timeline.** When recording an approval, write the expiry date into `.neuroflow/timeline.md`. `/phase` surfaces upcoming deadlines from the timeline, so an approaching expiry is visible without running `/ethics`.
4. **Warn on the gate.** On `--status`, if `.neuroflow/data/` exists and the gate is closed — or the earliest data predates the approval date — print a prominent warning. (Sentinel performs the same cross-check during audits.)
5. **Participants only ever see validated software.** Stimuli, questionnaires and consent run in the software the approved protocol names (e.g. PsychoPy or a survey platform), never inside Claude Code, where answers would reach the model and every installed plugin. Claude Code writes and validates those scripts; it does not present them.

## Dashboard (`--status` output)

```
Ethics — {committee} ({protocol reference})

  Status:    ✅ approved            (or ❌ none / ⏳ pending / ⚠️ expired / ⛔ withdrawn)
  Set by:    person, 2026-09-12     (⚠ "model" = not confirmed — the gate stays closed)
  Approved:  2026-05-01
  Expires:   2027-05-01             ⚠ shown in red if < 60 days away
  AI processing: none
  Consent:   v3 (in force since 2026-05-01)
  Amendments: 1 approved, 1 pending
```

## At end

- Update `.neuroflow/ethics/flow.md` (including `erasure-log.md` when created) and register `ethics/` in the root `flow.md` on first use.
- Append `## HH:MM — [ethics] {what changed}` to the session log. For `--erase`, the line names no participant ID.
