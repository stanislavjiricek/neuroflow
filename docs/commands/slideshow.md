---
title: /slideshow
---

# `/neuroflow:slideshow`

**Build a presentation from selected areas of the project.**

`/slideshow` assembles a structured slide deck outline from your `.neuroflow/` project memory. Pick which phases, analyses, figures, and findings to include; specify your audience and talk length; get a ready-to-export slide deck in Markdown/reveal.js or a structured text outline for PowerPoint or Keynote.

---

## When to use it

- Before a conference talk or poster session
- For a lab meeting or group presentation
- For a thesis defense or progress review
- For a funder update or internal stakeholder presentation

---

## What it does

Claude asks:

1. **What is this presentation for?** (conference, lab meeting, defense, funder update, other)
2. **Who is the audience?** (specialists, general neuroscience, mixed, non-scientists)
3. **How long is the talk?** (determines slide count)
4. **Which phases or topics to include?** (picks from what exists in `.neuroflow/`)
5. **Output format?** (Markdown/reveal.js or structured text for PowerPoint/Keynote)

Then Claude loads the relevant phase content, synthesises key findings and figures, and produces a complete slide deck outline.

---

## Slide structure

Every deck follows a fixed spine regardless of length:

| Slide | Content |
|---|---|
| Title | Project name, presenter, affiliation, date, venue |
| Agenda | Section list — one line per topic |
| Per-phase sections | Section title slide + content slides (background, methods, results, limitations) |
| Summary | 3–5 take-home bullet points |
| Future directions | Next steps (talks > 10 min) |
| Acknowledgements | Funding and collaborators |
| References | Papers cited in analyses or preregistration |

---

## Slide count heuristic

| Talk length | Target slides |
|---|---|
| 5–10 min | 8–12 |
| 15–20 min | 15–22 |
| 30 min | 25–30 |
| 45 min | 32–40 |

---

## Output formats

### Markdown / reveal.js

```markdown
---
title: "OddballStudy2026"
author: "J. Smith"
date: "2026-03-09"
theme: white
---

# OddballStudy2026

J. Smith · Institute of Neuroscience · 2026-03-09

---

## Agenda

- Background
- Methods
- Results
- Summary

---

## Methods

---

### Participants

- N = 24 adults (12 F), mean age 26.3 ± 4.1 years
- Exclusions: 1 (excessive artefacts)

--

### EEG Acquisition

- 64-channel BrainProducts LiveAmp
- 1000 Hz sampling rate
- Online reference: FCz
```

Open with [reveal.js](https://revealjs.com/) or [Slidev](https://sli.dev/).

---

### Structured text outline (PowerPoint / Keynote)

```
[SLIDE] Title
[TITLE] OddballStudy2026
[BULLET] J. Smith — Institute of Neuroscience
[BULLET] Date: 2026-03-09
[SPEAKER NOTE] Greet the audience and introduce the study briefly.

[SLIDE] Agenda
[TITLE] Overview
[BULLET] Background
[BULLET] Methods
[BULLET] Results
[BULLET] Summary

[SLIDE] Results — P300 Effect
[TITLE] Noise reduces P300 amplitude
[BULLET] Cluster at 350–520ms (p = 0.012)
[BULLET] Amplitude reduction: 2.3 µV (Cohen's d = 0.71)
[IMAGE: figures/erp_comparison.png]
[SPEAKER NOTE] Point to the shaded cluster region on the figure.
```

Copy each `[SLIDE]` block into a new slide in PowerPoint or Keynote.

---

## Output

The slide deck is saved as `slideshow-YYYY-MM-DD.md` in `.neuroflow/slideshow/`. If a file with the same date already exists, a version suffix is added (`-v2`, `-v3`, etc.).

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md`, `.neuroflow/{phase}/flow.md` (for each selected phase), `.neuroflow/fails/` |
| Writes | `.neuroflow/slideshow/slideshow-YYYY-MM-DD.md`, `.neuroflow/slideshow/flow.md`, `.neuroflow/sessions/YYYY-MM-DD.md` |

---

## Related commands

- [`/write-report`](write-report.md) — generate a prose report rather than a slide deck
- [`/notes`](notes.md) — capture rough notes that can seed a future slideshow
- [`/output`](output.md) — package the slideshow file along with figures for sharing
- [`/sentinel`](sentinel.md) — audit project consistency before presenting
