---
name: preregistration
description: Create and manage pre-registration documents for OSF or AsPredicted. Covers study design, hypotheses, analysis plan, and linking registered reports.
phase: preregistration
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/preregistration/flow.md
  - .neuroflow/ideation/flow.md
  - .neuroflow/experiment/flow.md
  - skills/phase-preregistration/SKILL.md
writes:
  - .neuroflow/preregistration/
  - .neuroflow/preregistration/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /preregistration

Read the `neuroflow:phase-preregistration` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/preregistration/flow.md` before starting. Also read `.neuroflow/ideation/flow.md` and `.neuroflow/experiment/flow.md` if they exist — load the research question, hypothesis, and paradigm details from there.

## What this command does

Helps the user create and manage pre-registration documents. Ask which mode applies:

1. **Draft pre-registration** — produce a complete pre-registration document for OSF or AsPredicted
2. **Review pre-registration** — check an existing pre-reg document for completeness and internal consistency
3. **Deviation log** — record and justify any post-registration deviation from the pre-registered plan
4. **Link registered report** — record the DOI, URL, or registry ID of a submitted or accepted registered report

---

## Steps

### Draft pre-registration

Ask the user which registry and template they are targeting:
- **OSF** — Preregistration template (standard)
- **OSF** — Secondary data pre-registration
- **AsPredicted**
- **Registered report** (stage 1 submission to a journal)
- **Custom** — ask user for required sections

Pull the research question and hypothesis from `.neuroflow/ideation/` and the paradigm details from `.neuroflow/experiment/` if they exist. Then produce the pre-registration document covering:

**For OSF (standard):**
1. Title and authors
2. Description / study overview
3. Hypotheses (directional where possible)
4. Design: variables, conditions, randomisation, blinding
5. Participants: population, sample size, inclusion/exclusion criteria, power calculation
6. Procedure: timeline, instruments, paradigm details
7. Measures: operationalisation of each variable
8. Analysis plan: statistical tests, correction for multiple comparisons, handling of missing data and outliers
9. Any exploratory (non-confirmatory) analyses clearly labelled
10. Data availability and sharing plan

**For AsPredicted:**
1. Hypothesis and study question
2. Dependent variable(s)
3. Conditions
4. Analyses
5. Outliers and exclusions
6. Sample size (and rationale)

Save as `prereg-[registry]-[date].md` in `.neuroflow/preregistration/`.

### Review pre-registration

Read the existing pre-registration document (ask the user for the file path). Check:
- Is the hypothesis stated in a directional, falsifiable form?
- Are all analysis steps fully specified (test, assumptions, handling of violations)?
- Is the sample size justified by a power calculation?
- Are exclusion and missing-data rules defined before data collection?
- Are exploratory analyses clearly distinguished from confirmatory ones?
- Is there any ambiguity that could allow selective reporting?

Produce a short review report saved as `prereg-review-[date].md` in `.neuroflow/preregistration/`.

### Deviation log

Record a post-registration deviation:
- What was pre-registered?
- What actually happened?
- Why did the deviation occur?
- How does it affect the interpretation of results?

Append to `deviations.md` in `.neuroflow/preregistration/`.

### Link registered report

Record the details of a submitted or accepted registered report:
- Registry or journal
- URL or DOI
- Stage (stage 1 submitted, stage 1 accepted, stage 2 submitted, published)
- Date

Save to `registered-report.md` in `.neuroflow/preregistration/`.

---

## At end

- Update `.neuroflow/preregistration/flow.md` with any new files created
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `project_config.md` if the active phase changed
