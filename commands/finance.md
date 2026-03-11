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

Build a structured budget table covering the full funding period. Show annual breakdowns where the period is multi-year. Save as `budget-[funder]-[date].md` in `.neuroflow/finance/`.

### Expense log

Ask for the expense to record:
- Category (personnel, equipment, consumables, travel, other)
- Amount and currency
- Date incurred
- Description and justification
- Budget line it maps to

Append the entry to `expenses-[year].md` in `.neuroflow/finance/`. If an expense would exceed its budget line, flag it immediately and ask the user how to proceed.

### Financial report

Produce a structured financial report covering:
- Total budget vs total expenditure to date
- Breakdown by category
- Remaining balance per budget line
- Any flagged overspends or compliance notes
- Reporting period and funder reference number (ask if not in project memory)

Save as `financial-report-[funder]-[date].md` in `.neuroflow/finance/`.

### Grant compliance

Check the current expense log against the grant conditions:
- Are all expenses within approved categories?
- Are personnel costs within the approved headcount and FTE?
- Are any budget reallocations needed (and does the grant allow them without prior approval)?
- Is the reporting deadline approaching?

Produce a short compliance checklist saved as `compliance-check-[date].md` in `.neuroflow/finance/`.

---

## At end

- Update `.neuroflow/finance/flow.md` with any new files created
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `project_config.md` if the active phase changed
