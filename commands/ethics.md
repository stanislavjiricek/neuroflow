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
---

# /ethics

Follow the `neuroflow:neuroflow-core` lifecycle. Ethics approval is a **hard gate** for human neuroscience — no data collection may begin before it, and expired approvals invalidate ongoing collection. This command makes that gate visible.

Everything lives in the standard `.neuroflow/ethics/` root folder, with a `status.md` as the single source of truth.

## Modes

| Mode | What it does |
|---|---|
| *(none)* / `--status` | Show the approval dashboard (below) |
| `--protocol` | Draft or update the ethics protocol; log amendments |
| `--consent` | Create or revise a consent form — always as a new version |
| `--approved` | Record an approval: committee, reference number, approval date, **expiry date** |

## `ethics/status.md` — the source of truth

```markdown
# Ethics status

| Item | Value |
|---|---|
| Committee | {name of IRB / ethics committee} |
| Protocol reference | {number} |
| Status | draft \| submitted \| approved \| amendment-pending \| expired |
| Approved | YYYY-MM-DD |
| Expires | YYYY-MM-DD |
| Consent form version | v{N} (consent-v{N}.md) |

## Amendments
| # | Date | What changed | Status |
|---|---|---|---|
```

## Rules

1. **Consent forms are versioned, never edited in place.** A change to `consent-v2.md` becomes `consent-v3.md` — participants signed a specific version, and that version must remain retrievable exactly as signed. Record which version was in force for which date range in `status.md`.
2. **Protocol amendments are append-only** — every change to an approved protocol gets an amendment row with its own status. Amendments that change data collection also trigger a `reasoning/general.json` entry (mandatory trigger: scope change).
3. **Expiry goes on the timeline.** When recording an approval, write the expiry date into `.neuroflow/timeline.md`. `/phase` surfaces upcoming deadlines from the timeline, so an approaching expiry is visible without running `/ethics`.
4. **Warn on the gate.** On `--status`, if `.neuroflow/data/` exists and the status is not `approved` — or the earliest data predates the approval date — print a prominent warning. (Sentinel performs the same cross-check during audits.)

## Dashboard (`--status` output)

```
Ethics — {committee} ({protocol reference})

  Status:    ✅ approved            (or ❌ draft / ⏳ submitted / ⚠️ expired)
  Approved:  2026-05-01
  Expires:   2027-05-01             ⚠ shown in red if < 60 days away
  Consent:   v3 (in force since 2026-05-01)
  Amendments: 1 approved, 1 pending
```

## At end

- Update `.neuroflow/ethics/flow.md` and register `ethics/` in the root `flow.md` on first use.
- Append `## HH:MM — [ethics] {what changed}` to the session log.
