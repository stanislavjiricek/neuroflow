---
title: /finance
---

# `/neuroflow:finance`

**Manage grant documents and track project expenses.**

`/finance` helps you build and maintain the financial side of your research project — from the initial budget plan through expense tracking to funder-facing reports and compliance checks.

---

## When to use it

- You need to build or update the project budget
- You want to log an expense against a budget line
- You need to produce a financial report for your funder
- You want to check whether current spending is within grant conditions

---

## What it does

Claude reads your project memory (`.neuroflow/grant-proposal/`) for funder and budget context, then asks which mode applies:

1. **Budget plan** — build the full project budget, broken down by personnel, equipment, consumables, travel, and indirect costs
2. **Expense log** — record a new expense against a budget line; flags overspends immediately
3. **Financial report** — produce a funder-facing report comparing budget to actual spend
4. **Grant compliance** — check whether spending aligns with grant conditions and flag any issues

---

## Budget plan

Claude asks for:

- Funder and grant scheme (loaded from `/grant-proposal` if available)
- Funding period (start and end dates)
- Budget lines: personnel (names, roles, FTE), equipment, consumables, travel, overhead rate

It then produces a structured budget table with annual breakdowns for multi-year grants.

**Output:** `budget-[funder]-[date].md` saved to `.neuroflow/finance/`

---

## Expense log

Claude records:

- Category (personnel, equipment, consumables, travel, other)
- Amount and currency
- Date incurred
- Description and justification
- Which budget line it maps to

Overspends are flagged immediately.

**Output:** appended to `expenses-[year].md` in `.neuroflow/finance/`

---

## Financial report

Claude produces a report covering:

| Section | Content |
|---|---|
| **Summary** | Total budget vs total expenditure |
| **By category** | Breakdown per budget line |
| **Remaining balance** | Per budget line |
| **Compliance notes** | Any flagged issues |

**Output:** `financial-report-[funder]-[date].md` saved to `.neuroflow/finance/`

---

## Grant compliance

Claude checks the current expense log against grant conditions:

- Are all expenses within approved categories?
- Are personnel costs within approved headcount and FTE?
- Are budget reallocations needed — and does the grant allow them without prior approval?
- Is the reporting deadline approaching?

**Output:** `compliance-check-[date].md` saved to `.neuroflow/finance/`

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/finance/flow.md`, `.neuroflow/grant-proposal/flow.md` |
| Writes | `.neuroflow/finance/`, `.neuroflow/finance/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md` |

---

## Related commands

- [`/grant-proposal`](grant-proposal.md) — write the grant application that defines the approved budget
- [`/write-report`](write-report.md) — generate a progress report for funders alongside a financial report
