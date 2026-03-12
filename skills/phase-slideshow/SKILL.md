---
name: phase-slideshow
description: Phase guidance for the neuroflow /slideshow command. Loaded automatically when /slideshow is invoked to orient agent behavior, slide structure decisions, format selection, and audience calibration for presentation generation.
---

# phase-slideshow

The slideshow phase generates a structured slide deck outline from `.neuroflow/` contents — covering selected phases, analyses, figures, and key findings — ready to export as Markdown/reveal.js or a PowerPoint-compatible structured outline.

## Approach

- Confirm scope (which phases), audience, talk length, and output format before loading any files
- Use `flow.md` files to navigate `.neuroflow/` rather than reading all content up front
- Calibrate slide count and detail level to the stated talk length — do not pad or over-explain
- Synthesize, do not transcribe — a slide is a claim supported by evidence, not a file dump
- Flag figures by path but do not attempt to embed binary image files

## Relevant skills

- `neuroflow:neuroflow-core` — read first; defines the command lifecycle and `.neuroflow/` write rules

## Audience calibration

| Audience | Approach |
|---|---|
| Specialist (same field) | Include technical detail in methods; abbreviations are fine |
| General neuroscience | Explain modality-specific methods briefly; avoid jargon in results |
| Mixed | Lead with big-picture framing; keep methods to one slide; emphasise findings |
| Non-scientists | One-sentence lay summary per section; no statistical notation without explanation |

## Slide count heuristic

| Talk length | Target slides |
|---|---|
| 5–10 min | 8–12 |
| 15–20 min | 15–22 |
| 30 min | 25–30 |
| 45 min | 32–40 |

If the user asks for more slides than the heuristic suggests, comply but note that the pace may be tight.

## Output format guidance

### Markdown / reveal.js

- Use YAML frontmatter with `title`, `author`, `date`, `theme`
- `---` separates horizontal slides; `--` separates vertical sub-slides within a section
- Recommended themes: `white` (light), `black` (dark), `moon` (dark, muted)
- Remind the user to install [reveal.js](https://revealjs.com/) or use [Slidev](https://sli.dev/) for rendering

### Structured text outline (PowerPoint / Keynote)

- Each slide block starts with `[SLIDE]`
- Use `[TITLE]`, `[BULLET]`, `[IMAGE: path/to/figure]`, `[SPEAKER NOTE]` markers
- This format can be copied into a presentation app slide by slide
- Remind the user to replace `[IMAGE: ...]` markers with actual figure files

## Workflow hints

- Save the slideshow to `.neuroflow/slideshow/slideshow-YYYY-MM-DD.md` — confirm before writing
- If a same-date file exists, append `-v2`, `-v3`, etc.
- Keep bullet points to ≤ 6 words per line where possible — slides are prompts, not paragraphs

## Slash command

`/neuroflow:slideshow` — runs this workflow as a slash command.
