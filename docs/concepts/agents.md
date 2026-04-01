---
title: Agents
---

# Agents

**Agents are autonomous subprocesses launched by commands when deeper, focused work is needed.**

Unlike commands (which interact conversationally with you), agents operate semi-autonomously on a specific task — searching a database, auditing a folder, running a check. A command invokes an agent, the agent does the work, and the result flows back to you.

---

## Available agents

### `scholar`

**Academic literature research specialist.**

Searches PubMed then bioRxiv sequentially (with CrossRef / Semantic Scholar fallbacks) for a given topic and returns a clean, structured list of results.

**Invoked by:** `/neuroflow:ideation` (Explore literature mode)

**What it does:**

1. Runs the query sequentially: PubMed first, then bioRxiv, then fallbacks one at a time if needed
2. If results are thin, generates 2–3 alternative queries (synonyms, narrower/broader terms)
3. Deduplicates results across sources
4. Downloads open-access full text in batches of 2; skips paywalled papers (saves metadata stub)
5. Returns results in a structured format with markers:
   - ⚠️ `PREPRINT` — bioRxiv papers that have not been peer-reviewed
   - 🔒 `PAYWALLED` — papers without open-access full text

**Output format:**

```
PubMed results
──────────────
**N2 and P300 in auditory attention** (2023) — Smith et al.
*NeuroImage* | DOI: 10.1016/j.neuroimage.2023.001
Shows P300 amplitude reduces with cognitive load in selective attention tasks.

bioRxiv results
───────────────
**Noise effects on ERP** (2024) — Jones et al.
*bioRxiv* | DOI: 10.1101/2024.001
⚠️ PREPRINT — White noise as stressor reduces P300 in healthy adults.

Summary: P300 attenuation under high cognitive load is consistent in the
literature. White noise as a specific stressor is understudied — a gap exists.
```

**Follow-up actions after results:**

| Action | What happens |
|---|---|
| `"download"` | Fetch full text for open-access papers (skips paywalled) |
| `"save"` / `"md"` | Save as `literature-[topic]-[date].md` in `.neuroflow/ideation/` |
| `"summarize"` | Deeper synthesis: main findings, methodological patterns, contradictions |

**Rules:**
- Never fabricates papers, authors, or DOIs
- If a DOI cannot be verified, it is marked as unverified
- PubMed and bioRxiv results are always presented separately

!!! note "No credentials required"
    PubMed and bioRxiv search is handled by the `paper-search-mcp-nodejs` server — no credentials needed.

---

### `sentinel`

**Project coherence guard.**

Audits `.neuroflow/` for internal consistency and drift. Called by the `/neuroflow:sentinel` command when in a project repository (not a plugin repository).

**Invoked by:** `/neuroflow:sentinel` (when `.neuroflow/` exists)

**What it checks:**

- `flow.md` completeness — files listed vs files on disk
- Timestamp drift — stale `flow.md` vs recent file activity
- Broken references in `reasoning/` JSON files
- Phase consistency — active phase vs session logs vs folder activity
- Preregistration drift — planned analyses vs what was actually done
- Plugin version sync — `project_config.md` vs current `plugin.json`
- Subfolder name validation — no unrecognized or skill-named folders
- `CLAUDE.md` neuroflow reference check

See [`/sentinel`](../commands/sentinel.md) for full documentation.

---

### `sentinel-dev`

**Plugin development coherence guard.**

Audits the neuroflow plugin repository itself for structural consistency. Called by the `/neuroflow:sentinel` command when run inside the plugin repo (where `.claude-plugin/plugin.json` exists).

**Invoked by:** `/neuroflow:sentinel` (when `.claude-plugin/plugin.json` exists)

**What it checks:**

- Command folder names vs frontmatter `name:` fields
- Skill folder names vs `SKILL.md` frontmatter
- README tables vs actual files
- Version sync between `plugin.json` and all references
- Dead references (links to files that don't exist)
- Command frontmatter completeness

---

### Phase agents

**Specialist autonomous subprocesses, one per research phase.**

Each phase agent has deep domain knowledge scoped to its phase. It operates with a plan-first, confirm-before-executing discipline — it drafts a plan, shows it to you, and only proceeds after confirmation.

| Agent | Phase | What it does |
|---|---|---|
| `ideation` | ideation | Crystallises research questions via brainstorm, literature explore, formalise, or proposal modes |
| `grant-proposal` | grant-proposal | Structures proposals section by section for a target funder (NIH, ERC, Wellcome, MRC) |
| `experiment` | experiment | Paradigm design (PsychoPy), recording setup, and instrument configuration for EEG, fMRI, eye-tracking, ECG |
| `tool-build` | tool-build | Spec-first design and implementation of acquisition, real-time, LSL, BCI, and analysis pipeline tools |
| `tool-validate` | tool-validate | Timing, marker integrity, output format, and edge-case testing; writes validation plan before running any tests |
| `data` | data | Inventory → BIDS validation → conversion sequence; confirms modality before touching anything |
| `data-preprocess` | data-preprocess | Modality-aware preprocessing pipeline (EEG, fMRI, ECG, eye-tracking); documents all parameters before running |
| `data-analyze` | data-analyze | Statistical analysis — ERPs, time-frequency, connectivity, decoding, GLM; audits assumptions and applies multiple-comparison correction |
| `review` | review | Reads a colleague's paper and produces a structured referee report calibrated to the target journal; delegates to the `review-neuro` skill |
| `notes` | notes | Captures freeform input without interruption; reformats into a structured document only when asked |
| `write-report` | write-report | Synthesises `.neuroflow/` memory into a structured report for any phase or the full project |
| `brain-build` | brain-build | Spec-first design of neuron models and network topology for NEURON, Brian2, NetPyNE, NEST, tvb-library |
| `brain-optimize` | brain-optimize | Plans parameter sweeps or data-fitting runs; selects the right algorithm (grid, differential evolution, Bayesian, BluePyOpt) |
| `brain-run` | brain-run | Configures and executes simulation runs, sanity-checks outputs for silence, runaway activity, or NaN values; supports HPC job submission |

---

## How agents differ from commands

| | Commands | Agents |
|---|---|---|
| Invoked by | You (directly) | Commands (programmatically) |
| Interaction style | Conversational | Autonomous task execution |
| Scope | Phase-level work | Focused sub-task |
| Output | Phase subfolder in `.neuroflow/` | Result returned to calling command |
