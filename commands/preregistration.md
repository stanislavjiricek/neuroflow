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
lifecycle: full
produces:
  - ".neuroflow/preregistration/prereg-{registry}-{date}.md"
  - .neuroflow/preregistration/status.md
next:
  - experiment
---

# /preregistration

Read the `neuroflow:phase-preregistration` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/preregistration/flow.md` before starting. Also read `.neuroflow/ideation/flow.md` and `.neuroflow/experiment/flow.md` if they exist — load the research question, hypothesis, and paradigm details from there.

## What this command does

Helps the user create and manage pre-registration documents. Ask which mode applies:

1. **Draft pre-registration** — produce a complete pre-registration document for OSF or AsPredicted
2. **Review pre-registration** — check an existing pre-reg document for completeness and internal consistency
3. **Deviation log** — record and justify any post-registration deviation from the pre-registered plan
4. **Link registered report** — record the DOI, URL, or registry ID of a submitted or accepted registered report
5. **Freeze** — hash-lock the final pre-registration (and, as a person's action only, unfreeze it)

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

**Machine-readable parameters (every template).** End the document with one fenced block that restates the planned parameters, so later steps can compare the analysis with the plan without parsing prose. Keep it in sync with the text; where the two differ, the registered prose wins. Leave out keys that do not apply.

````markdown
```yaml prereg-parameters
planned_n: 48                  # sample size the study commits to
stopping_rule: fixed           # fixed | sequential (describe the interim looks in the text)
alpha: 0.05
preprocessing:
  highpass_hz: 0.1
  lowpass_hz: 30
  notch_hz: 50
  reference: average
  epoch_s: [-0.2, 0.8]
  baseline_s: [-0.2, 0.0]
  rejection: "peak-to-peak > 100 uV"
rois:
  P3: [Pz, CPz, POz]
windows_s:
  P3: [0.30, 0.50]
tests:
  - id: H1
    dv: mean amplitude, P3 ROI, P3 window
    test: paired t-test, target vs standard
    tail: greater
    correction: none
exclusions:
  - fewer than 30 artifact-free trials per condition
allocation:                    # only if orders or groups come from allocation.py
  scheme: williams
  seed: 20261007
  schedule_sha256: 3f5a...
```
````

Save as `prereg-[registry]-[date].md` in `.neuroflow/preregistration/`.

### Review pre-registration

Read the existing pre-registration document (ask the user for the file path). Check:
- Is the hypothesis stated in a directional, falsifiable form?
- Are all analysis steps fully specified (test, assumptions, handling of violations)?
- Is the sample size justified by a power calculation?
- Are exclusion and missing-data rules defined before data collection?
- Are exploratory analyses clearly distinguished from confirmatory ones?
- Is there any ambiguity that could allow selective reporting?
- Is there a `prereg-parameters` block, and does it match the text (filters, windows, ROIs, tests, alpha, N, stopping rule)?

Produce a short review report saved as `prereg-review-[date].md` in `.neuroflow/preregistration/`.

### Deviation log

Record a post-registration deviation:
- What was pre-registered?
- What actually happened?
- Why did the deviation occur?
- How does it affect the interpretation of results?

Append to `deviations.md` in `.neuroflow/preregistration/`. It is append-only: never edit or delete an earlier entry, and add no running totals or "last updated" lines (collaborators' copies are merged line by line).

### Freeze

Freeze the pre-registration once it is final — at the latest when it goes to the registry. The registry copy (OSF, AsPredicted, the journal) is the public record; the freeze keeps the local copy honest and gives `/sentinel` and the analysis phases a fixed reference.

1. Read `.neuroflow/preregistration/status.md` if it exists. List the files to freeze (the `prereg-*.md` document(s), not the review reports) and show the person the plan: files, registry, DOI, `planned_n` (from the `prereg-parameters` block).
2. Freeze only after the person explicitly confirms in this turn ("yes, freeze it") — never on your own and never in unattended runs (`/pipeline` executor mode, autoresearch). Then run:
   `python <phase-preregistration base dir>/scripts/freeze.py freeze <files> --set-by person [--registry OSF] [--doi <doi>] [--planned-n <N>]`
   It writes the C2 frontmatter of `status.md` (`status: frozen`, `frozen_at`, the SHA-256 of each file, `set_by: person`, `set_at`) and puts the banner `> FROZEN <date> — sha256 <hash>… — do not edit; record changes in deviations.md` on the first line of each frozen file. Exit 0 = frozen; 2 = refused (already frozen, file outside the project, not a text file).
3. Check it at any time with `python <phase-preregistration base dir>/scripts/freeze.py verify`: exit 0 = every frozen file unchanged (or nothing frozen), 1 = a file changed, is missing or lost its banner, or the freeze was not set by a person — report it; a changed file is restored and the change recorded in `deviations.md`.

<!-- nf-rule: PREREG-FROZEN -->
**Frozen preregistration files are never edited; changes go to `deviations.md`.** This holds for the whole frozen file, typos included. Unfreezing (for example to fix a typo before the registry submission) is a person's action: only when the person asks for it in this turn, run `freeze.py unfreeze --set-by person --reason "<why>"`. It sets `status: draft`, removes the banners and logs the unfreeze, with the previous hashes, in `deviations.md`; freeze again afterwards.

### Link registered report

Record the details of a submitted or accepted registered report:
- Registry or journal
- URL or DOI
- Stage (stage 1 submitted, stage 1 accepted, stage 2 submitted, published)
- Date

Save to `registered-report.md` in `.neuroflow/preregistration/`. If the document is not frozen yet, pass the DOI to the freeze (`--doi`).

---

## At end

- Update `.neuroflow/preregistration/flow.md` with any new files created (`status.md`, `deviations.md` included)
- Append to `.neuroflow/sessions/YYYY-MM-DD.md`
- Update `active_phase` in `project_config.md` if the active phase changed
