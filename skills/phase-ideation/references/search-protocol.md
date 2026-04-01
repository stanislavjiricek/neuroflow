# Literature Search Protocol

> **This protocol is executed by the main agent inline — no sub-agents are spawned.**
> Follow every step below directly. If you are the agent running `/ideation` or the `ideation` agent, you perform these searches yourself.

---

## Step 0 — MCP health check

Before doing anything else, call the bioRxiv MCP search tool with a minimal date-range query (e.g. a single recent day, `max_results=1`) to verify the `biorxiv` MCP server is reachable and its tools are registered in context.

- If this call **succeeds**: continue to the search strategy below.
- If this call **fails** or the tool is not available (tool not found, MCP error, or any exception):
  - Emit exactly:
    > ❌ **bioRxiv MCP server unavailable. Cannot proceed with literature search.**
    > Run `claude mcp list` to confirm the `biorxiv` server is ✓ Connected, then retry.
  - **Stop the literature search immediately. Do NOT fall back to shell scripts, Python, curl, wget, or any other workaround.**

---

## Search strategy

1. Run PubMed and bioRxiv searches **in parallel** — fire both tool calls simultaneously. Wait for both to complete before proceeding. CrossRef, Semantic Scholar, and arXiv fallbacks are run sequentially after the parallel pair completes.
2. **bioRxiv API limitation — handle explicitly**: The bioRxiv MCP server uses a date-range API that does not support keyword filtering. If bioRxiv returns zero results:
   - Emit this warning **immediately** (not in a footnote):
     > ⚠️ **bioRxiv keyword search returned 0 results.** The bioRxiv API does not support keyword filtering — it is limited to date-range queries. Attempting CrossRef, then Semantic Scholar, then arXiv as sequential fallbacks.
   - Query fallback sources **one at a time in this order** — do not fire them simultaneously:
     1. **CrossRef first**: query `https://api.crossref.org/works?query=<url-encoded-query>&filter=type:posted-content&rows=20`
     2. **Semantic Scholar second** (only if CrossRef returns fewer than 10 results): query `https://api.semanticscholar.org/graph/v1/paper/search?query=<url-encoded-query>&fields=title,authors,year,abstract,externalIds&limit=20`
     3. **arXiv third** (only if previous sources together return fewer than 10 results): query `https://export.arxiv.org/api/query?search_query=all:<url-encoded-query>&max_results=20`
   - Present results from these fallback sources under a **CrossRef / Semantic Scholar / arXiv** section, marked ⚠️ PREPRINT where applicable
3. **Semantic Scholar rate-limit handling**: If the Semantic Scholar API returns a 429 (Too Many Requests) or any rate-limit error, wait 3 seconds and retry once. If still rate-limited, skip Semantic Scholar for this session and emit this warning **immediately**:
   > ⚠️ **Semantic Scholar rate-limited after retry.** Results from this source are unavailable for this session. Coverage may be reduced. CrossRef and arXiv have been queried as substitutes.
4. **PubMed query-overlap detection and auto-diversification**: After PubMed results are collected, check coverage:
   - If fewer than 15 unique papers are returned across all PubMed queries (a rough lower bound for a field with 20–50+ relevant works), OR if two or more queries share >80% of their results (by DOI or title, indicating query synonymy rather than genuine coverage), automatically generate 2–3 diversified alternative queries (different MeSH terms, synonyms, narrower/broader scope, related methodology terms) and run them **one at a time** — do not fire multiple diversified queries simultaneously.
   - Emit this notice **before the results list** if diversification was triggered:
     > ⚠️ **PubMed coverage thin or queries overlapping** — auto-generated N diversified queries. [list the extra query strings used]
   - If diversified queries still return fewer than 10 unique papers, note this prominently in the coverage summary.
5. If results are still thin or too broad after the above steps, generate further alternative queries and run those too
6. Deduplicate across sources
7. **Coverage summary — emit before the results list**: Before showing any paper results, always print a coverage block:

   ```
   ## Search coverage — [topic] — [date]
   | Source              | Status        | Results |
   |---------------------|---------------|---------|
   | PubMed              | ✅ ok / ⚠️ thin / ❌ failed | N papers |
   | bioRxiv             | ✅ ok / ⚠️ 0 results (API limitation) | N papers |
   | CrossRef (fallback) | ✅ used / — not needed | N papers |
   | Semantic Scholar    | ✅ ok / ⚠️ rate-limited / — not needed | N papers |
   | arXiv (fallback)    | ✅ used / — not needed | N papers |
   Total unique papers after deduplication: N
   Query diversification: [not needed | triggered — N extra queries run]
   ```

   Any ⚠️ or ❌ rows must also appear as inline warning blocks immediately after the table (see step 2 and 3 above). Do not bury coverage failures in footnotes.

8. **Journal area identification**: read `skills/phase-ideation/references/journal-defaults.md` (included in the neuroflow plugin). Match the query topic to one of the eight neuroscience areas defined there (EEG/MEG/electrophysiology, fMRI/neuroimaging, computational neuroscience, systems neuroscience/circuits, clinical neurophysiology, cognitive neuroscience, network neuroscience, information theory/causality). Use this to:
   - Surface the 2–3 highest-impact journals for that area in a **Journal fit** note appended to the results.
   - Prioritise papers from those top journals in output ordering when relevance is equal.
   - Suggest which preprint server (bioRxiv / medRxiv / PsyArXiv) is most appropriate for the area.

---

## Output format

Return results in up to three sections — PubMed first, bioRxiv second (or CrossRef / Semantic Scholar / arXiv if bioRxiv returned zero results) — followed by a brief overall summary.

For each paper:

```
**Title** (Year) — Authors et al.
*Journal or source* | DOI: ...
One sentence describing the key finding or contribution.
⚠️ PREPRINT    (bioRxiv only)
🔒 PAYWALLED   (if full text is not open access)
```

End with a **2–3 sentence Summary** across both sources: what the literature shows, where the gaps are.

---

## Paper stub creation (always runs after search)

After returning the results list, **always** save a `.md` metadata stub for every paper to `.neuroflow/ideation/papers/`. Do NOT download PDFs automatically — present the results first, then ask the user which papers to download.

### Stub format

For every paper in the results list, save a `.md` metadata stub to `.neuroflow/ideation/papers/[stem]/[stem].md` using this template. Set `full_text_available: false` and `reason: not-yet-downloaded`.

**Filename stem**: `[FirstAuthorLastName]-[Year]-[SlugTitle]` — the slug is the paper title lower-cased, punctuation stripped, spaces replaced with hyphens, truncated at 60 characters; if the author's last name contains non-ASCII characters, transliterate them (e.g. "Müller" → "muller"); if the year is missing use "unknown". Apply DOI disambiguation if needed: if titles are identical in the first 60 characters and a collision occurs, append the last 6 characters of the DOI (dashes stripped).

```markdown
---
title: "[Full paper title]"
authors: "[Author1, Author2, ...]"
year: [YYYY]
journal: "[Journal or source name]"
doi: "[DOI; if the DOI could not be verified via the API, write 'unverified: [raw DOI string]']"
pmid: "[PMID or omit if unavailable]"
pmcid: "[PMCID or omit if unavailable]"
preprint: [true | false]
full_text_available: false
reason: "not-yet-downloaded"
---

# [Full paper title]

**Authors:** [Author1, Author2, ...]
**Year:** [YYYY]
**Journal/Source:** [Journal or source name]
**DOI:** [DOI]
**Status:** Not yet downloaded — metadata stub created from search results

## Abstract

[Full abstract text as returned by the search API, or "Abstract not available" if none exists.]

## Notes

- Metadata-only stub created during literature search on [date]
- To download: re-run /ideation and select this paper for download, or use the standalone scholar agent
```

---

## Resume detection (for user-requested downloads)

Before downloading anything, check which papers are already present:

1. List all folders and files currently in `.neuroflow/ideation/papers/`
2. For each paper in the results list, compute its expected filename stem (see above)
3. For each paper, check the expected stem folder:
   - If it contains `[stem].pdf` or `[stem].txt` → real full-text download; mark `⏭️ already downloaded` and skip
   - If it contains only `[stem].md` (no `.pdf` or `.txt`) → check the stub's `reason` field:
     - `reason: not-yet-downloaded` → eligible for download
     - `reason: unavailable` → all sources exhausted; mark `⏭️ unavailable (metadata cached)` and skip
     - `reason: failed` → previous attempt errored; retry the download
     - `reason: paywalled` → skip unless user explicitly requests it

---

## Download procedure

**Batching rule**: Process papers in batches of **2 simultaneously**. Complete each batch before starting the next. Do not attempt all papers at once.

**Timeout rule**: if a download tool call does not return within ~20 seconds or returns an error/empty response, mark that source as failed immediately and move to the next source. Do not wait or retry a timed-out call.

For each paper not yet present, in order:

1. If the paper is marked `🔒 PAYWALLED`, save a partial metadata file marked as paywalled, note it as `⛔ skipped — paywalled (metadata saved)`, and move on
2. Otherwise, attempt to fetch the full text by trying each source in this priority order:
   - **Source 1 — Unpaywall**: query the Unpaywall API for the DOI to obtain an open-access PDF URL, then call `download_paper` with that URL
   - **Source 2 — PubMed Central**: if a PMCID is available, call `download_paper` with the PMC PDF URL (`https://www.ncbi.nlm.nih.gov/pmc/articles/[PMCID]/pdf/`). **Never use `get_full_text_article`** — it returns the full article body as text into the context window and is extremely token-expensive.
   - **Source 3 — bioRxiv direct**: if the paper is a bioRxiv preprint, use the direct PDF link from the search result with `download_paper`
3. Move to the next source immediately if a source returns no PDF, a 404, or an access-denied response
4. If all three sources fail, **pause 2 seconds as a backoff, then retry the full source chain once** before giving up
5. If a PDF or plain-text was successfully retrieved, save to `.neuroflow/ideation/papers/[stem]/[stem].pdf` (or `.txt`). **Never save a metadata `.md` stub and call it a download.**
6. Mark the paper with one of:
   - `✅ downloaded` — a `.pdf` or `.txt` full-text file was confirmed saved
   - `❌ unavailable` — all sources exhausted; save a partial metadata file with `reason: unavailable`
   - `⚠️ failed` — network/tool error; save a partial metadata file with `reason: failed`

### Partial metadata file template

For `❌ unavailable`, `⚠️ failed`, and `⛔ paywalled` outcomes, save a `.md` file using the same stub template above, but set the `reason` field appropriately (`unavailable`, `failed`, or `paywalled`) and update the Status and Notes sections to match.

---

## Download summary

After all download attempts, report:

```
## Download summary — [topic] — [date]
✅ [n] downloaded (PDF/text)   ⏭️ [n] already downloaded   ⏭️ [n] unavailable (metadata cached)   ❌ [n] unavailable (metadata saved)   ⚠️ [n] failed (metadata saved)   ⛔ [n] skipped — paywalled (metadata saved)

Downloaded files saved to: .neuroflow/ideation/papers/ (each paper in its own named subfolder)
✅ = full-text PDF or plain-text file confirmed saved. Metadata-only .md stubs are NEVER counted as downloaded.
```

If any papers are marked `⚠️ failed`, list them:

```
### Papers to retry (⚠️ failed)
- [Title] — DOI: [doi] — reason: [brief error description]
  Metadata saved to: .neuroflow/ideation/papers/[stem]/[stem].md
```

Then add: *"To resume: re-run `/ideation` → explore literature with the same query. Papers already downloaded as PDF/text will be skipped automatically."*

---

## Follow-up actions

After returning results and saving stubs, ask the user:

> **Which papers would you like to download for full-text analysis?**
> Enter numbers (e.g. `1,3,5`), `all`, or `skip` to proceed with abstract-only analysis.

Then offer:

- `"literature-review"` — run the `literature-review` agent on papers in `.neuroflow/ideation/papers/`
- `"save"` — save the result list as `literature-[topic]-[date].md` in `.neuroflow/ideation/`
- `"summarize"` — produce a deeper synthesis: main findings, methodological patterns, open questions

---

## Hard constraints

- **NEVER** fall back to shell scripts, Python scripts, `curl`, `wget`, or any other workaround if MCP tools are unavailable.
- If a `tools_changed_notice` fires mid-session, stop immediately and emit:
  > ❌ **MCP tools changed or became unavailable mid-session. Stopping to avoid shell/script fallback.**
  > Run `claude mcp list` to confirm server status, then retry.
- Never make up a paper, author, or DOI
- If a DOI cannot be verified, mark it as unverified
- Always separate PubMed and bioRxiv results clearly
- Mark preprints — they are not peer-reviewed
- Always save `.md` metadata stubs for all results automatically — do not wait for the user
- Never download PDFs automatically — always ask the user which papers to download first
