---
name: notebooklm
description: Complete API for Google NotebookLM — full programmatic access including features not in the web UI. Create notebooks, add sources (URLs, YouTube, PDFs, audio, video, images), generate all artifact types (podcast, video, slide deck, infographic, report, quiz, flashcards, mind map), and download results in multiple formats. Activates on explicit /notebooklm or intent like "create a podcast about X", "turn this into an audio overview", "generate a quiz from my research", "make an infographic", or "create a slide deck".
---

# NotebookLM

Complete programmatic access to Google NotebookLM — including capabilities not exposed in the web UI. Create notebooks, add sources (URLs, YouTube, PDFs, audio, video, images), chat with content, generate all artifact types, and download results in multiple formats.

---

## Installation

**Python package (required):**

```bash
pip install notebooklm-py
```

**Skill install:**

```bash
notebooklm skill install
# or
npx skills add teng-lin/notebooklm-py
```

**Authenticate before first use:**

```bash
notebooklm login        # Opens browser for Google OAuth
notebooklm list         # Verify authentication works
```

---

## Agent setup verification

Before starting any workflow, verify the CLI is ready:

1. `notebooklm status` → should show "Authenticated as: email@..."
2. `notebooklm list --json` → should return valid JSON (even if empty)
3. If either fails → run `notebooklm login`

---

## When this skill activates

**Explicit invocation:** user says "/notebooklm", "use NotebookLM", or mentions the tool by name.

**Intent detection — activate for requests like:**
- "Create a podcast about [topic]"
- "Summarize these URLs/documents"
- "Generate a quiz from my research"
- "Turn this into an audio overview"
- "Create flashcards for studying"
- "Generate a video explainer"
- "Make an infographic"
- "Create a mind map of the concepts"
- "Download the quiz as markdown"
- "Add these sources to NotebookLM"

---

## Autonomy rules

**Run automatically (no confirmation needed):**
- `notebooklm status` — check context
- `notebooklm auth check` — diagnose auth issues
- `notebooklm list` — list notebooks
- `notebooklm source list` — list sources
- `notebooklm artifact list` — list artifacts
- `notebooklm language list` / `get` / `set` — language settings
- `notebooklm artifact wait` (in subagent context)
- `notebooklm source wait` (in subagent context)
- `notebooklm research wait` (in subagent context)
- `notebooklm use <id>` — set context (⚠️ SINGLE-AGENT ONLY — use `-n` flag in parallel workflows)
- `notebooklm create` — create notebook
- `notebooklm ask "..."` — chat queries (without `--save-as-note`)
- `notebooklm history` — display conversation history (read-only)
- `notebooklm source add` — add sources

**Ask before running:**
- `notebooklm delete` — destructive
- `notebooklm generate *` — long-running, may fail
- `notebooklm download *` — writes to filesystem
- `notebooklm artifact wait` / `notebooklm source wait` / `notebooklm research wait` — long-running (when in main conversation)
- `notebooklm ask "..." --save-as-note` — writes a note
- `notebooklm history --save` — writes a note

---

## Quick reference

| Task | Command |
|------|---------|
| Authenticate | `notebooklm login` |
| Diagnose auth issues | `notebooklm auth check` |
| List notebooks | `notebooklm list` |
| Create notebook | `notebooklm create "Title"` |
| Set context | `notebooklm use <notebook_id>` |
| Show context | `notebooklm status` |
| Add URL source | `notebooklm source add "https://..."` |
| Add file | `notebooklm source add ./file.pdf` |
| Add YouTube | `notebooklm source add "https://youtube.com/..."` |
| List sources | `notebooklm source list` |
| Wait for source processing | `notebooklm source wait <source_id>` |
| Web research (fast) | `notebooklm source add-research "query"` |
| Web research (deep) | `notebooklm source add-research "query" --mode deep --no-wait` |
| Chat | `notebooklm ask "question"` |
| Chat (save answer as note) | `notebooklm ask "question" --save-as-note` |
| Show conversation history | `notebooklm history` |
| Generate podcast | `notebooklm generate audio "instructions"` |
| Generate video | `notebooklm generate video "instructions"` |
| Generate slide deck | `notebooklm generate slide-deck` |
| Generate infographic | `notebooklm generate infographic` |
| Generate report | `notebooklm generate report --format briefing-doc` |
| Generate quiz | `notebooklm generate quiz` |
| Generate flashcards | `notebooklm generate flashcards` |
| Generate mind map | `notebooklm generate mind-map` |
| Check artifact status | `notebooklm artifact list` |
| Wait for completion | `notebooklm artifact wait <artifact_id>` |
| Download audio | `notebooklm download audio ./output.mp3` |
| Download video | `notebooklm download video ./output.mp4` |
| Download slide deck (PDF) | `notebooklm download slide-deck ./slides.pdf` |
| Download slide deck (PPTX) | `notebooklm download slide-deck ./slides.pptx --format pptx` |
| Download report | `notebooklm download report ./report.md` |
| Download quiz (markdown) | `notebooklm download quiz --format markdown quiz.md` |
| Download flashcards (markdown) | `notebooklm download flashcards --format markdown cards.md` |
| List languages | `notebooklm language list` |
| Set language | `notebooklm language set zh_Hans` |
| Delete notebook | `notebooklm notebook delete <id>` |

---

## Generation types

All generate commands support `-s, --source` (specific sources), `--language` (output language), `--json` (machine-readable output), and `--retry N` (auto-retry on rate limits).

| Type | Command | Options | Download format |
|------|---------|---------|-----------------|
| Podcast | `generate audio` | `--format [deep-dive\|brief\|critique\|debate]`, `--length [short\|default\|long]` | .mp3 |
| Video | `generate video` | `--format [explainer\|brief]`, `--style [auto\|classic\|whiteboard\|kawaii\|anime\|watercolor\|retro-print\|heritage\|paper-craft]` | .mp4 |
| Slide Deck | `generate slide-deck` | `--format [detailed\|presenter]`, `--length [default\|short]` | .pdf / .pptx |
| Infographic | `generate infographic` | `--orientation [landscape\|portrait\|square]`, `--detail [concise\|standard\|detailed]`, `--style [auto\|sketch-note\|professional\|bento-grid\|editorial\|instructional\|bricks\|clay\|anime\|kawaii\|scientific]` | .png |
| Report | `generate report` | `--format [briefing-doc\|study-guide\|blog-post\|custom]`, `--append "extra instructions"` | .md |
| Mind Map | `generate mind-map` | *(sync, instant)* | .json |
| Data Table | `generate data-table` | description required | .csv |
| Quiz | `generate quiz` | `--difficulty [easy\|medium\|hard]`, `--quantity [fewer\|standard\|more]` | .json/.md |
| Flashcards | `generate flashcards` | `--difficulty [easy\|medium\|hard]`, `--quantity [fewer\|standard\|more]` | .json/.md |

---

## Features beyond the web UI

| Feature | Command | Description |
|---------|---------|-------------|
| Batch downloads | `download <type> --all` | Download all artifacts of a type at once |
| Quiz/Flashcard export | `download quiz --format json` | Export as JSON, Markdown, or HTML |
| Mind map extraction | `download mind-map` | Export hierarchical JSON for visualization tools |
| Data table export | `download data-table` | Download structured tables as CSV |
| Slide deck as PPTX | `download slide-deck --format pptx` | Editable .pptx (web UI only offers PDF) |
| Slide revision | `generate revise-slide "prompt" --artifact <id> --slide N` | Modify individual slides |
| Report template append | `generate report --format study-guide --append "..."` | Append custom instructions |
| Source fulltext | `source fulltext <id>` | Retrieve indexed text content of any source |
| Save chat to note | `ask "..." --save-as-note` | Save Q&A answers as notebook notes |

---

## Common workflows

### Research to podcast

1. `notebooklm create "Research: [topic]"`
2. `notebooklm source add` for each URL/document
3. Wait for sources: `notebooklm source list --json` until all status=READY
4. `notebooklm generate audio "Focus on [specific angle]"` (confirm when asked)
5. Note the artifact ID returned
6. Check `notebooklm artifact list` for status
7. `notebooklm download audio ./podcast.mp3` when complete

**For automated/background generation**, spawn a subagent after step 4:
```
Task(
  prompt="Wait for artifact {artifact_id} in notebook {notebook_id} to complete, then download.
          Use: notebooklm artifact wait {artifact_id} -n {notebook_id} --timeout 600
          Then: notebooklm download audio ./podcast.mp3 -a {artifact_id} -n {notebook_id}",
  subagent_type="general-purpose"
)
```

### Document analysis

1. `notebooklm create "Analysis: [project]"`
2. `notebooklm source add ./doc.pdf` (or URLs)
3. `notebooklm ask "Summarize the key points"`
4. Continue chatting as needed

---

## Processing times

| Operation | Typical time | Suggested timeout |
|-----------|--------------|-------------------|
| Source processing | 30s–10 min | 600s |
| Research (fast) | 30s–2 min | 180s |
| Research (deep) | 15–30+ min | 1800s |
| Quiz, flashcards | 5–15 min | 900s |
| Report, data-table | 5–15 min | 900s |
| Audio generation | 10–20 min | 1200s |
| Video generation | 15–45 min | 2700s |

---

## Error handling

| Error | Cause | Action |
|-------|-------|--------|
| Auth/cookie error | Session expired | Run `notebooklm auth check` then `notebooklm login` |
| "No notebook context" | Context not set | Use `-n <id>` flag (parallel) or `notebooklm use <id>` (single-agent) |
| "No result found for RPC ID" | Rate limiting | Wait 5–10 min, retry |
| `GENERATION_FAILED` | Google rate limit | Wait and retry later |
| Download fails | Generation incomplete | Check `artifact list` for status |

**Unreliable operations** (may fail with rate limiting): audio, video, quiz, flashcards, infographic, slide deck generation. Workaround: retry after 5–10 minutes or use the NotebookLM web UI as fallback.

---

## Parallel safety

Use explicit notebook IDs in parallel workflows. Commands supporting `-n` shorthand: `artifact wait`, `source wait`, `research wait/status`, `download *`. For automation, prefer full UUIDs to avoid ambiguity.

**CI/CD setup:** Set `NOTEBOOKLM_AUTH_JSON` from a secret containing your `storage_state.json` contents.

**Multiple accounts:** Use different `NOTEBOOKLM_HOME` directories per account.

---

## Language configuration

Language setting controls output language for generated artifacts (audio, video, etc.). This is a GLOBAL setting affecting all notebooks.

```bash
notebooklm language list          # List 80+ supported languages
notebooklm language set zh_Hans   # Simplified Chinese
notebooklm language set en        # English (default)
```

Override per command: `notebooklm generate audio --language ja`
