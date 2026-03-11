---
name: phase-preregistration
description: Phase guidance for the neuroflow /preregistration command. Loaded automatically when /preregistration is invoked to orient agent behavior, relevant skills, and workflow hints for creating and managing pre-registration documents.
---

# phase-preregistration

The preregistration phase produces and manages pre-registration documents that commit the research team to a specific hypothesis, design, and analysis plan before data collection begins.

## Approach

- Identify which mode applies (draft, review, deviation log, link registered report) before starting
- Always pull the research question and hypothesis from `.neuroflow/ideation/` if it exists; pull paradigm details from `.neuroflow/experiment/` if it exists — do not ask the user to repeat information already in project memory
- Ask which registry or template applies before drafting; structure adapts significantly between OSF and AsPredicted
- In all pre-registration drafts: hypotheses must be directional and falsifiable, analysis plans fully specified, and exploratory analyses clearly distinguished from confirmatory ones
- If a power calculation is missing, prompt the user to provide one before saving the document
- After data collection begins, use the deviation log mode to record any plan changes — never silently edit a submitted pre-registration document

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Workflow hints

- `prereg-[registry]-[date].md` — the primary pre-registration document; version-control this file
- `prereg-review-[date].md` — completeness and consistency review report
- `deviations.md` — running log of post-registration deviations; append only, never overwrite past entries
- `registered-report.md` — metadata for any submitted or accepted registered reports (DOI, stage, date)
- Pre-registration documents are the scientific record — flag any ambiguity that could allow selective reporting or HARKing (Hypothesizing After Results are Known)
- If the user is drafting for a registered report journal submission, note that stage 1 acceptance is typically contingent on the analysis plan being fully specified
