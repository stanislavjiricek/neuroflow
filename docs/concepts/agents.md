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
- Plugin version sync — `project_config.md` vs current `plugin.json`
- Subfolder name validation — no unrecognized or skill-named folders
- `CLAUDE.md` neuroflow reference check

See [`/sentinel`](../commands/sentinel.md) for full documentation.

---

### `sentinel-dev`

**Plugin development coherence guard.**

Audits the neuroflow plugin repository itself for structural consistency. Called by the `/neuroflow:sentinel` command when run inside the plugin repo (where `.claude-plugin/plugin.json` exists).

**Invoked by:** `/neuroflow:sentinel` (when `.claude-plugin/plugin.json` exists)

**What it checks:** it runs `scripts/automation/validate_pr.py` first — V1–V15, the same checks CI runs on every pull request — then the judgement checks (README hooks documentation, real names and institutions, concept-map placement, guards versus prose):

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
