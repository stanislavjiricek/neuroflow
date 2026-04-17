---
name: wiki
description: Knowledge base skill — Karpathy-style LLM-maintained wiki at three levels (personal/flowie, project, team/hive). Handles ingest, query, lint, schema, and project-tagging workflows. Invoked by /flowie --wiki-* (personal), /wiki (project), /hive --wiki-* (team).
---

# wiki

A compounding knowledge base maintained by the LLM. Knowledge accumulates across sessions — cross-references are already there, contradictions already flagged, synthesis reflects everything ingested.

You never write the wiki yourself — the LLM writes and maintains all of it. You curate sources and ask questions.

**Three levels, one skill:**

| Level | Root path | Git repo | Who sees it |
|-------|-----------|----------|-------------|
| `flowie` | `.neuroflow/flowie/wiki/` | flowie private repo | owner only |
| `project` | `.neuroflow/wiki/` | project repo (shared) | all collaborators |
| `hive` | `{hive-repo}/wiki/` | hive org repo | whole team |

The wiki at each level serves a different purpose:
- **flowie** — personal knowledge, reading notes, method library, ideas across all projects
- **project** — shared project brain: experimental rationale, analysis decisions, literature relevant to the project, methods the team uses on this project
- **hive** — team knowledge: lab-wide methods, shared literature, cross-project synthesis, team epistemics

Git operations by level:
- `flowie`: `git -C .neuroflow/flowie ...`
- `project`: standard `git` in project root
- `hive`: `gh` CLI or GitHub API targeting hive org repo

---

## Structure

The wiki structure is identical at all three levels. The root path is resolved from the active level.

```
{wiki-root}/
├── index.md          ← catalog: every page, one-line summary, date, type (LLM maintains)
├── log.md            ← append-only chronological log (## [date] op | title)
├── schema.md         ← wiki conventions and LLM operating guide (auto-loaded on every operation)
├── raw/              ← immutable source documents (human drops files here, LLM never modifies)
│   └── assets/       ← locally downloaded images
└── pages/
    ├── concepts/     ← topic and idea pages
    ├── entities/     ← people, tools, datasets, organisms, locations
    ├── sources/      ← one summary page per ingested source
    ├── synthesis/    ← cross-source analysis, comparisons, evolving theses
    └── methods/      ← protocols, pipelines, analysis methods
```

### Why `pages/methods/`?

This subfolder is a neuroflow-specific addition to the Karpathy pattern. It accumulates your personal library of analysis methods, experimental protocols, and software pipelines — whether they worked or failed. Entries can be cross-referenced with `/fails` data and flowie project history.

---

## Wiki page format

Every file in `pages/` uses this frontmatter:

```yaml
---
title: Gamma Oscillations in Working Memory
type: concept              # concept | entity | source | synthesis | method
tags: [oscillations, working-memory, EEG]
projects: [project-name]   # links to flowie project registry — ALWAYS ask
phase: data-analyze        # most relevant neuroflow phase (optional)
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [raw/paper-xyz.md]              # raw files this page draws from
related: [pages/concepts/theta.md]       # explicit cross-references
status: current            # current | stale | draft
---
```

**`projects:`** is the key neuroflow addition. Every ingest, query, and add operation MUST ask which projects this relates to. Project source by level:
- `flowie` → read `.neuroflow/flowie/projects/projects.json`
- `project` → context is the current project itself (from `project_config.md`); ask if it relates to other flowie projects
- `hive` → read `{hive-repo}/projects/projects.json`

The user can always answer "none" — but you must always ask.

---

## Page types

| Type | Folder | Purpose |
|---|---|---|
| `source` | `pages/sources/` | One page per ingested source. Title = source title. Body = summary, key claims, quotes. |
| `concept` | `pages/concepts/` | A topic, idea, or theme. Updated each time a relevant source is ingested. |
| `entity` | `pages/entities/` | A person, tool, dataset, organism, or location. |
| `synthesis` | `pages/synthesis/` | Cross-source analysis. Could be a question answer filed back as a page. |
| `method` | `pages/methods/` | An analysis method, experimental protocol, or pipeline. Include warnings from `/fails` if applicable. |

---

## index.md format

The index is a catalog of all pages organized by type:

```markdown
# Wiki Index

Last updated: YYYY-MM-DD
Pages: N

## Sources
| Page | Summary | Updated | Sources |
|---|---|---|---|
| [Title](pages/sources/slug.md) | One-line summary | YYYY-MM-DD | 1 |

## Concepts
| Page | Summary | Updated | Sources |
|---|---|---|---|

## Entities
| Page | Summary | Updated | Sources |
|---|---|---|---|

## Synthesis
| Page | Summary | Updated | Sources |
|---|---|---|---|

## Methods
| Page | Summary | Updated | Sources |
|---|---|---|---|
```

Update `index.md` after every write operation. Read `index.md` first on every query.

---

## log.md format

Append-only. Each entry starts with a consistent prefix so it's grep-parseable:

```
## [YYYY-MM-DD] ingest | Source Title
## [YYYY-MM-DD] query | Question summary
## [YYYY-MM-DD] lint | N issues found
## [YYYY-MM-DD] add | Page title
## [YYYY-MM-DD] schema | Updated schema.md
```

Never remove or edit past entries. Always append.

---

## schema.md

The wiki's own operating guide — defines conventions specific to this user's wiki domain. Read `schema.md` at the start of every wiki operation. If it does not exist (first run), generate a starter schema by interviewing the user about their domain and preferences.

Starter schema template:

```markdown
# Wiki Schema

## Domain
{user's research domain, topics covered}

## Page conventions
- Titles: sentence case, specific (not "EEG" but "EEG in working memory tasks")
- Summaries in index.md: max 12 words
- Cross-references: wikilink style [[Page Title]] in body text, plus `related:` frontmatter

## Ingest conventions
- {user preferences for emphasis, what to summarize, what to skip}

## Tag vocabulary
{controlled list of tags used in this wiki}

## Project tags
{list of active flowie project names used as project: tags}
```

Evolve `schema.md` collaboratively over time. When the user says "always do X" or "don't do Y", update the schema.

---

## Operations

### Ingest workflow (`--wiki-ingest`)

1. Read `schema.md` (generate starter if missing)
2. Read the source — either a file path the user provides, or pasted text
3. Brief discussion: ask the user what to emphasize, any context they want captured
4. **Read `projects/projects.json`** → list active/recent project names → ask: "Which projects does this relate to?" (MANDATORY — always ask, even if connection seems tenuous)
5. Write `pages/sources/{slug}.md` with source summary and full frontmatter
6. Read `index.md` → identify up to 15 existing pages that this source is relevant to → update each (add cross-reference, note new evidence, flag contradictions)
7. For any concept/entity/method mentioned but lacking its own page: create it
8. Update `index.md` with all new and changed pages
9. Append to `log.md`: `## [date] ingest | {title}`
10. Git push (flowie standard pattern)

**After ingest:** ask whether this might add to `flowie/ideas.md` (if synthesis spans multiple projects) or update `profile.md` methodological stances (if it supports a strong new stance).

### Query workflow (`--wiki-query`)

1. Read `schema.md` + `index.md`
2. Identify relevant pages by type, tags, projects, and relevance to the question
3. Read those pages in full
4. Synthesize answer with citations (link to wiki pages, not raw sources)
5. Ask: "Would you like to file this answer as a wiki page?" — if yes, write to `pages/synthesis/{slug}.md` with full frontmatter, ask for project tags
6. Append to `log.md`: `## [date] query | {question summary}`
7. Git push if anything was written

### Lint workflow (`--wiki-lint`)

Run health checks and report findings:

1. **Orphan pages** — pages in `pages/` with no inbound `related:` links from any other page
2. **Stale pages** — pages where `updated` date is > 90 days ago and `status: current` (flag, not auto-fix)
3. **Missing concept pages** — concepts mentioned in 3+ pages but with no dedicated page in `pages/concepts/`
4. **Missing project tags** — pages whose body text references a known project name (from `projects.json`) but lacks it in `projects:` frontmatter
5. **Log/page mismatch** — `log.md` ingest entries for sources with no matching file in `pages/sources/`
6. **Cross-reference gaps** — if page A references page B in `related:`, verify B lists A in its own `related:` (bidirectional)
7. **Methods without fails check** — pages in `pages/methods/` that have no mention of the `/fails` log (suggest checking if method appears there)

After reporting, ask which issues the user wants to fix now. Fix iteratively.

Append to `log.md`: `## [date] lint | {N} issues found`

### Add workflow (`--wiki-add`)

For manually creating or updating a wiki page:

1. Ask for title (or get from args)
2. Ask for page type (concept / entity / source / synthesis / method)
3. Read `projects/projects.json` → ask for `projects:` tags (MANDATORY)
4. Ask for tags, related pages, sources
5. Ask for body content (collaboratively drafted)
6. Write page to correct subfolder with full frontmatter
7. Update `index.md`
8. Append to `log.md`: `## [date] add | {title}`
9. Git push

### Schema workflow (`--wiki-schema`)

Show current `schema.md`. Then ask:
- "Would you like to update any conventions?"
- Walk through each section collaboratively

After updating, show diff, confirm, write, push.

---

## Initialization (`--wiki-schema` on a new wiki)

If `wiki/` does not exist:

1. Tell the user: "Your wiki doesn't exist yet. Let me set it up."
2. Ask 3-4 questions to generate a starter `schema.md`:
   - "What topics will this wiki cover? (your research domain, personal interests, both?)"
   - "What kinds of sources will you ingest? (papers, articles, books, notes, podcasts?)"
   - "Any conventions you want from the start? (tag vocabulary, emphasis rules?)"
3. Create the full directory structure (index.md, log.md, schema.md, raw/, pages/ with subfolders)
4. Create `.flow` index for the wiki folder:
   ```markdown
   # wiki
   | file / folder | description |
   |---|---|
   | index.md | catalog of all wiki pages |
   | log.md | append-only ingestion and query log |
   | schema.md | wiki conventions and LLM operating guide |
   | raw/ | immutable source documents |
   | pages/ | LLM-maintained wiki pages |
   ```
5. Update `.neuroflow/flowie/.flow` to add a wiki row
6. Git push: `git -C .neuroflow/flowie add -A && git -C .neuroflow/flowie commit -m "wiki: initialize" && git -C .neuroflow/flowie push || true`

---

## Neuroflow-specific integrations

### Project tagging (mandatory)
Every ingest/add/query-that-writes MUST read `projects/projects.json` and ask about project links. Even if the connection is unclear. The user can always say "none." Never skip this.

### ideas.md sync
During ingest or query, if a synthesis page spans multiple projects or generates a cross-project hypothesis, ask based on level:
- `flowie`: "Add to flowie/ideas.md?" → append to `.neuroflow/flowie/ideas.md`
- `project`: "Add to team ideas?" → if hive connected, append to `{hive-repo}/ideas.md`; otherwise append to `.neuroflow/flowie/ideas.md` if flowie active
- `hive`: "Add to hive ideas.md?" → append to `{hive-repo}/ideas.md`

### profile.md evolution
Only applies at `flowie` level. After a lint or synthesis that strongly supports or contradicts a methodological stance from `profile.md`, ask:
> "This seems relevant to your profile stance on X. Update profile.md?"
If yes, follow flowie's write rules: show diff, confirm, write, push.

### Fails integration
When writing or updating `pages/methods/` pages, check `fails/science.md` (from `.neuroflow/fails/science.md`, if present). If the method appears in the fails log, add a callout:
```markdown
> ⚠️ **See fails log:** This method has a recorded failure entry. Review `.neuroflow/fails/science.md` before relying on it.
```

### Paper routing prompt
After `/ideation` or `/search` outputs papers, those commands add a closing reminder to offer wiki ingest. The wiki skill handles it when the user runs `--wiki-ingest` with a paper path or DOI.

### Notes routing prompt
After `/notes` saves a session, it adds a closing reminder offering wiki ingest. The wiki skill handles it when the user runs `--wiki-ingest` with the notes file path.

---

## Git sync

Git operations depend on level:

**flowie level:**
```bash
git -C .neuroflow/flowie pull --rebase origin main || true
git -C .neuroflow/flowie add -A && git -C .neuroflow/flowie commit -m "wiki: {description}" && git -C .neuroflow/flowie push || true
```

**project level:**
```bash
git pull --rebase origin main || true
git add .neuroflow/wiki/ && git commit -m "wiki: {description}" && git push || true
```

**hive level:** use `gh` CLI or GitHub API to push to hive org repo. Pull via `gh api` or `git clone --depth 1` before reads.

Pull before every read. Push after every write. Fail silently on network errors.

---

## Privacy rules

- **flowie wiki**: private GitHub repo — never included in external outputs or exports
- **project wiki**: git-tracked in project repo — shared with all collaborators; treat as project-confidential (not public)
- **hive wiki**: stored in private org GitHub repo — team-wide access only

---

## Session log

Append to `.neuroflow/sessions/YYYY-MM-DD.md` after every wiki operation:
```
[HH:MM] /wiki --{mode} [level:{level}]: {brief summary}
```
Examples:
- `[14:30] /wiki --ingest [level:project]: ingested "Gamma in WM" paper, updated 8 pages`
- `[15:00] /flowie --wiki-query [level:flowie]: answered "what do I know about ICA?", filed as synthesis page`
- `[15:45] /hive --wiki-lint [level:hive]: found 3 orphan pages, 1 missing concept page, fixed 2`
