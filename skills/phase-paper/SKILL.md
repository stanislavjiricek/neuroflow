---
name: phase-paper
description: Phase guidance for the neuroflow /paper command. Loaded automatically when /paper is invoked to orient agent behavior, relevant skills, and workflow for the unified paper phase — covering manuscript drafting and rigorous internal peer review in a single write→critique loop.
---

# phase-paper

The paper phase produces a reviewed and approved neuroscience manuscript. Every section draft is subjected to a brutal `paper-writer` → `paper-critic` loop before it is saved. Nothing reaches disk without critic approval or an explicit user decision to accept an unresolved draft.

## Approach

- Read upstream phase flows (ideation, data-analyze, experiment) before drafting — pull facts from memory, not from recall
- If `.neuroflow/data-analyze/multiverse.md` exists, every result that came from that search is exploratory: report it as exploratory, state in Methods how many specifications were tried, and never present it as confirmatory
- Confirm target journal before writing any section; it determines structure, length, style, and the critic's review persona
- Draft section by section in logical order; write the abstract last
- Distinguish what the results show (Results) from what they mean (Discussion) — flag if they become conflated
- **Cite only from the project library** — the papers in `.neuroflow/ideation/papers/` or the person's reference manager (an exported `.bib`). Never cite from memory. A claim that needs a reference the library lacks gets a `[CITE: what is needed]` placeholder and goes to the person (find the paper with `/ideation` or the `scholar` agent first)
- Every section draft is routed through the `paper-critic` agent using the full eight-area `neuroflow:review-neuro` methodology before saving
- Nothing is saved to `output_path` without a `[STATUS: APPROVED]` verdict or explicit user acceptance of an unresolved draft
- AI assistance is disclosed, never hidden: the humanizer is a style edit that runs only when the person asks, and `--submit` drafts the AI-use statement from the session and critic logs

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules
- `neuroflow:worker-critic` — defines the multi-agent revision loop protocol (max 3 iterations per section)
- `neuroflow:review-neuro` — the eight-area review methodology used by the `paper-critic` agent on every draft
- `neuroflow:humanizer` — optional style edit (filler, rhythm, register), only when the person asks for it; never automatic and never used to disguise AI involvement
- `neuroflow:notebooklm` — use when the user wants a podcast, slide deck, or infographic generated from manuscript sections

## Two-agent write→critique loop

The loop runs section by section, strictly following the `neuroflow:worker-critic` protocol:

1. **paper-writer** receives the task, upstream memory, journal target, project library, and rubric — returns an outline first (Outline mode); once the person approves it, drafts the section
2. **paper-critic** receives the draft and rubric — applies the full eight-area `review-neuro` methodology — returns `[STATUS: APPROVED]` or `[STATUS: REJECTED]` with specific actionable feedback
3. On `REJECTED`: **paper-writer** receives the critic's feedback — revises, addressing each bullet specifically
4. Loop repeats until `APPROVED` or three iterations are exhausted

Both agents run as subagents and cannot talk to the person: the orchestrator asks every question between spawns and passes the answers in the next prompt. Rounds 2 and 3 resume the same two agents (`neuroflow:worker-critic` → Revision mode).

On the third rejection the loop halts. The orchestrator presents draft v3 and the unresolved critique to the user, appends the critique to `.neuroflow/paper/critic-log.md`, and asks whether to continue with the next section.

**After each section verdict** (approved or halted), immediately — before moving to the next section:
- Append a session line `## HH:MM — [paper] {Section}: approved after {N} round(s)` (or `halted at v3`)
- If any framing or scope decision was made, append it to `.neuroflow/reasoning/paper.jsonl`

Write session and reasoning entries immediately after each section verdict — if the session is interrupted, the record must already reflect completed work.

## Critic standards

The `paper-critic` agent applies the FULL eight-area `neuroflow:review-neuro` methodology to every draft — including partial section drafts. The eight areas are:

1. **Language, Style & Terminology** — spelling, grammar, notation, neuroscience terminology errors, causality language
2. **Internal Consistency & Cross-Reference Integrity** — figure/table references, value consistency across sections
3. **Claim Support, Causality Language & Connectivity Interpretation** — overclaims, causality creep, FC over-interpretation, citations that do not support the sentence citing them
4. **Statistics, Network Inference & Multiple Comparisons** — effect sizes, correction procedures, null models, estimator specification
5. **Methods Reproducibility, Reporting Standards & Open Science** — COBIDAS/ARRIVE compliance, data/code availability
6. **Contribution, Novelty & Journal Fit** — novelty assessment, prior work comparison, journal fit, referee recommendation
7. **Literature Gap** — whether key prior work is cited; uses Zotero or `.neuroflow/ideation/papers/` as reference database
8. **Figure Review** — colormaps, font sizes, caption completeness, axis labels, figure–text consistency

A section is approved only if it would survive peer review at a top-tier neuroscience journal. The bar is not "acceptable draft" — it is "ready for submission".

## Journal recommendation

If the user has not set a target journal and requests recommendations:

1. Read `project_config.md` for modality, research question, and tools.
2. Read `.neuroflow/ideation/` if it exists for topic keywords and collected literature.
3. Use the `scholar` agent to search PubMed and bioRxiv for recent papers (past 3 years) in the same area. A journal is considered recurring if it appears in at least 3 of the top 20 results.
4. Rank 3–5 candidate journals using these criteria (in order of priority):
   - **Scope alignment** — does the journal publish this modality and methodology?
   - **Paper type fit** — empirical, methods, review, brief communication?
   - **Open access** — required, preferred, or irrelevant for this project?
   - **Typical length** — does the journal's word-count range suit the planned manuscript?
   - **Prestige vs. speed** — balance impact factor with typical time-to-decision
5. Present the shortlist in priority order. For each journal: name, publisher, one-sentence scope, why it fits this project, notable constraints (page limits, OA fees, data sharing policy).
6. Ask the user to pick or skip. If they pick, write `target_journal: <name>` in the `project_config.md` frontmatter — this is the authoritative location. Also write it to `.neuroflow/paper/flow.md` only if that file already exists — do not create the folder or file.

## Output paths

| What | Where |
|---|---|
| Approved section drafts, final manuscript | `output_path` (default: `manuscript/`) — outside `.neuroflow/` |
| Submission package (`--submit`), incl. AI-use statement | `{output_path}/submission/` |
| Revision + response to reviewers (`--revise`) | `{output_path}/revision/` |
| Conference abstracts (`--abstract`) | `{output_path}/abstracts/` |
| Phase memory, plans, critic logs | `.neuroflow/paper/` |
| Critic loop state per section | `.neuroflow/paper/critic-log.md` |
| Coauthor rounds (`--coauthor`) | `.neuroflow/paper/coauthor-round-N.md`, `coauthor-reply-N.md` |
| X-ray findings (`--xray`) | `.neuroflow/paper/xray-{file-stem}-YYYY-MM-DD.md` and `.jsonl` |
| Living paper skeleton (`--auto`) | `.neuroflow/paper/paper-ledger.md`, `skeleton.md`, `gaps.md` |
| DOI lookup cache (`cite_check.py`) | `.neuroflow/paper/doi-cache.json` |
| Scope and framing decisions | `.neuroflow/reasoning/paper.jsonl` |

Log any framing or scope decisions that differ from the original research question in `.neuroflow/reasoning/paper.jsonl` — ask before writing.

## Publication-tail modes

`/paper` also carries the manuscript past the draft: `--submit` (cover letter, availability statements, CRediT, AI-use statement, acknowledgements, pre-submission checks, checklist), `--revise` (reviewer rebuttal), `--coauthor` (a coauthor's Word comments), `--abstract` (conference abstract), plus `--xray` (sentence-by-sentence check) and `--auto` (living paper skeleton). Full specs live in `commands/paper.md`.

**The `--revise` prime rule is absolute: minimal changes, only what a reviewer explicitly asked, existing terminology only, every edit cross-referenced in the response document, ambiguous comments resolved with the user before editing, and when in doubt about scope — ask, never widen it alone.** No rule elsewhere in this skill overrides it. `--coauthor` and applied X-ray fixes follow the same rule.

## Scripts

Deterministic checks live in `scripts/` next to this skill (Python 3.10+, standard library; `--help` on each). Run them as `python <skill base dir>/scripts/<name>.py …`. Exit code 0 = clean, 1 = findings, 2 = usage or read error.

| Script | What it checks | Used by |
|---|---|---|
| `cite_check.py` | DOIs in .bib/.md/.tex/.docx resolve (Crossref, then doi.org); retraction, withdrawal, expression-of-concern and correction notices recorded in Crossref; preprints with a published version; with `--library`, cited DOIs missing from the project library. `--offline --cache FILE` works without network; `--cache FILE --max-age DAYS` looks up only DOIs that are new or older than DAYS in the cache. | `--submit`, `--xray`, `/grant-proposal`, `/poster`; the neuroflow mod after manuscript writes and weekly (setting `citations`) |
| `statcheck.py` | recomputes p from reported t, F, r, χ² and z with their df; skips p-values marked as corrected | drafting loop (before the critic), `--submit`, `--xray` |
| `revise_audit.py` | every changed sentence between an original and its `-r1` copy is quoted under a comment id in the response document, and every quoted change is in the manuscript | `--revise`, `--coauthor`, applied X-ray fixes |
| `docx_comments.py` | a .docx's comments (anchor text, threads, resolved flag) and tracked changes as a work table | `--coauthor` |

Labels name the test, never a virtue: "DOI resolves", "no retraction notice found in Crossref as of <date>", "reported p matches t and df" — never "verified". A clean run is not a review: a DOI that resolves can be cited for a claim the paper does not make, and many p-values (corrected, permutation, mixed-model) cannot be recomputed. Only DOI strings leave the machine. The scanner for hidden text in manuscripts and letters lives with review-neuro: `<skill base dir>/../review-neuro/scripts/hidden_text_scan.py`.

## Living paper skeleton (`--auto`)

The portable spec for `/paper --auto`. Three files in `.neuroflow/paper/`, listed in its `flow.md` (no new subfolder). They are project memory, not a manuscript: facts and quotes with their sources, no prose.

**Allow-list — the only sources `sync` reads:**

| Source | Feeds |
|---|---|
| `ideation/research-question.md`, `objectives.md` | Introduction brief: gap, aims |
| references the person marked as core, or the manuscript's own `.bib` | Introduction brief (not every scholar stub) |
| `preregistration/status.md`, the frozen prereg file, `registered-report.md`, `deviations.md` | Hypotheses and planned analyses, Deviations, freeze state |
| `ethics/status.md` | Methods: approval statement |
| `experiment/`, `tool-build/`, `tool-validate/` | Methods: procedure and apparatus |
| `data/`, `data-preprocess/` | Methods: participants (aggregate counts), acquisition, preprocessing; Results: data quality |
| `data-analyze/analysis-plan.md`, `analysis-summary.md`, `environment.md` | Methods: statistics and software; Results slots |
| `brain-build/`, `brain-optimize/`, `brain-run/` | Methods: model; Results: simulations |
| `reasoning/*.jsonl` | Discussion notes: limitations, deviations, decisions |

Never `sessions/` (local tier), never raw data, and never the `results/` or `figures/` trees — results enter only through the ledger.

<!-- nf-rule: PARTICIPANT-ROUTE -->
Participant-level files (per-participant QC rows, `participants.tsv`, anything identifying) are read only as `ai_processing` in `.neuroflow/ethics/status.md` allows (neuroflow-core → Integrity markers). The skeleton holds aggregate counts only, never a row per participant.

**`paper-ledger.md`** — an append-only table, one row per fact. A later row with the same key supersedes the earlier ones; rows are never edited or deleted.

| Key | Value | Source | Date | Status |
|---|---|---|---|---|
| `participants.n_final` | 24 (12 female, 18–35 years) | `data/data-inventory.md#participants` | 2026-09-30 | draft |
| `result.H1` | P300 larger in noise, t(23) = 2.45, p = .022, d = 0.50 | `data-analyze/analysis-summary.md#h1` | 2026-10-02 | final |

`Status` stays `draft` until the person declares a result final in the conversation; only then is a `final` row appended.

**`skeleton.md`** — rebuilt by `sync`, never edited by hand. First line: `<!-- generated by /paper --auto sync YYYY-MM-DD from paper-ledger.md: edit the sources, not this file -->`. Sections in IMRaD order:
- **Introduction (brief):** gap, aims, curated references — bullets, not prose
- **Hypotheses and planned analyses:** quoted word for word from the frozen preregistration as one locked block, with registry, DOI and freeze date from `status.md`
- **Methods:** fact bullets, each with a visible `[src: path#section]` tag
- **Deviations from the preregistration:** rendered from `deviations.md`
- **Results:** one slot per planned test, in preregistration order, filled only from `final` ledger rows; a slot without a final result says so, and null results stay visible. Everything else goes under **Exploratory (not preregistered)**
- **Discussion notes:** limitation and deviation bullets from the reasoning logs
- No Abstract

<!-- nf-rule: PREREG-FROZEN -->
The skeleton quotes the preregistration and never edits it: frozen preregistration files are not changed, and a change goes to `deviations.md` through `/preregistration`.

**`gaps.md`** — a table `| Gap | Checklist item | Fill with |`: each reporting item the ledger lacks (COBIDAS for MRI, COBIDAS-MEEG for EEG/MEG, ARRIVE 2.0 for animal work) with the command that would fill it. When `analysis-plan.md` and the preregistration disagree, that is a gap — "undeclared deviation? log it via /preregistration" — and the skeleton never reconciles the two.

**Frozen** — worked out from files on every run, however `/paper` was started:
- `{output_path}/submission/` or `{output_path}/revision/` exists → the whole skeleton is frozen
- `registered-report.md` records Stage 1 accepted or later → the Introduction brief and Methods are locked to the Stage 1 text

While frozen, `sync` reports what changed in the sources and rewrites nothing.

**Use in drafting:** default `/paper` passes the skeleton and ledger to `paper-writer` as facts with sources. They are never draft text, never draft v1, and the humanizer never runs on them.

## X-ray files (`--xray`)

`xray-{file-stem}-YYYY-MM-DD.md` — the annotated copy, one line per sentence, findings beneath with a checkbox:

```
# X-ray: results.md (2026-10-07)
Basis: statcheck.py (12 statistics), cite_check.py (31 DOIs, as of 2026-10-07), reading against review-neuro areas 1-8.
Unmarked sentences are not "passed"; paragraph- and section-level findings are listed under each section.

## Results
S3.1 (l. 41) The P300 amplitude was larger in the noise condition.
S3.2 (l. 42) This effect was significant, t(23) = 2.45, p = .002.
  - [ ] S3.2-1 red · Area 4 · statcheck: reported p does not match t and df (recomputed p = .022). Fix: NEEDS-SOURCE: the p-value from the analysis output.
Section findings:
  - [ ] S3-1 orange · Area 4 · six ERP comparisons; no correction for multiple comparisons is stated.
```

`xray-{file-stem}-YYYY-MM-DD.jsonl` — one finding per line:

```json
{"id": "S3.2-1", "scope": "sentence", "sentence": "S3.2", "line": 42, "severity": "red", "area": 4, "basis": "script:statcheck", "finding": "reported p does not match t and df (recomputed p = .022)", "fix": "NEEDS-SOURCE: the p-value from the analysis output", "status": "open"}
```

`scope` is `sentence`, `paragraph`, `section` or `paper`; `basis` is `script:statcheck`, `script:cite_check` or `model`; `status` is `open`, `accepted` (ticked) or `rejected`. A rejected scientific finding stays in the file with the person's reason, and a later X-ray raises it again only if the sentence changed.

## Slash command

`/neuroflow:paper` — runs this workflow as a slash command.
