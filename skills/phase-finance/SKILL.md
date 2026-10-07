---
name: phase-finance
description: Phase guidance for the neuroflow /finance command. Loaded automatically when /finance is invoked to orient agent behavior, relevant skills, and workflow hints for grant document management and expense tracking.
---

# phase-finance

The finance phase covers everything related to the financial management of a research project — from building the initial budget through grant compliance to funder-facing financial reports.

## Approach

- Identify which mode applies (budget plan, expense log, financial report, compliance check) before doing anything
- Always read `.neuroflow/grant-proposal/flow.md` first if it exists — funder, scheme, and approved budget figures should already be there
- Keep budget tables and expense logs in `.neuroflow/finance/`; never place financial documents outside this folder without explicit user request
- Flag overspends and compliance risks immediately — do not silently continue when a budget line is exceeded
- Ask for the reporting period and funder reference number before producing any funder-facing report
- **Totals come from `scripts/ledger.py`, never from mental arithmetic.** Every sum, remaining balance and overspend in a report or answer is the script's output
- **Never book AI usage as an expense.** Every expense comes from the person, with a receipt or invoice. Never create, estimate or suggest expense rows from AI usage figures (`/cost`, session cost meters, token counts, a share of a subscription) — they are list-price estimates, not records an auditor can verify. If a funder asks about AI use, that belongs in an AI-use disclosure (model, dates, purpose), not in the expense log

## Expense log format

`expenses-[year].md` holds one markdown table with exactly these columns (notes may sit above or below it):

```markdown
| date | grant | category | budget_line | amount | currency | description | reference |
|---|---|---|---|---|---|---|---|
| 2026-03-14 | GR-2025-001 | consumables | consumables | 1240.00 | EUR | EEG caps (2x, size M) | INV-2026-0314 |
```

- `date` — YYYY-MM-DD, the date incurred
- `grant` — the grant or funder reference, spelled the same in every row and in the budget
- `category` — `personnel` | `equipment` | `consumables` | `travel` | `other`
- `budget_line` — the line it is charged to, as named in the budget's `## Budget lines` table
- `amount` — a plain decimal with a dot and no thousands separators (`1240.00`)
- `currency` — ISO code in capitals (`EUR`, `USD`). Never convert: if the funder needs another currency, the person gives the converted amount at the rate the funder or institution mandates
- `reference` — receipt or invoice number
- Append only: new rows go at the bottom; a correction is a new row (negative amount for a refund or reversal), never an edit. No running totals in the file — the script computes them

Every budget file carries one machine-readable table under `## Budget lines` — the approved total per line for the whole funding period (annual breakdown tables for humans may follow):

```markdown
## Budget lines

| grant | budget_line | category | amount | currency |
|---|---|---|---|---|
| GR-2025-001 | consumables | consumables | 5000.00 | EUR |
| GR-2025-001 | travel | travel | 2000.00 | EUR |
```

## Ledger script

```bash
python <skill base dir>/scripts/ledger.py [.neuroflow/finance/] [--budget .neuroflow/finance/budget-[funder]-[date].md] [--grant ID] [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--csv out.csv] [--json]
```

Read-only: totals per currency by grant, by grant and category, and by grant and budget line; with `--budget`, budget vs spent vs remaining per line; with `--csv`, the validated rows for a funder's spreadsheet.

- Exit 0 — clean: use the totals as printed.
- Exit 1 — findings (malformed rows, unknown categories, overspent or unbudgeted lines, currency mismatches): show each to the person; fix malformed rows with them; for an overspend, ask how to proceed.
- Exit 2 — usage or runtime error (no expense files, a budget without a `## Budget lines` table): say so and stop.

Older free-form expense or budget files are not parsed: offer to rewrite them into the tables above (show the result, write only after the person confirms).

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Workflow hints

- `budget-[funder]-[date].md` — the budget plan, with its `## Budget lines` table; reference this in every subsequent expense log and report
- `expenses-[year].md` — append-only expense table; one file per calendar year
- `financial-report-[funder]-[date].md` — formal funder-facing report
- `compliance-check-[date].md` — internal compliance checklist
- When a budget is multi-year, always show annual breakdowns alongside the total
- If funder conditions are not known, ask the user to provide the grant agreement or key restrictions before doing a compliance check
