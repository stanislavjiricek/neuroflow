---
name: paper
description: Unified manuscript writing and review command — drafts a neuroscience paper section by section through a brutal paper-writer → paper-critic loop, then carries it to publication with --submit (journal submission package), --revise (minimal-change reviewer rebuttal), and --abstract (conference abstract).
phase: paper
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/fails/core.md
  - .neuroflow/fails/science.md
  - .neuroflow/fails/ux.md
  - .neuroflow/ideation/flow.md
  - .neuroflow/data-analyze/flow.md
  - .neuroflow/paper/flow.md
  - skills/phase-paper/SKILL.md
writes:
  - .neuroflow/paper/
  - .neuroflow/paper/flow.md
  - .neuroflow/paper/critic-log.md
  - .neuroflow/reasoning/paper.json
  - .neuroflow/timeline.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /paper

Read the `neuroflow:phase-paper` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/paper/flow.md` before starting. Load upstream context from `.neuroflow/ideation/` (research question, hypothesis) and `.neuroflow/data-analyze/` (results summary, figures).

**Modes:** default (drafting loop, below) · `--submit` (submission package) · `--revise` (reviewer rebuttal — minimal-change discipline) · `--abstract` (conference abstract). The three publication-tail modes are specified after the drafting workflow.

Apply `neuroflow:humanizer` to every section draft before passing it to the critic — strip AI signatures, fix rhythm, and calibrate register so the prose reads as genuinely human-authored.

## What this command does

Produces a reviewed and approved manuscript — not a raw draft. Every section goes through a structured write→critique loop before it is saved. Nothing is written to disk without critic approval or an explicit user decision to accept an unresolved draft.

Gather four inputs before proceeding:

1. What is the target journal?
2. LaTeX or Word format?
3. Which section(s) should be drafted in this session, or should the full paper be attempted?
4. Is there a specific review focus, or should the critic apply its full eight-area methodology to every section?

---

## Workflow

### Step 1 — Activate paper-writer

Pass the four inputs (target journal, format, section scope, review focus) to the `paper-writer` agent. The agent reads upstream phase memory before drafting and presents each section as a standalone draft block.

Drafting order if doing the full paper: Methods → Results → Introduction → Discussion → Abstract (always last).

### Step 2 — Activate paper-critic (after each section draft)

Pass the section draft plus the rubric to the `paper-critic` agent. The critic applies the full `neuroflow:review-neuro` eight-area methodology (Language, Internal Consistency, Claim Support, Statistics, Methods Reproducibility, Contribution/Novelty, Literature Gap, Figure Review) and returns either `[STATUS: APPROVED]` or `[STATUS: REJECTED]`.

### Step 3 — Worker-critic loop (up to 3 iterations per section)

Follow the `neuroflow:worker-critic` loop protocol strictly:

```
paper-writer (Initial Draft mode) → draft v1
paper-critic (draft v1 + rubric)  → [STATUS: APPROVED] or [STATUS: REJECTED] + feedback

if APPROVED → proceed to next section
if REJECTED → paper-writer (Revision mode: draft v1 + feedback) → draft v2
              paper-critic (draft v2) → verdict

if APPROVED → proceed to next section
if REJECTED → paper-writer (Revision mode: draft v2 + feedback) → draft v3
              paper-critic (draft v3) → verdict

if APPROVED → proceed to next section
if REJECTED (3rd rejection) → halt loop for this section
                              present draft v3 and unresolved critique to user
                              append unresolved feedback to .neuroflow/paper/critic-log.md
                              ask user whether to continue with the next section or stop
```

**After each section verdict — immediately, before moving to the next section:**
- Append a one-liner to `.neuroflow/sessions/YYYY-MM-DD.md`: section name, verdict (`approved` / `halted at v3`), and iteration count
- If any editorial or framing decision was made (target journal confirmed, scope narrowed, section order changed), append to `.neuroflow/reasoning/paper.json`

### Step 4 — Save approved sections only

After each `[STATUS: APPROVED]` verdict, save the approved draft to `output_path` (default: `manuscript/`) — not inside `.neuroflow/`. Do not save a section until it is approved or the user explicitly accepts an unresolved draft.

Write loop state to `.neuroflow/paper/critic-log.md` after each iteration using the format defined in `neuroflow:worker-critic`.

---

## At end

- Save approved section drafts to `output_path` (from `.neuroflow/paper/flow.md`, default: `manuscript/`) — not inside `.neuroflow/`
- Update `.neuroflow/paper/flow.md`
- Update `.neuroflow/paper/critic-log.md` with final loop outcome for each section
- Confirm that session entries were appended to `.neuroflow/sessions/YYYY-MM-DD.md` after each section verdict during the session — if any were missed, append them now
- Confirm that any framing or scope decisions were written to `.neuroflow/reasoning/paper.json` as they occurred — if any were missed, append them now
- Update `project_config.md` if phase changed

---

## Mode: `--submit` — journal submission package

Assemble everything the journal wants besides the manuscript. Read the manuscript from `output_path`, the target journal from `project_config.md` (ask if unset), and `collaborators:` for authorship.

Produce, in `{output_path}/submission/`:

1. **Cover letter** (`cover-letter.md`) — one page: what the paper shows, why it fits this journal, confirmation of originality and no concurrent submission. Apply `neuroflow:humanizer`. No hype.
2. **Highlights / significance statement** — only if the journal requires one (check the journal's format requirements; ask the user if unknown).
3. **Data & code availability statements** — drafted from what actually exists: check `.neuroflow/data/` and `output_path` for repositories/DOIs recorded by `/output --archive`. Never claim availability that has not been set up — if nothing is archived yet, say so and suggest `/output --archive` first.
4. **CRediT author contributions** (`credit.md`) — one row per person from `collaborators:`, using the 14 standard CRediT roles. **Ask the user to assign or confirm roles — never guess authorship contributions.**
5. **Suggested reviewers** — ask the user; format name/affiliation/email as the journal requires. Never invent reviewer names.
6. **Submission checklist** (`checklist.md`) — journal-specific requirements (word limits, figure formats, reference style, ORCID, funding statements) with ✅/❌ against the current manuscript.

At end: register the package in `.neuroflow/paper/flow.md`, add the submission date to `timeline.md`, session milestone `## HH:MM — [paper] Submission package assembled for {journal}`.

---

## Mode: `--revise` — reviewer rebuttal

**THE PRIME RULE — nothing in this mode overrides it: changes are MINIMAL and address ONLY what a reviewer explicitly asked. Never anything else.**

The known failure mode of AI-assisted revision is doing too much — rewriting paragraphs that were fine, "improving" text nobody complained about, introducing new terms. In a rebuttal this is fatal: every unrequested change is something reviewers did not agree to and must re-review. Discipline:

1. **Only what was asked.** Each edit must map to one specific reviewer comment. If a change cannot be pointed back to a comment, it does not happen. No style fixes, no "while we're here" improvements, no reorganizing — even if the text could clearly be better.
2. **Unsure → ask.** If you are uncertain whether something falls inside a comment's scope, or you feel an extra change would help: **stop and ask the user.** Never decide alone to widen scope.
3. **Ambiguity check before any edit.** Read every reviewer comment for double meanings. If a comment has more than one plausible reading (e.g. "the connectivity analysis needs justification" — statistical justification, or motivation for using connectivity at all?), present the readings to the user and get their pick **before** touching the text. Do this comment by comment during planning, not mid-edit.
4. **Existing terminology only.** Use exactly the vocabulary the manuscript and project memory already use. Never introduce a new term, fact, abbreviation, or citation that is not already in the paper or explicitly provided by the user for this revision.
5. **Every change cross-referenced.** Each text change appears in the response document with its location ("Methods, p. 8, lines 143–147") and revised wording quoted. No silent edits — the response document and the manuscript diff must match 1:1, nothing in one without the other.
6. **Dry and direct responses.** Each reply: brief thanks at most, then directly what was changed (or the precise scientific reason for not changing, stated respectfully). No padding, no repeating the reviewer's comment back at length, no over-explaining.

**Workflow:**

1. User pastes or points to the decision letter. Split it into individually numbered comments (R1.1, R1.2, R2.1, …).
2. **Planning pass (no edits yet):** for each comment, classify — `text change` / `new analysis needed` / `rebut without change` / `ambiguous → ask user`. Present the full plan table and get user approval. Ambiguous comments are resolved with the user here.
3. Execute approved plan, one comment at a time. Minimal edit per comment. For `new analysis needed`, point at `/data-analyze` and mark the comment pending — never fabricate results.
4. Build `{output_path}/revision/response-to-reviewers.md`: each comment quoted once, response beneath, changed passages quoted with location. Save the revised manuscript alongside; keep the pre-revision version untouched (`-r1` suffix on the new files).
5. Final self-audit before showing the user: diff the manuscript — **every changed passage must trace to an approved comment. Anything untraceable gets reverted.** State the audit result explicitly.

At end: critic-log entry, session milestone per comment batch, reasoning entry for any rebut-without-change decision (these are scientific-direction decisions).

---

## Mode: `--abstract` — conference abstract

1. Ask: which conference, word limit, deadline, structured or free-form (and category/keywords if the conference uses them).
2. Draft from project memory (`data-analyze` results, `paper` drafts if any) — never claim results that memory does not contain. Apply `neuroflow:humanizer`. Respect the word limit exactly.
3. One `paper-critic` pass (single iteration — an abstract does not need the full 3-cycle loop; check claim support, internal consistency, and word count).
4. Save to `{output_path}/abstracts/abstract-{conference}-{YYYY-MM-DD}.md`; add the deadline to `timeline.md`; suggest `/poster` if the conference needs one.


