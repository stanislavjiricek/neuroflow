---
name: finance
description: Manage grant documents and track project expenses. Covers budget planning, expense logging, financial reporting to funders, and grant compliance.
phase: finance
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/finance/flow.md
  - .neuroflow/grant-proposal/flow.md
  - skills/phase-finance/SKILL.md
writes:
  - .neuroflow/finance/
  - .neuroflow/finance/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
lifecycle: full
produces:
  - .neuroflow/finance/
---

# /finance

Read the `neuroflow:phase-finance` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/finance/flow.md` before starting. Also read `.neuroflow/grant-proposal/flow.md` if it exists — load any funder, scheme, or budget figures from there.

## What this command does

Helps the user manage grant documents and track project expenses. Ask which mode applies:

1. **Budget plan** — build or update the project budget (personnel, equipment, consumables, indirect costs)
2. **Expense log** — record expenses against budget lines; flag overspends
3. **Financial report** — produce a funder-facing financial report or internal expense summary
4. **Grant compliance** — check whether spending aligns with grant conditions and flag any issues

---

## Steps

### Budget plan

Ask the user for:
- Funder and grant scheme (check `.neuroflow/grant-proposal/flow.md` if it exists)
- Funding period (start and end dates)
- Budget lines: personnel (names/roles/FTE), equipment, consumables, travel, indirect/overhead rate

Build a structured budget table covering the full funding period. Show annual breakdowns where the period is multi-year. Save as `budget-[funder]-[date].md` in `.neuroflow/finance/`, including the machine-readable `## Budget lines` table (phase-finance → Expense log format).

### Expense log

Ask for the expense to record:
- Category (personnel, equipment, consumables, travel, other)
- Amount and currency
- Date incurred
- Description and justification
- Budget line it maps to
- Receipt or invoice reference

Every expense comes from the person, with a receipt or invoice — never book AI usage figures (`/cost`, token counts, a share of a subscription) as an expense.

Append the entry as one row of the expense table in `expenses-[year].md` in `.neuroflow/finance/` (phase-finance → Expense log format), then run `python <phase-finance base dir>/scripts/ledger.py .neuroflow/finance/ --budget {budget file}` (Claude Code shows the base directory when the `neuroflow:phase-finance` skill loads; exit codes as in phase-finance → Ledger script). If it reports an overspent line (exit 1), flag it immediately and ask the user how to proceed; fix any malformed-row finding with them.

### Financial report

Run `ledger.py` (with `--budget`, `--grant` and `--from`/`--to` for the reporting period) and take every figure from its output — no hand-computed totals. Use `--csv` when the funder wants a spreadsheet. Produce a structured financial report covering:
- Total budget vs total expenditure to date
- Breakdown by category
- Remaining balance per budget line
- Any flagged overspends or compliance notes
- Reporting period and funder reference number (ask if not in project memory)

Save as `financial-report-[funder]-[date].md` in `.neuroflow/finance/`.

### Grant compliance

Check the current expense log against the grant conditions (start from `ledger.py --budget` findings):
- Are all expenses within approved categories?
- Are personnel costs within the approved headcount and FTE?
- Are any budget reallocations needed (and does the grant allow them without prior approval)?
- Is the reporting deadline approaching?

Produce a short compliance checklist saved as `compliance-check-[date].md` in `.neuroflow/finance/`.

---

## At end

- Update `.neuroflow/finance/flow.md` with any new files created
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `active_phase` in `project_config.md` if the phase changed
