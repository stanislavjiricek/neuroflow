---
name: ideation
description: The very beginning of a research project — brainstorm a research question, explore literature inline (no sub-agents), formalize an existing idea into a project definition, or produce a project proposal document.
phase: ideation
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/ideation/flow.md
  - .neuroflow/ideation/watch.md
  - ~/.neuroflow/user.yaml
  - skills/phase-ideation/SKILL.md
  - skills/phase-ideation/references/search-protocol.md
writes:
  - .neuroflow/ideation/
  - .neuroflow/ideation/papers/
  - .neuroflow/ideation/flow.md
  - .neuroflow/sessions/YYYY-MM-DD.md
  - ~/.neuroflow/user.yaml
lifecycle: full
produces:
  - .neuroflow/ideation/research-question.md
  - .neuroflow/ideation/papers/
  - .neuroflow/ideation/literature-review-*.md
next:
  - preregistration
  - grant-proposal
  - experiment
---

# /ideation

Read the `neuroflow:phase-ideation` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md`, `flow.md`, and `.neuroflow/ideation/flow.md` before starting.

## What this command does

Handles the very beginning of a research project. Five possible entry points — ask the user which applies:

1. **Brainstorm** — the user has a vague idea and wants to think through research questions
2. **Explore literature** — the user wants to search what is already known before committing to a question
3. **Formalize** — the user has an idea and wants to sharpen it into a concrete, testable research question
4. **Proposal** — the user wants to produce a written project proposal document
5. **Literature review** — papers have been retrieved (via the inline search protocol, or manually placed in `.neuroflow/ideation/papers/`) and the user wants to run the full 12-protocol analysis

If `project_config.md` already has a research question, confirm whether they want to build on it or start fresh.

If `.neuroflow/ideation/watch.md` exists and a query's `Last checked` date is more than 7 days old, offer the watch check in one line (see **Standing queries** below) — do not run it unasked.

---

## Steps

### Brainstorm / Formalize

Ask the user to describe their idea in any form — a phenomenon they want to study, a method they want to apply, a gap they noticed. Then:

1. Help them narrow it down to a testable research question
2. Identify the key variables (independent, dependent, confounds)
3. Identify the population and modality
4. State the hypothesis in one clear sentence

Save the result as `research-question.md` in `.neuroflow/ideation/`.

### Explore literature

**Zotero (optional, first time only):** before the first search of a session, check whether a Zotero MCP server is available (any `mcp__*zotero*` tool). If it is not, and no `zotero:` answer is recorded yet, ask once:

> Do you use **Zotero** for your reference library? If you connect it (a community `zotero-mcp` server — see `/setup`), I can search your existing library first and skip papers you already have — and, only when you say so, file new findings into a Zotero collection as well as the local stubs. **(y/n/later)**

Record the answer as `zotero: yes/no` in `~/.neuroflow/user.yaml` — it is a personal preference, not a project fact, so it never goes into `project_config.md` (an existing legacy `zotero:` line there still counts as the answer; leave it in place). Skip the question forever after `no`; `later` = ask again next session. **When Zotero is connected, the search flow adapts:**
- Step 0.5: search the user's Zotero library for the topic **before** any external search — known papers are marked 📚 *in your library* in the results table and excluded from download offers
- After downloads, ask whether to add the selected papers to a Zotero collection (named after the project) — nothing is added unless the person says yes
- Before invoking the `literature-review` agent (it has no Zotero access), you may read the person's existing Zotero notes/annotations for the selected papers and pass relevant excerpts in its brief

<!-- nf-rule: EGRESS-CONFIRM -->
**Zotero writes are opt-in, never a default.** Reading the library is fine; adding items, collections, notes, tags or attachments happens only after the person confirms that specific write in the same turn — never as a side effect of a search, a download or a review, and never by a standing "always save" setting.

Perform the literature search **directly — do NOT spawn a sub-agent**. Read and follow `skills/phase-ideation/references/search-protocol.md` step by step:

1. Run the MCP health check (Step 0 of the protocol)
2. Execute PubMed and bioRxiv searches in parallel, with CrossRef/Semantic Scholar/arXiv fallbacks as needed
3. Deduplicate results and emit the coverage summary table
4. Present the results list in the output format defined in the protocol
5. Save a `.md` metadata stub for every result to `.neuroflow/ideation/papers/` automatically
6. Ask the user which papers to download for full-text analysis (`1,3,5`, `all`, or `skip`)
7. If the user selects papers, follow the download procedure in the protocol (open-access routes only — never Sci-Hub; batches of 2, with resume detection)
8. After downloads complete (or are skipped), offer follow-up actions: literature-review, save, summarize, or watch

All search logic, output formats, stub templates, resume detection, and download procedures are defined in the search protocol reference — follow them exactly.

### Standing queries (watch list)

When the person wants to keep following a query (the `watch` follow-up, or they ask), first recommend free alerts — they arrive without any session: a **PubMed** saved search with e-mail alerts ("Create alert" under the PubMed search box; free NCBI account) and **bioRxiv / medRxiv** subject alerts or RSS feeds. Then offer to pin the query in `.neuroflow/ideation/watch.md`:

```markdown
# Literature watch

| Query | Tools | Pinned | Last checked | Free alert |
|---|---|---|---|---|
| P300 background noise | search_pubmed, search_crossref | 2026-10-07 | 2026-10-07 | PubMed alert, weekly |
```

**Watch check** (only when the person asks, or accepts the offer at the start of `/ideation`): re-run each pinned query with its tools from the search protocol — `sortBy: "date"` and a `year` range covering the time since `Last checked` (`days` for `search_biorxiv`); keep only hits whose record date is after `Last checked` and whose DOI or stem is not already in `.neuroflow/ideation/papers/`; present those new hits; update `Last checked`. New hits become stubs in `papers/` only for the papers the person picks — never automatically, because `papers/` is the literature-review corpus. Pinned queries are sent to the search services only when a check runs.

### Literature review

After papers have been retrieved and downloaded, run the full 12-protocol literature review using the `literature-review` agent:

1. Confirm the contents of `.neuroflow/ideation/papers/` with the user — the agent runs without asking questions, so this is the only confirmation
2. Invoke the `literature-review` agent with the confirmed paper list — it drafts each protocol, checks it with its own critic pass (rubric, mechanical checks first, up to 3 rounds), and saves it as a checkpoint in `.neuroflow/ideation/literature-review-[date]/protocol-NN.md`; an interrupted run resumes from those checkpoints when invoked again
3. The agent saves the compiled review to `.neuroflow/ideation/literature-review-[date].md` and returns a status table (protocol, status, rounds) — present it to the person
4. **Independent check (optional):** the agent's critic pass is a self-check. Offer an independent one in critic mode, for halted protocols, or for Protocols 7 and 12: spawn a general-purpose agent with this brief — *"You are the critic for one literature-review protocol. Read `[checkpoint path]` (the draft, with its rubric at the end) and the paper files in `.neuroflow/ideation/papers/`. Check every claim and citation against the paper files, then every rubric item. Do not edit files. Reply in the worker-critic format: `[STATUS: APPROVED]` + one sentence, or `[STATUS: REJECTED]` + one bullet per fix."* Append the verdict to `.neuroflow/ideation/critic-log.md` as `(critic: independent)`; on APPROVED set `critic: independent` in the checkpoint's frontmatter. On REJECTED, show the fixes and ask whether to re-run that protocol: if yes, delete its checkpoint and the compiled review, then invoke the agent again — it resumes, redoes the missing protocol and recompiles. Protocols that build on it (7 on 1–6, 12 on 2, 3 and 10) are redone only if the person asks.

The 12 protocols the `literature-review` agent runs:

1. **Intake Protocol** — map every paper by author + year + core claim; cluster by shared assumptions; flag contradictions
2. **Contradiction Hunter** — expose every head-to-head conflict between papers with evidence assessment
3. **Knowledge Gap Detector** — identify what all papers assume but never prove; missing methodologies; missing populations
4. **Timeline Builder** — reconstruct the intellectual history of the field from these papers alone
5. **Methodology Auditor** — extract study designs, sample sizes, and limitations; name what the dominant method cannot prove
6. **Citation Network Map** — identify which paper everything else builds on and which is the field's Achilles heel
7. **Lit Review Writer** — produce the prose literature review (opening → thematic body → transition → close)
8. **Devil's Advocate** — build the strongest case against the dominant consensus using the papers themselves
9. **Theoretical Framework Extractor** — map all theoretical models in use; name the missing lens
10. **Variable Map** — inventory every IV/DV/moderator; surface the never-studied variable combination
11. **Plain Language Translator** — rewrite the 5 most complex findings for a non-academic audience; identify the best headline
12. **Future Research Agenda** — write a 5-point agenda grounded in gaps, contradictions, and unreplicated variables

### Proposal

Produce a structured project proposal document covering: research question, background (from literature), hypothesis, planned methods, population, modality, timeline (rough). Save as `proposal-[date].md` in `.neuroflow/ideation/`.

---

## At end

- Update `.neuroflow/ideation/flow.md` with any new files created (including files in `papers/`, `watch.md`, the literature-review checkpoint folder and the compiled literature review)
- Append to `.neuroflow/sessions/YYYY-MM-DD.md` in the canonical format: `## HH:MM — [ideation] …`
- If a research question was defined or updated, update it in the markdown body of `project_config.md` — the research question is not a frontmatter key

---

## Integration reminders

Apply these checks at the points indicated above and whenever the user explicitly requests an integration:

**PubMed / bioRxiv** — available out of the box. No setup required.

**Miro** — if the user mentions Miro, asks to visualise a mind map, or wants to export ideas to a board:
1. Miro is available when a tool whose name contains `miro` exists in this session. Never read `integrations.json` for Miro, and never ask for the token.
2. If no such tool exists, show the `/neuroflow:setup` Step 2 instructions:

> ⚠️ **Miro not connected.**
> You add Miro once, yourself, for all your projects:
> 1. Create a personal access token at https://miro.com/app/settings/user-profile/apps → **Create new app** (or open an existing one) → **Token** → **Create token**.
> 2. In a **separate terminal** — not in this chat — run:
>    `claude mcp add --scope user miro -e MIRO_ACCESS_TOKEN=<your-token> -- npx -y @k-jarzyna/mcp-miro`
> 3. Restart Claude Code; the Miro tools then appear in every project.
>
> Please don't paste the token here.
>
> Would you like to set it up now?
> - **Y** — run `/neuroflow:setup`, which walks you through these steps; Miro is available after the restart
> - **n** — skip Miro; I'll describe what would be created instead
