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

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Workflow hints

- `budget-[funder]-[date].md` — the budget plan; reference this in every subsequent expense log and report
- `expenses-[year].md` — running expense log; one file per calendar year
- `financial-report-[funder]-[date].md` — formal funder-facing report
- `compliance-check-[date].md` — internal compliance checklist
- When a budget is multi-year, always show annual breakdowns alongside the total
- If funder conditions are not known, ask the user to provide the grant agreement or key restrictions before doing a compliance check
