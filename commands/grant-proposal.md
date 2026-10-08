---
name: grant-proposal
description: Write a full grant application. Starts with an interactive interview, discovers ideation outputs, accepts funding call documents or URLs, adapts to any funder (NIH, ERC, Wellcome, national research councils, etc.), and drafts section by section with word-count tracking.
phase: grant-proposal
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/objectives.md         # read if exists — project objectives cornerstones
  - .neuroflow/ideation/             # all .md files discovered in Step 0
  - .neuroflow/grant-proposal/flow.md
  - .neuroflow/sessions/             # Step 6b: evidence for the AI-use declaration
writes:
  - .neuroflow/grant-proposal/
  - .neuroflow/grant-proposal/flow.md
  - .neuroflow/objectives.md         # written/updated after interview confirms objectives
  - .neuroflow/reasoning/grant-proposal.jsonl
  - .neuroflow/timeline.md           # the deadline
  - .neuroflow/sessions/YYYY-MM-DD.md
lifecycle: full
produces:
  - .neuroflow/grant-proposal/grant-[funder]-[date].md
  - .neuroflow/objectives.md
next:
  - finance
  - preregistration
---

# /grant-proposal

Read the `neuroflow:phase-grant-proposal` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` (and open with the version notice when the project's `plugin_version` is missing or older than the running neuroflow's version in `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` — **Command lifecycle**, step 3), `flow.md`, and `objectives.md` (if it exists) before starting.

**Style editing is opt-in.** Run `neuroflow:humanizer` on a section only when the person asks for it — a style edit (filler, rhythm, register), never a way to hide that AI helped write the text. AI assistance is declared in Step 6b.

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
| Funding body | NIH, ERC, Wellcome Trust, Horizon Europe, a national research council or science foundation, a foundation, institutional |
| Scheme / mechanism | R01, Starting Grant, Discovery Award, standard project grant |
| Total budget ceiling | e.g. $500 K direct costs, €1.5 M total |
| Language and format | Required language(s) of each part, template, font and page rules — national funders often want parts in the national language and others in English |
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
4. Show word count: `Word count: NNN / NNN limit` — counted with a tool (`wc -w` on the section file, or the text piped to `wc -w`), never estimated. Where the limit is in pages, say so: the word count is only a guide, and the page count is checked in the funder's template.
5. After drafting, ask:
   - `"revise"` — iterate
   - `"next"` — proceed
   - `"save"` — write to `.neuroflow/grant-proposal/draft-[funder]-[date]-[section].md`
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
- Shared infrastructure the project will rely on (compute allocations, core facilities, data repositories, hosted model gateways): how access is secured, and the acknowledgement each one requires in later papers — take the wording from the provider, never invent it

**Data Management Plan (DMP) — required by every supported funder**
- Draft as a standalone document, not a proposal section: `dmp-{funder}-{YYYY-MM-DD}.md` in `.neuroflow/grant-proposal/`
- Use the funder's template structure:
  - **NIH (DMS Policy, 2023)** — six elements: data type/amount, related tools & software, standards (name BIDS explicitly for neuroimaging/ephys), preservation & access (name the repository — OpenNeuro/OSF/Zenodo — and timeline), access/reuse restrictions and their justification, oversight
  - **Horizon Europe / ERC** — DMP template on the FAIR principles: findable (DOI, metadata), accessible (repository, embargo), interoperable (formats, standards), reusable (license); open-research-data is the default, opt-outs must be justified
  - **Wellcome** — outputs management plan: outputs foreseen, sharing venue and timing, resources needed
  - Other funders: ask for the template, or default to the FAIR structure
- Fill from project memory: modality and expected volume from `project_config.md`, BIDS from the `neuroflow:bids` skill, consent-based restrictions from `.neuroflow/ethics/` if present
- **Promise only what the workflow can deliver** — the repositories and licenses named here are what `/output --archive` will later execute; do not promise a repository or timeline the user has not confirmed
- Cross-check: sentinel compares the DMP's promises against actual practice during audits

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
- [ ] References formatted in funder-required style, cited only from the project library (`.neuroflow/ideation/papers/` or the person's reference manager)
- [ ] Reference DOIs checked: `python <phase-grant-proposal skill base dir>/../phase-paper/scripts/cite_check.py <the draft-*.md section files> --library .neuroflow/ideation/papers --cache .neuroflow/grant-proposal/doi-cache.json`. Exit 0: "DOI resolves; no retraction notice found in Crossref as of {date}". Exit 1: settle each flagged DOI with the person. Exit 2: no network, mark it unchecked. Never "verified".
- [ ] Budget arithmetic is correct
- [ ] AI-use declaration drafted (Step 6b), if the funder asks for one

Report the checklist to the user and fix any issues before saving.

---

## Step 6b — AI-use declaration

Many funders ask applicants to declare generative-AI use, and some limit it. Read the call text for the policy and the required wording. Draft the declaration from evidence, never from memory: `[grant-proposal]` lines in `.neuroflow/sessions/` (this machine only — ask co-applicants about their own sessions), which sections were drafted or edited with the model, whether the humanizer ran, and what the applicants did themselves (the ideas, the decisions, checking every claim, the final text). Name the tool ("Claude, via Claude Code with the neuroflow plugin"). Never under-state or over-state, and never quote session lines. Ask the person to confirm it, then save it as `.neuroflow/grant-proposal/ai-use-statement-[funder]-[date].md`.

---

## Step 7 — Save and update memory

Save the completed grant document to `.neuroflow/grant-proposal/grant-[funder]-[date].md`.

Update `.neuroflow/grant-proposal/flow.md`. Append a session line `## HH:MM — [grant-proposal] Draft saved: {funder} {scheme}`. Add the deadline to `timeline.md`, and note funder and scheme in the free-text part of `project_config.md` (below the frontmatter — they are not frontmatter keys) if not already there — confirm with the user first. The choice of funder and scheme is a reasoning entry in `.neuroflow/reasoning/grant-proposal.jsonl`.

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
| Horizon Europe | EIC Pathfinder | €3M, 4 yr | Concept, Methodology, Impact | Novelty, Scientific approach, Impact |
| National research council / science foundation | Standard project grant | Varies — read the call | Summary, state of the art, objectives, methodology, feasibility, budget | Originality, feasibility, team, budget — read the call |
