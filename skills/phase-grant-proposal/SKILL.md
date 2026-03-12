---
name: phase-grant-proposal
description: Phase guidance for /grant-proposal with deep funder knowledge, neuroscience-specific grant tactics, review criteria alignment, and workflow orchestration.
---

# phase-grant-proposal

The grant-proposal phase translates a defined research question into a competitive, funder-ready application. It begins with automatic discovery of ideation outputs and ends with a fully drafted, word-counted, reviewer-aligned document saved to `.neuroflow/grant-proposal/`.

---

## Phase entry checklist

Before drafting anything, verify:

- [ ] Ideation output discovered (`.neuroflow/ideation/`) **or** research question confirmed with user
- [ ] Funder and scheme identified
- [ ] Page/word limits per section confirmed
- [ ] Review criteria retrieved (from funder website or call document)
- [ ] Deadline confirmed and logged

Never skip the discovery step. A grant without a clear research question is not draftable.

---

## Ideation discovery protocol

1. List all `.md` files in `.neuroflow/ideation/`
2. Read each file and extract:
   - Research question / hypothesis
   - Target modality (EEG, iEEG, fMRI, eye-tracking, ECG, behaviour)
   - Study population / participant criteria
   - Preliminary data or pilot results
   - Key references already identified
3. Present a 3–5 bullet summary to the user
4. If no ideation files exist: ask the user for the research question, any existing documents, or a URL to the funder call

---

## Funder knowledge base

> Budget figures, page limits, and scheme names are approximate typical values as of 2024–2025. Verify against the current call document or funder website before advising a user — requirements change each cycle.

### NIH (USA)
- **Mechanisms**: R01 (5 yr, $500K DC/yr), R21 (2 yr, $275K total), R03 (2 yr, $50K/yr), K awards (career development), U01 (cooperative agreement)
- **Key sections**: Specific Aims (1 page — the most critical), Research Strategy (12p for R01: Significance, Innovation, Approach), Human Subjects, Authentication of Resources, Bibliography
- **Review criteria** (scored 1–9, lower = better): Significance (gap and impact), Investigators (team track record), Innovation (conceptual or methodological novelty), Approach (rigor, feasibility, power analysis), Environment (facilities, collaborations)
- **Common weaknesses cited by study sections**: insufficient power analysis, vague alternatives for failed aims, overambitious scope, lack of preliminary data, budget not justified
- **Register on**: NIH eRA Commons; submit via Grants.gov or ASSIST

### ERC (EU)
- **Mechanisms**: Starting Grant (≤7 yr post-PhD, €1.5M), Consolidator (7–12 yr post-PhD, €2M), Advanced Grant (established PIs, €2.5M), Synergy Grant (2–4 PIs, €10M)
- **Key sections**: B1 Extended Synopsis (5p), B2 Full Proposal (Part B1 + B2 up to 15p for StG; 50p for AdG)
- **Review criteria**: Scientific excellence (primary), Impact (to science and society), Quality and efficiency of implementation (team, resources, management)
- **Common weaknesses**: proposal not ambitious enough for ERC standards, host institution not sufficiently described, no clear "frontier research" framing
- **Note**: ERC funds PI-driven curiosity research, not translational or applied work — frame accordingly

### Wellcome Trust (UK)
- **Mechanisms**: Discovery Award (£3–5M, 5 yr), Investigator Award (£1–3M, 5 yr), Sir Henry Wellcome (4 yr postdoc award), Collaborative Award
- **Key sections**: Flexible — Wellcome provides a template; typically Summary, Scientific rationale, Approach, Impact, Team, Budget
- **Review criteria**: Scientific opportunity (is this the right question?), Team (can they deliver?), Delivery (is the plan achievable?)
- **Note**: Wellcome values interdisciplinary approaches and expects explicit attention to open science (data sharing, preregistration)

### MRC (UK)
- **Mechanisms**: Programme Grant, Project Grant, Clinician Scientist Fellowship, Senior Research Fellowship
- **Key sections**: Case for Support (20p), Justification of Resources
- **Review criteria**: Importance (scientific and health impact), Quality and originality, Investigator capability, Resources

### GAČR (Czech Republic)
- **Mechanisms**: Standard Project (3 yr, ~5M CZK/yr), Junior Star (5 yr, ~9M CZK/yr), EXPRO excellence (5 yr, ~10M CZK/yr), International bilateral projects
- **Key sections**: Project summary (Czech + English, 600 words), State of the art, Objectives and hypotheses, Methodology, Feasibility, Budget justification, Timeline
- **Review criteria**: Originality and scientific quality, Feasibility, Team qualification, Budget adequacy
- **Note**: Czech-language applications required for domestic funding; international projects use English

### DFG (Germany)
- **Mechanisms**: Research Grants (Emmy Noether, Heisenberg, SPP priority programs, Collaborative Research Centres / SFB)
- **Key sections**: Work programme (10–15p), Preliminary work, Requested funds, Curriculum vitae (tabular, max 2p)
- **Review criteria**: Scientific quality, Originality, Feasibility, Training of junior researchers

### Horizon Europe (EU)
- **Mechanisms**: EIC Pathfinder (€3M, 4 yr), EIC Transition, EIC Accelerator (SMEs), MSCA Fellowships, ERC (separate)
- **Key sections**: Excellence (concept, methodology), Impact (strategy, pathways to impact), Implementation (timeline, resources, team)
- **Review criteria**: Excellence (novelty, scientific quality), Impact (significance, dissemination), Implementation (coherence, resources)

---

## Neuroscience-specific grant writing tactics

### Power analysis
- Always include a formal power analysis, even if approximate
- For EEG/ERP: reference pilot data or published effect sizes (Cohen's d for amplitude differences; cite the source)
- For fMRI: cite comparable studies for BOLD effect sizes; state voxel-wise threshold + cluster correction
- For behavioural measures: G*Power output with exact parameters (α, 1-β, effect size, allocation ratio)
- Reviewers from biostatistics panels will look for this — a missing power analysis is a common scoring weakness

### Preprocessing and analysis plan
- Name the software pipeline explicitly (MNE-Python, EEGLAB, SPM12, FSL, Brainstorm, ERPLAB)
- State: sampling rate, bandpass filter cutoffs, epoch window, artifact rejection method (ICA, threshold)
- For fMRI: TR, slice timing, HRF model, motion scrubbing threshold
- Reference BIDS compliance if relevant

### Participant recruitment
- State inclusion/exclusion criteria precisely
- Address any vulnerable populations explicitly (IRB / ethics committee considerations)
- If EEG: mention net type, cap system, electrode count
- Provide realistic recruitment numbers with dropout correction (plan for 20% attrition minimum)

### Preliminary data
- Show it early — link pilot data to feasibility
- If no preliminary data exists: substitute published proof-of-concept studies with your team's commentary
- Use figures — a single figure showing pilot ERP or BOLD effect is worth 200 words

### Budget granularity
- Break personnel costs to FTE fractions (PI 20%, postdoc 100%, RA 50%, etc.)
- List equipment by model number and price if >$5K items
- Consumables: EEG gel/electrode replacement, MRI contrast agents, participant payment
- Travel: conference attendance, site visits (justify each)
- Indirect costs: confirm the correct rate for your institution

---

## Review criteria alignment checklist

For each major funder, map every section of the proposal to the review criterion it addresses:

| Section | NIH criterion | ERC criterion | Wellcome criterion |
|---|---|---|---|
| Specific Aims | Significance + Innovation | Scientific excellence | Scientific opportunity |
| Background | Significance | Scientific excellence | Scientific opportunity |
| Innovation | Innovation | Scientific excellence | — |
| Approach | Approach + Environment | Quality of implementation | Delivery |
| Team | Investigators | Quality of implementation | Team |
| Budget | — | Quality of implementation | Delivery |
| Preliminary data | Approach | Scientific excellence | Delivery |

Use this mapping to ensure reviewer criteria are explicitly addressed in the text — never assume reviewers will infer alignment.

---

## Common fatal weaknesses (avoid these)

1. **Overambitious scope** — three aims that cannot be done in the funded period
2. **No power analysis** — instant credibility loss with quantitative reviewers
3. **Vague alternatives** — "if Aim 1 fails, we will modify our approach" is not acceptable
4. **Hypothesis-free Approach** — methods with no testable prediction attached
5. **Budget not justified** — line items without rationale
6. **Ignoring funder priorities** — NIH wants disease relevance; ERC wants frontier science; these are different framings
7. **Insufficient preliminary data** — especially for NIH R01; reviewers score feasibility based on prior work
8. **Poor Specific Aims page** — the single most influential page in a US grant; if reviewers are not sold after 1 page, scores suffer

---

## Workflow integration

### Reads from
- `.neuroflow/ideation/` — research question, literature, study design drafts
- `.neuroflow/project_config.md` — team, institution, phase, modality
- `.neuroflow/grant-proposal/flow.md` — prior grant context if resuming

### Writes to
- `.neuroflow/grant-proposal/grant-[funder]-[date].md` — full draft
- `.neuroflow/grant-proposal/flow.md` — funder, scheme, deadline, section status
- `.neuroflow/sessions/YYYY-MM-DD.md` — session log
- `project_config.md` — funder and deadline (with user confirmation)

### Connects to
- `/ideation` — if no research question exists, redirect the user there first
- `/experiment` — paradigm details flow into the Approach section
- `/preregistration` — registered analysis plan can be referenced in the Approach
- `/write-report` — funder progress reports use the same structure

---

## Output format standard

Each drafted section is presented as a standalone block:

```
## [Section name]  ([page limit] page / [word limit] words)

[Drafted content]

---
Word count: NNN / NNN limit    ✅ within limit  /  ⚠️ over by NNN words
```

After each section, offer:
- `"revise"` — rework the current section
- `"next"` — proceed to the next section
- `"expand [topic]"` — add depth to a specific part of the current section
- `"save"` — write current section to the draft file
- `"checklist"` — run the quality checklist against the current section

---

## Relevant skills

- `neuroflow:neuroflow-core` — lifecycle and `.neuroflow/` write rules (read first)
- `neuroflow:phase-ideation` — if user needs to define the research question first
- `neuroflow:phase-experiment` — paradigm design details for the Approach section
- `neuroflow:phase-preregistration` — link registered analysis plan

## Slash command

`/neuroflow:grant-proposal` — runs this workflow as a slash command.
