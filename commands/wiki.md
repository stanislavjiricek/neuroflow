---
name: wiki
description: Project-level shared knowledge base — Karpathy-style LLM-maintained wiki at .neuroflow/wiki/, git-tracked and shared with all project collaborators. The shared brain for experimental rationale, analysis decisions, project literature, and methods. Use /flowie --wiki-* for personal wiki, /hive --wiki-* for team wiki.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/wiki/**
  - ~/.neuroflow/user.yaml                # wiki_auto (--auto)
  - .neuroflow/reasoning/*.jsonl          # --catchup, after the person agrees
  - .neuroflow/sessions/*.md              # --catchup, this machine's milestone lines
  - .neuroflow/{phase}/*.md               # --catchup, phase summaries
  - .neuroflow/preregistration/deviations.md
writes:
  - .neuroflow/wiki/
  - .neuroflow/wiki/.pending/             # review-queue cards — local tier, never committed
  - ~/.neuroflow/user.yaml                # --auto writes the wiki_auto key only, merged
  - .neuroflow/sessions/YYYY-MM-DD.md
lifecycle: full
produces:
  - .neuroflow/wiki/
---

# /wiki

Project-level shared knowledge base. Lives at `.neuroflow/wiki/`, git-tracked in the project repo, visible to all collaborators.

**Three-level wiki overview:**
- `/wiki` — this command — project brain (shared with collaborators)
- `/flowie --wiki-*` — personal wiki (private, in flowie repo)
- `/hive --wiki-*` — team wiki (lab-wide, in hive repo)

Read the `neuroflow:wiki-protocol` skill first with `level: project`. Then follow the neuroflow-core lifecycle — its version notice included (**Command lifecycle**, step 3).

---

## Step 0 — Check for .neuroflow/

If `.neuroflow/` does not exist, stop and tell the user to run `/neuroflow` first.

---

## Step 1 — Parse mode flag

If no flag given: default to `--view` if wiki exists, `--schema` if it does not.

| Flag | Action |
|------|--------|
| `--view` | Show wiki overview: page count, recent activity |
| `--ingest [path]` | Ingest a source into the project wiki |
| `--query [question]` | Ask a question answered from the project wiki |
| `--lint` | Health check: orphans, stale pages, missing tags |
| `--add [title]` | Create or update a wiki page |
| `--add --from-pending <card file>` | Write a page from a review-queue card through the normal `--add` flow |
| `--review` | Walk the pending capture cards one by one: accept writes the page, skip marks the card skipped. With the neuroflow mod active, opens the review pane instead |
| `--catchup` | Queue cards from project memory written since the last wiki log entry (reasoning logs, this machine's session milestones, phase summaries, preregistration deviations) — asks before reading |
| `--auto ask\|off\|status` | Personal capture switch: `wiki_auto` in `~/.neuroflow/user.yaml`; `status` shows the setting, the project policy and the number of pending cards |
| `--schema` | View or update wiki conventions (also initializes wiki) |

Wiki root for all operations: `.neuroflow/wiki/`
Git pattern: standard `git` in project root (not `-C` flowie pattern), branch-safe — fast-forward-only pull of the current branch, commits limited to `.neuroflow/wiki/`, and a push only after the person confirms (the wiki-protocol skill's **Git sync**).

---

## Step 2 — Execute mode

Follow the `neuroflow:wiki-protocol` skill at `level: project`.

**Project-specific context for `projects:` tagging:**
The current project IS the context — read `project_config.md` for project name, phase, and modality. Ask if the page also relates to other projects the user is aware of.

**Review queue** — switches, card format and rubric: the `neuroflow:wiki-protocol` skill → **Auto capture (review queue)**.

- `--review` — take the cards in `.neuroflow/wiki/.pending/` with `status: pending`, newest first, and walk them one at a time in text: show the title, type, evidence and text, then ask accept, skip or stop. Accept → `--add --from-pending` below; skip → set the card's `status: skipped`; stop → leave the rest pending. No pending card: say so. With the neuroflow mod active, `--review` opens the review pane instead.
- `--add --from-pending <card file>` — the card (its file name or path in `.neuroflow/wiki/.pending/`) is the source text of the normal `--add` flow; after the page is written, set the card's `status: accepted`. A card that is no longer `pending` is not written again — say so.
- `--catchup` — with `wiki_capture: forbid` in the `project_config.md` frontmatter, say so and stop. Otherwise ask before reading anything, then run the rubric over `reasoning/*.jsonl`, this machine's `sessions/` milestone lines, the phase summaries and `preregistration/deviations.md`, taking only what is dated after the last `log.md` entry (everything when the log is empty). The two-card cap counts per command found there. Write the cards to the queue, say how many, and suggest `--review`.
- `--auto ask|off|status` — `ask` or `off` writes `wiki_auto` to `~/.neuroflow/user.yaml`, merging into the file (create it if missing), never replacing it; with `ask` in a project with `wiki_capture: forbid`, add that capture stays off here. `status` prints the setting (absent = `off`), the project's `wiki_capture` policy (absent = `allow`) and the number of pending cards.

---

## Step 3 — Session log

Append to `.neuroflow/sessions/YYYY-MM-DD.md`:

```
## HH:MM — [wiki] --{mode} [level:project]: {brief summary}
```
