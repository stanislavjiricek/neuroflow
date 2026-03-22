---
name: grant-proposal
description: Write a full grant application. Starts with an interactive interview, discovers ideation outputs, accepts funding call documents or URLs, adapts to any funder (NIH, ERC, Wellcome, GAČR, etc.), and drafts section by section with word-count tracking.
phase: grant-proposal
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/objectives.md         # read if exists — project objectives cornerstones
  - .neuroflow/ideation/             # all .md files discovered in Step 0
  - .neuroflow/grant-proposal/flow.md
writes:
  - .neuroflow/grant-proposal/
  - .neuroflow/grant-proposal/flow.md
  - .neuroflow/objectives.md         # written/updated after interview confirms objectives
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /grant-proposal

Read the `neuroflow:phase-grant-proposal` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `objectives.md` (if it exists) before starting.

Apply `neuroflow:humanizer` to every drafted section before saving — strip AI signatures, fix rhythm, and calibrate register so the prose reads as genuinely human-authored.

Use `mcp__plugin_neuroflow_sequentialthinking__sequentialthinking` when structuring the logical argument for Innovation and Approach sections — invoke it before drafting those sections, not after.

---

## Step 0 — Interview the researcher

**Before looking at any ideation files or funder documents, interview the user.** Ask questions one or two at a time — conversational, not a form dump. Build context progressively.

Questions to work through (adapt based on what emerges):

1. What is your core research question? (If `.neuroflow/ideation/` exists, read it first and offer a summary — ask "Is this still the right question?")
2. What funder and scheme are you targeting? (Or: "Do you have the call URL or document?")
3. What is your funding ceiling and duration?
4. Do you have a deadline?
5. What are your specific objectives or aims? (Ask for 3–4 concrete, verb-led statements)
6. What preliminary data do you have?
7. What makes your approach novel — what do you do that current methods don't?
8. Who is your team and what is each person's role?
9. Are there any constraints I should know about? (Ethics approval, required partnerships, budget items already committed)
10. Do you have any previous grant applications I can use as structural inspiration?

After the interview, save the answers to `.neuroflow/grant-proposal/interview-[funder]-[date].md`.

**Write the objectives to `.neuroflow/objectives.md`** (create or overwrite) — one numbered sentence per objective. These are the cornerstones for the rest of the session.

**Offer panel research (optional):** "Would you like me to research the review panel for [funder] and suggest where to submit? (Requires the panel listing URL)"

If yes → run Step 0b. If no → proceed to Step 1.

---

## Step 0b — Panel research (optional)

If the user agrees to panel research:

1. Ask for the panel listing URL (funder website)
2. Use WebFetch to retrieve the panel listing
3. For each panel/reviewer found: use WebSearch to research their background (2–3 key papers, methodological themes, primary research area)
4. Build a panel profile table:

```
| Panel name | Member | Research background | Relevance to your project |
|---|---|---|---|
| [Panel A] | [Name] | [methods, topics] | [high/medium/low — one sentence] |
```

5. Suggest the top 2–3 panels with a rationale sentence for each
6. Save to `.neuroflow/grant-proposal/panels/panel-analysis-[funder]-[date].md`
7. Note which panels are most relevant — use their terminology and methodological priorities when drafting the proposal

---

## Step 1 — Build inspiration map (if previous grants provided)

If the user provided previous grant applications in the interview:

1. Read each provided grant document
2. Map its sections to the new grant's sections — build a cross-reference table:

```
| New grant section        | Previous grant A           | Previous grant B           |
|--------------------------|----------------------------|----------------------------|
| Specific Aims            | Section 1 (pp. 1–2)        | Introduction (pp. 1–3)     |
| Background & Significance| Literature Review (pp. 3–6) | Background (pp. 2–5)       |
| Innovation               | Novelty section (p. 7)     | Not present                |
| Approach                 | Methods (pp. 8–14)         | Research Plan (pp. 6–12)   |
| Budget                   | Budget justification (p. 15)| Budget narrative (pp. 13–14)|
```

3. Save to `.neuroflow/grant-proposal/inspiration-map-[date].md`
4. When drafting each section, explicitly reference the corresponding inspiration section — pull framing, structure, and language from it (not content — just patterns and approach)

---

## Step 2 — Gather funder information

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

Report what you found and ask the user to confirm before proceeding.

---

## Step 3 — Confirm the brief

Display a full confirmation block before drafting:

```
Grant brief — please confirm before I start drafting:

• Research question: [from interview or ideation]
• Funder / Scheme: [name]
• Budget: [ceiling]
• Duration: [years]
• Deadline: [date]
• Objectives:
  1. [objective 1]
  2. [objective 2]
  3. [objective 3]
• Sections to draft: [list with page/word limits]
• Review criteria: [list]
• Inspiration grants: [list, or "none"]
• Panel target: [panel name, or "not researched"]

Type "confirmed" to proceed, or correct any item.
```

Do not draft until confirmed.

---

## Step 4 — Build a proposal outline

Based on the funder requirements and the research idea:

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
   4f. Expected outcomes and timelines
   4g. Potential limitations and alternatives
5. Budget and justification                 [X pages]
6. Timeline                                 [X pages / Gantt chart]
7. Team and environment                     [X pages]
8. References / Bibliography
```

Adapt to the actual funder. Ask the user to approve the outline.

---

## Step 5 — Draft section by section

Work through sections in order. **Before each major section, re-read `objectives.md` and confirm all objectives are represented.** For each section:

1. State the section name, page limit, and review criteria that apply to it
2. If an inspiration map exists: note which inspiration section corresponds to this one
3. Draft the section content
4. Show word count: `Word count: NNN / NNN limit`
5. After drafting, ask:
   - `"revise"` — iterate
   - `"next"` — proceed
   - `"save"` — write to file
   - `"expand [topic]"` — add more depth

### Section-specific guidance

**Specific Aims / Project Summary**
- Hook: state the gap, significance, and impact in sentence 1
- List all objectives with a clear verb (characterize, determine, test, develop, validate)
- End with expected outcomes and long-term impact

**Background and Significance**
- State of the art: what is known, what is not
- Frame the gap in terms the funder cares about
- End with a crisp statement of why your study changes the field

**Innovation**
- Lead with the strongest novel element
- Contrast with existing approaches: "Unlike X, our approach does Y because Z"
- Use `sequentialthinking` to structure the logical chain before drafting

**Approach**
- Cover each objective explicitly — verify none are missing
- For neuroscience grants: modality, preprocessing pipeline, statistical model, power analysis
- Address limitations proactively; propose concrete alternatives
- Use `sequentialthinking` to build the logical argument chain before drafting

**Budget**
- Ask for: personnel (FTE), equipment, consumables, travel, indirect costs rate
- Year-by-year table with justification prose for each line

**Timeline**
- Map all objectives to quarters or months
- Show dependencies between objectives

**Team and Environment**
- PI and co-investigators with role descriptions
- Institutional resources: scanners, clusters, core facilities

---

## Step 6 — Quality checks before saving

Before saving, verify:

- [ ] Every objective has a measurable outcome — and all N objectives appear in both Aims AND Methodology
- [ ] All methods are feasible within the budget and timeline
- [ ] Power analysis present
- [ ] Limitations and alternatives addressed for each objective
- [ ] Word / page counts within limits for all sections
- [ ] Funder review criteria explicitly addressed in text
- [ ] Panel terminology reflected in framing (if panel research was done)
- [ ] Preliminary data supports feasibility
- [ ] References formatted in funder-required style
- [ ] Budget arithmetic is correct

Report the checklist to the user and fix any issues before saving.

---

## Step 7 — Save and update memory

Save the completed grant document to `.neuroflow/grant-proposal/grant-[funder]-[date].md`.

Update `.neuroflow/grant-proposal/flow.md`. Append `##` milestone to `.neuroflow/sessions/YYYY-MM-DD.md`. Update `project_config.md` with funder, scheme, and deadline if not already present — confirm with the user first.

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
