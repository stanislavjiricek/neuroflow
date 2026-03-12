---
name: slideshow
description: Build a presentation from selected areas of the project — pick phases, figures, and key findings, then get a structured slide deck ready to export.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/fails/core.md
  - .neuroflow/fails/science.md
  - .neuroflow/fails/ux.md
  - .neuroflow/{phase}/flow.md
writes:
  - .neuroflow/sessions/YYYY-MM-DD.md
  - .neuroflow/slideshow/
  - .neuroflow/slideshow/flow.md
---

# /slideshow

Read the `neuroflow:phase-slideshow` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` and `flow.md` before starting.

## What this command does

Generates a structured slide deck outline from `.neuroflow/` contents. Useful for conference presentations, lab meeting talks, thesis defenses, or progress updates. The user chooses which phases, analyses, figures, and documents to include; Claude assembles a coherent, ordered slide deck and saves it in Markdown (reveal.js compatible) or a structured text outline suitable for import into PowerPoint or Keynote.

---

## Step 0 — Check for .neuroflow/

If `.neuroflow/` does not exist, stop and tell the user to run `/neuroflow` first.

---

## Step 1 — Read project state

Read `.neuroflow/project_config.md` and `.neuroflow/flow.md`.

If `.neuroflow/slideshow/` does not exist yet, create it now:
- Create `slideshow/flow.md` with the standard index table (empty, today's date)
- Update the root `.neuroflow/flow.md` to add a row for `slideshow/`

If `slideshow/` exists, read `slideshow/flow.md` to show the user a list of existing slideshows.

---

## Step 2 — Gather presentation intent

Ask the user the following questions (ask all at once, not one at a time):

1. **What is this presentation for?** (conference talk, lab meeting, thesis defense, funder update, internal review, other)
2. **Who is the audience?** (specialists in the field, general neuroscience, mixed, non-scientists)
3. **How long is the talk?** (e.g. 10 min, 20 min, 45 min — this determines the number of slides)
4. **Which phases or topics to include?** List the available phases discovered from `flow.md` and let the user select. They may say "all", pick a subset, or describe topics.
5. **Output format?** Markdown/reveal.js (default) or structured text outline for PowerPoint/Keynote.

Use sensible defaults where the user provides partial answers. A 10-minute talk → ~10–12 slides; 20 minutes → ~20 slides; 45 minutes → ~35–40 slides.

---

## Step 3 — Load phase content

For each selected phase, read its `flow.md` to discover what's available. Load key documents selectively — do not read entire folders. Focus on:

- Analysis summaries and key findings
- Figures referenced in flow files (note paths; do not embed binary files)
- Key decisions logged in reasoning files
- Preregistration deviations (if any)
- Fails flagged in `.neuroflow/fails/` that are relevant to the scope

Navigate using `flow.md` as the index. Only load a full file when it contains content directly relevant to a slide.

---

## Step 4 — Produce the slide deck outline

Build the slide deck in the chosen format. Every deck must include the following structure regardless of length:

### Required slides

1. **Title slide**
   - Project name (from `project_config.md`)
   - Presenter name (ask if not in project_config)
   - Affiliation / institution (ask if not known)
   - Date (today)
   - Any relevant conference / venue name

2. **Overview / agenda slide**
   - List the major sections of the talk
   - One line per section

3. **One section per selected phase or topic**
   Each section opens with a section title slide, then contains content slides:
   - Background / motivation (if ideation phase included)
   - Methods (experiment, data-preprocess, data-analyze phases)
   - Results (data-analyze, brain-run phases) — key findings with bullet points; note figure paths
   - Limitations (drawn from fails and preregistration deviations if any)
   - Model / simulation (brain-build, brain-optimize, brain-run phases if included)

4. **Summary / conclusions slide**
   - 3–5 bullet points summarising the main take-home messages

5. **Future directions slide** (include if talk is > 10 min)
   - What comes next in the project; drawn from open questions in flow files

6. **Acknowledgements slide**
   - Funding (from project_config if available)
   - Collaborators / supervisors (ask if not in project_config)

7. **References slide** (include if any references were cited)
   - List referenced papers cited in analysis or preregistration files

---

## Step 5 — Format output

### Markdown / reveal.js format

Use `---` as the horizontal slide separator and `--` as the vertical slide separator (for sub-slides within a section).

```markdown
---
title: "Project Title"
author: "Author Name"
date: "YYYY-MM-DD"
theme: white
---

# Project Title

Author Name · Affiliation · YYYY-MM-DD

---

## Agenda

- Background
- Methods
- Results
- Summary

---

<!-- Section: Methods -->

## Methods

---

### Participants

- N = 24 participants
- ...

--

### EEG Acquisition

- 64-channel BrainProducts LiveAmp
- ...
```

### Structured text outline (PowerPoint / Keynote)

Use indented plain text with `[SLIDE]`, `[TITLE]`, `[BULLET]`, and `[SPEAKER NOTE]` markers:

```
[SLIDE] Title
[TITLE] Project Title
[BULLET] Author Name — Affiliation
[BULLET] Date: YYYY-MM-DD
[SPEAKER NOTE] Introduce yourself briefly before starting.

[SLIDE] Agenda
[TITLE] Overview
[BULLET] Background
[BULLET] Methods
[BULLET] Results
[BULLET] Summary
```

---

## Step 6 — Save the slideshow

Save the output as `slideshow-YYYY-MM-DD.md` in `.neuroflow/slideshow/`.

If a slideshow with the same date already exists, append `-v2`, `-v3`, etc.

---

## Step 7 — Update flow and log session

Update `.neuroflow/slideshow/flow.md`:

Add a row:
```
| slideshow-YYYY-MM-DD.md | <format> | <phases covered> | <audience> | <talk length> |
```

Append to `.neuroflow/sessions/YYYY-MM-DD.md`:

```
[HH:MM] /slideshow — Built <format> slide deck covering <phases>. Saved to .neuroflow/slideshow/slideshow-YYYY-MM-DD.md.
```

---

## At end

- Created `.neuroflow/slideshow/slideshow-YYYY-MM-DD.md`
- Updated `.neuroflow/slideshow/flow.md`
- Appended to `.neuroflow/sessions/YYYY-MM-DD.md`
- Told the user where the file is and how to open it in reveal.js (if Markdown format) or import it (if PowerPoint outline)
