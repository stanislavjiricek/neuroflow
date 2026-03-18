---
name: grant-proposal
description: Write a full grant application. Discovers ideation outputs automatically, accepts funding call documents or URLs, adapts to any funder (NIH, ERC, Wellcome, GAČR, etc.), and drafts section by section with word-count tracking.
phase: grant-proposal
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/ideation/           # all .md files discovered in Step 0
  - .neuroflow/grant-proposal/flow.md
writes:
  - .neuroflow/grant-proposal/
  - .neuroflow/grant-proposal/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /grant-proposal

Read the `neuroflow:phase-grant-proposal` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` and `flow.md` before starting.

Apply `neuroflow:stop-slop` to every drafted section before saving — eliminate AI writing patterns, filler phrases, passive voice, and formulaic structures from all prose.

---

## Step 0 — Discover the research idea

Before asking the user anything, do the following automatically:

1. Check whether `.neuroflow/ideation/` exists and contains any `.md` files. List every file found.
2. If files exist, read them and extract:
   - The research question or hypothesis
   - Target population / modality (EEG, fMRI, iEEG, eye-tracking, ECG, behaviour, etc.)
   - Any preliminary data or pilot results mentioned
   - Key references or literature already cited
3. Summarise what you found in 3–5 bullet points and tell the user:
   > "I found an existing ideation document. Here's what I'll build the proposal from: …"
4. If no ideation files exist, ask the user:
   - "What is the research question or hypothesis you want to build this grant around?"
   - "Do you have any existing documents (protocol, ethics application, pilot report) you can share?"
   - "Is there a URL to the funder's call for proposals I should read?"

Never skip this step. Do not start drafting until the research idea is confirmed.

---

## Step 1 — Gather funder information

Ask the user (or infer from pasted text / URL):

| Item | Examples |
|---|---|
| Funding body | NIH, ERC, Wellcome Trust, MRC, GAČR, DFG, ANR, NWO, SNSF, ARC, institutional |
| Scheme / mechanism | R01, Starting Grant, Senior Investigator Award, Standard Project |
| Total budget ceiling | e.g. $500 K direct costs, €1.5 M total, 5M CZK |
| Duration | 3 years, 5 years |
| Page / word limits per section | Often varies significantly |
| Deadline | Exact date |
| Required sections | Varies by funder — ask or infer from call document |
| Eligibility constraints | Career stage, host institution requirements |
| Review criteria | e.g. NIH scores significance + investigators + innovation + approach + environment |

If the user provides a URL to the funding call, read it (via WebFetch or browser tool) and extract all of the above automatically.

If the user provides a PDF or pasted text from the call, parse it and extract the same fields.

Report what you found:
> "Target funder: NIH R01. Direct costs up to $500K/year for 5 years. Required sections: Specific Aims (1 page), Research Strategy (12 pages: Significance, Innovation, Approach), Human Subjects, Bibliography. Review criteria: Significance, Investigators, Innovation, Approach, Environment. Deadline: Feb 5."

Ask the user to confirm or correct before proceeding.

---

## Step 2 — Build a proposal outline

Based on the funder requirements and the research idea, produce a structured outline:

```
Proposal outline — [Funder] [Scheme] — [Short title]

1. Specific Aims / Project Summary          [1 page]
2. Background and Significance              [X pages]
3. Innovation                               [X pages]
4. Approach / Methodology                  [X pages]
   4a. Study design
   4b. Participants and recruitment
   4c. Stimuli / Paradigm / Apparatus
   4d. Data acquisition and preprocessing
   4e. Analysis plan
   4f. Expected outcomes
   4g. Potential limitations and alternatives
5. Budget and justification                 [X pages]
6. Timeline                                 [X pages / Gantt chart]
7. Team and environment                     [X pages]
8. References / Bibliography
```

Adapt section names and page limits to the actual funder. Show page budgets and word counts next to each section. Ask the user to approve the outline before writing.

---

## Step 3 — Draft section by section

Work through sections in order. For each section:

1. State the section name, page limit, and review criteria that apply to it
2. Draft the section content
3. Show word count at the bottom: `Word count: NNN / NNN limit`
4. After each section, ask:
   - `"revise"` — iterate on the current section
   - `"next"` — proceed to the next section
   - `"save"` — write to file and continue
   - `"expand [topic]"` — add more depth to a specific part

### Section-specific guidance

**Specific Aims / Project Summary**
- Hook: state the gap, significance, and impact in sentence 1
- 3–5 aims, each with a clear verb (characterize, determine, test, develop, validate)
- End with expected outcomes and long-term impact
- This page is read first by all reviewers — make every sentence count

**Background and Significance**
- State of the art: what is known, what is not known
- Frame the gap in terms the funder cares about (disease burden, scientific opportunity, methodological advance)
- Cite recent and landmark literature
- End with a crisp statement of why your study will change the field

**Innovation**
- Lead with the strongest novel element
- Contrast explicitly with existing approaches: "Unlike X, our approach does Y because Z"
- Novelty can be: question, population, method, analysis, technology, or application
- Avoid overstating — reviewers will penalize unjustified novelty claims

**Approach**
- Describe each aim's methods with enough detail for an expert reviewer to evaluate feasibility
- For neuroscience grants: specify modality, preprocessing pipeline, statistical model, sample size justification (power analysis)
- Address limitations proactively; propose alternatives for each potential failure mode
- Include a Gantt chart or milestone table

**Budget**
- Ask the user for: number of personnel (FTE), equipment list, consumables, travel, indirect costs rate
- Produce a year-by-year table with justification prose for each line
- Flag any items likely to trigger reviewer scrutiny (e.g. large equipment, international travel)

**Timeline**
- Map all aims and key milestones to quarters or months
- Show dependencies (Aim 2 starts after Aim 1 data collection is complete)
- Include manuscript submission and dissemination milestones

**Team and Environment**
- List PI and co-investigators with 1–2 sentence role descriptions
- Highlight relevant expertise and track record (papers, prior grants, preliminary data)
- Describe institutional resources: scanners, clusters, core facilities, collaborator networks

---

## Step 4 — Quality checks before saving

Before saving, run through:

- [ ] Every aim has a measurable outcome
- [ ] All methods are feasible within the budget and timeline
- [ ] Limitations and alternatives are addressed for each aim
- [ ] Word / page counts are within limits for all sections
- [ ] Funder's review criteria are explicitly addressed
- [ ] Preliminary data supports feasibility (if required by funder)
- [ ] References are formatted in funder-required style
- [ ] Budget arithmetic is correct

Report the checklist to the user and fix any issues before saving.

---

## Step 5 — Save and update memory

Save the completed grant document:
- Filename: `grant-[funder]-[date].md` in `.neuroflow/grant-proposal/`

Update `.neuroflow/grant-proposal/flow.md` with:
```
# Grant proposal flow

- Funder: [name]
- Scheme: [name]
- Budget: [amount]
- Deadline: [date]
- Sections drafted: [list]
- Draft file: grant-[funder]-[date].md
- Last updated: [date]
```

Append to `.neuroflow/sessions/YYYY-MM-DD.md`.

Update `project_config.md` with funder, scheme, and deadline if not already present — confirm with the user first.

---

## Funder quick-reference

> Budget figures and page limits are approximate typical values and change with each call cycle. Always verify against the current call document or funder website before submitting.

| Funder | Scheme | Typical limit | Key sections | Review criteria |
|---|---|---|---|---|
| NIH | R01 | $500K DC/yr, 5 yr | Specific Aims (1p), Research Strategy (12p) | Significance, Investigators, Innovation, Approach, Environment |
| NIH | R21 | $275K total, 2 yr | Specific Aims (1p), Research Strategy (6p) | Same as R01 |
| ERC | Starting Grant | €1.5M, 5 yr | Extended Synopsis, Full Proposal | Scientific excellence, Impact, Quality/efficiency |
| ERC | Consolidator | €2M, 5 yr | Same as StG | Same as StG |
| ERC | Advanced Grant | €2.5M, 5 yr | Same as StG | Same as StG |
| Wellcome | Discovery | £3–5M, 5 yr | Flexible structure | Scientific opportunity, Team, Delivery |
| MRC | Programme Grant | £2–4M, 5 yr | Case for Support (20p) | Importance, Quality, Team |
| GAČR | Standard Project | 5M CZK/yr, 3 yr | Project summary, State of art, Objectives, Methodology | Originality, Feasibility, Team |
| DFG | Research Grants | 250K–1M €, 3 yr | Work programme (10–15p) | Scientific quality, Feasibility, Training |
| Horizon Europe | EIC Pathfinder | €3M, 4 yr | Concept, Methodology, Impact | Novelty, Scientific approach, Impact |
