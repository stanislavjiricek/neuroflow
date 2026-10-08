---
title: Agents
---

# Agents

**Agents are autonomous subprocesses launched by commands when deeper, focused work is needed.**

Unlike commands (which interact conversationally with you), agents operate semi-autonomously on a specific task — searching a database, auditing a folder, running a check. A command invokes an agent, the agent does the work, and the result flows back to you.

---

## Available agents

Nine agents ship with neuroflow: `scholar`, `sentinel`, `sentinel-dev`, `literature-review`, `paper-writer`, `paper-critic`, `poster-critic`, `autoresearch` and `flowie`. Their full definitions are under **Agents** in the navigation.

### `scholar`

**Academic literature research specialist.**

Searches PubMed and bioRxiv in parallel for a given topic — with CrossRef / Semantic Scholar / arXiv fallbacks through the same MCP server — and returns a clean, structured list of results.

**Invoked by:** ad-hoc literature searches outside the ideation workflow, and `/neuroflow` (journal recommendation step). Note: `/neuroflow:ideation` runs its literature searches **inline** — it does not spawn this agent.

**What it does:**

1. Runs PubMed and bioRxiv in parallel, then the fallbacks one at a time when bioRxiv returns little
2. If results are thin, generates 2–3 alternative queries (synonyms, narrower/broader terms)
3. Deduplicates results across sources
4. Downloads only open-access copies (preprint server, Semantic Scholar open-access link, publisher open access) in batches of 2, never Sci-Hub; papers without an open copy keep a metadata stub and a note to get them through the library
5. Returns results in a structured format with markers:
   - ⚠️ `PREPRINT` — bioRxiv papers that have not been peer-reviewed
   - 🔒 `PAYWALLED` — papers without open-access full text
6. Ends every reply with a `[REPORT downloaded=... files=... stubs=...]` line

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
- Each DOI is labelled with the check actually done (`doi_check`: from an API record, resolves on a date, does not resolve), never "verified"
- PubMed and bioRxiv results are always presented separately

!!! note "No credentials required"
    PubMed and bioRxiv search is handled by the `paper-search-mcp-nodejs` server — no credentials needed.

---

### `sentinel`

**Project coherence guard.**

Audits `.neuroflow/` for internal consistency and drift. Called by the `/neuroflow:sentinel` command when in a project repository (not a plugin repository).

**Invoked by:** `/neuroflow:sentinel` (when `.neuroflow/` exists)

**What it checks:** it runs `nf_check.py` first — the deterministic checks NF1–NF8 — then the judgement checks a script cannot make:

- `flow.md` completeness — files listed vs files on disk
- Timestamp drift — stale `flow.md` vs recent file activity
- Reasoning logs (`reasoning/*.jsonl`)
- Phase consistency — active phase vs session logs vs folder activity
- Preregistration drift — planned analyses vs what was actually done
- Plugin version — an older or missing `plugin_version` in `project_config.md` is reported with a pointer to `/neuroflow:migrate`; sentinel never edits the field
- Subfolder name validation — no unrecognized or skill-named folders
- `CLAUDE.md` neuroflow reference check

See [`/sentinel`](../commands/sentinel.md) for full documentation.

---

### `sentinel-dev`

**Plugin development coherence guard.**

Audits the neuroflow plugin repository itself for structural consistency. Called by the `/neuroflow:sentinel` command when run inside the plugin repo (where `.claude-plugin/plugin.json` exists).

**Invoked by:** `/neuroflow:sentinel` (when `.claude-plugin/plugin.json` exists)

**What it checks:** it runs `scripts/automation/validate_pr.py` first — V1–V15, the same checks CI runs on every pull request — then the judgement checks (README hooks documentation, real names and institutions, guards versus prose):

- Command folder names vs frontmatter `name:` fields
- Skill folder names vs `SKILL.md` frontmatter
- README tables vs actual files
- Version sync between `plugin.json` and all references
- Dead references (links to files that don't exist)
- Command frontmatter completeness

---

### `literature-review`

**Structured literature review of downloaded papers.**

Runs 12 analytical protocols on the papers in `.neuroflow/ideation/papers/`, from landscape mapping to a future research agenda. Each protocol is checked by a rubric critic pass inside the agent (a self-check) and saved as a resumable checkpoint in `.neuroflow/ideation/literature-review-[date]/`; `/ideation` can add an independent critic.

**Invoked by:** `/neuroflow:ideation`, after papers are retrieved

---

### `paper-writer`

**Manuscript writer for the unified paper phase.**

Drafts neuroscience manuscript sections from upstream project memory, the target journal's guidelines and the analysis results, citing only from the project library. It works inside the write→critique loop with `paper-critic` and revises until the critic approves or the loop runs out. It returns outlines, drafts and open questions instead of waiting for answers.

**Invoked by:** `/neuroflow:paper`

---

### `paper-critic`

**Hyper-critical manuscript reviewer.**

Applies the full eight-area `neuroflow:review-neuro` methodology to every section draft and returns `[STATUS: APPROVED]` or `[STATUS: REJECTED]` with specific, actionable feedback. It never writes content itself.

**Invoked by:** `/neuroflow:paper`, inside the write→critique loop

---

### `poster-critic`

**Conference poster reviewer.**

Judges the poster's LaTeX source, its compile log, a rendered preview and, when it exists, the compiled PDF against design, content and communication standards, including the QR code and LaTeX correctness. Returns `[STATUS: APPROVED]` or `[STATUS: REJECTED]` with actionable feedback.

**Invoked by:** `/neuroflow:poster`, in its worker-critic loop (at most 3 cycles)

---

### `autoresearch`

**The single managing agent of the improvement loop.**

Makes one focused change to a research artifact per iteration, judges it against the current best itself (no worker or evaluator fan-out), and keeps or reverts it. Its memory is a per-loop wiki it reads before and writes after every move. It never stops on its own judgement: it stops at the caps set in the loop's config, when you stop it, or after repeated errors. The protocol lives in the `neuroflow:autoresearch-protocol` skill.

**Invoked by:** `/neuroflow:autoresearch`

---

### `flowie`

**Personal identity agent.**

Reads your flowie profile (`~/.neuroflow/flowie/profile.md`) and shapes the work to who you are: your research stances, writing style and methodological preferences. At the start of a session it surfaces your active tasks for the current project and notes a stale sync. Profile data never appears verbatim in external-facing outputs such as manuscripts, grants or reports.

**Invoked by:** Claude, when a linked flowie profile should shape the work; see [Your profile](flowie.md)

!!! note "Per-phase agents were removed"
    Earlier versions listed one agent per research phase. Those agent files were never spawned by commands and have been removed: each command follows its phase skill directly.

---

## How agents differ from commands

| | Commands | Agents |
|---|---|---|
| Invoked by | You (directly) | Commands (programmatically) |
| Interaction style | Conversational | Autonomous task execution |
| Scope | Phase-level work | Focused sub-task |
| Output | Phase subfolder in `.neuroflow/` | Result returned to calling command |
