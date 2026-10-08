---
name: phase-preregistration
description: Phase guidance for the neuroflow /preregistration command. Loaded automatically when /preregistration is invoked to orient agent behavior, relevant skills, and workflow hints for creating and managing pre-registration documents.
user-invocable: false
---

# phase-preregistration

The preregistration phase produces and manages pre-registration documents that commit the research team to a specific hypothesis, design, and analysis plan before data collection begins.

## Approach

- Identify which mode applies (draft, review, deviation log, link registered report, freeze) before starting
- Always pull the research question and hypothesis from `.neuroflow/ideation/` if it exists; pull paradigm details from `.neuroflow/experiment/` if it exists — do not ask the user to repeat information already in project memory
- Ask which registry or template applies before drafting; structure adapts significantly between OSF and AsPredicted
- In all pre-registration drafts: hypotheses must be directional and falsifiable, analysis plans fully specified, and exploratory analyses clearly distinguished from confirmatory ones
- If a power calculation is missing, prompt the user to provide one before saving the document
- Every draft ends with the `prereg-parameters` YAML block (planned N, stopping rule, alpha, filters, windows, ROIs, tests, exclusions) that restates the plan in machine-readable form
- After data collection begins, use the deviation log mode to record any plan changes — never silently edit a submitted pre-registration document
- Freeze the final document with `scripts/freeze.py` only after the person explicitly confirms in the same turn; never freeze or unfreeze on your own

<!-- nf-rule: PREREG-FROZEN -->
**Frozen preregistration files are never edited; changes go to `deviations.md`.** A file listed under `files:` in `.neuroflow/preregistration/status.md` with `status: frozen` carries a `> FROZEN …` banner as its first line. Unfreezing is a person's action and is itself logged in `deviations.md`.

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules (integrity contract C2 for `status.md`)

## Workflow hints

- `prereg-[registry]-[date].md` — the primary pre-registration document; version-control this file
- `prereg-review-[date].md` — completeness and consistency review report
- `status.md` — the freeze record (frontmatter: `status`, `frozen_at`, `files` with SHA-256 hashes, `registry`, `doi`, `planned_n`, `set_by`, `set_at`); written by `freeze.py`, never by hand
- `deviations.md` — running log of post-registration deviations; append only, never overwrite past entries
- `registered-report.md` — metadata for any submitted or accepted registered reports (DOI, stage, date)
- Pre-registration documents are the scientific record — flag any ambiguity that could allow selective reporting or HARKing (Hypothesizing After Results are Known)
- If the user is drafting for a registered report journal submission, note that stage 1 acceptance is typically contingent on the analysis plan being fully specified

## Scripts

- `scripts/freeze.py` — `hash`, `freeze`, `verify`, `unfreeze` for the preregistration hash lock. Hashes ignore the banner, a byte-order mark and CRLF vs LF, so Windows and macOS checkouts agree. `python <skill base dir>/scripts/freeze.py verify` — exit 0 = unchanged or not frozen, 1 = findings (changed, missing, banner removed, freeze not set by a person), 2 = usage error or refusal. Other checks (`/sentinel`, the neuroflow mod) call this script rather than re-implement the hash.
