---
name: poster
description: Generate a LaTeX academic conference poster from project memory. Selects a template (A0/A1/A2, portrait/landscape, custom sizes), injects project content, adds a QR code, and runs the result through the poster-critic agent in an iterative review loop.
phase: poster
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - .neuroflow/ideation/flow.md
  - .neuroflow/data-analyze/flow.md
  - .neuroflow/paper/flow.md
  - .neuroflow/preregistration/flow.md
writes:
  - .neuroflow/poster/poster-YYYY-MM-DD.tex
  - .neuroflow/poster/critic-log.md
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /poster

Generate a publication-ready academic conference poster as a LaTeX `.tex` file from the project's `.neuroflow/` memory. The poster goes through an iterative critic loop (up to 3 revision cycles) before final output.

Apply `neuroflow:stop-slop` to all text blocks (Introduction, Methods, Results, Discussion, Conclusions) before passing the poster to the critic — eliminate AI writing patterns, filler phrases, passive voice, and formulaic structures.

---

## Step 1 — Read project state

1. Read `.neuroflow/project_config.md` to get: project title, PI name, affiliation(s), modality, research question, and any configured target conference.
2. Check `.neuroflow/poster/` — if a previous poster exists, ask whether to start fresh or revise the latest version.
3. Scan for available content sources (read their `flow.md` index files, not the full content):
   - `.neuroflow/ideation/` — hypotheses, key references
   - `.neuroflow/data-analyze/` — key results, figure paths
   - `.neuroflow/preregistration/` — objectives and analysis plan
   - `.neuroflow/paper/` — abstract and conclusions if a draft exists
4. List any figure files referenced in the flow.md files.

---

## Step 2 — Confirm poster configuration

Ask the user (if not already specified as arguments):

1. **Conference name** — e.g. "SfN 2025", "OHBM 2025", "Bernstein Conference"
2. **Poster size** — offer the template catalogue:
   - `A` — A0 Portrait (841 × 1189 mm) — most European conferences
   - `B` — A0 Landscape (1189 × 841 mm) — wide-format boards
   - `C` — A1 Portrait (594 × 841 mm) — seminars, lab retreats
   - `D` — Custom 90 × 120 cm Portrait
   - `E` — 48 × 36 in Landscape (US conferences)
   - `custom` — user specifies dimensions
3. **QR code URL** — preprint DOI, OSF page, GitHub repo, or "skip" to omit
4. **Authors and affiliations** — confirm or update from `project_config.md`
5. **Which sections to include** — all five standard sections (Introduction, Methods, Results, Discussion/Conclusions, References) or a subset

If the user gives a conference name, infer the likely size (e.g., SfN → A0 portrait or 48×36 in; OHBM → A0 portrait; NeurIPS → custom; COSYNE → 48×36 in) and confirm.

---

## Step 3 — Extract content from project memory

Read the relevant `.neuroflow/` files identified in Step 1. Extract:

- **Title** — from `project_config.md`; rephrase into a poster-appropriate punchy title if needed
- **Introduction** — from ideation phase: background, gap, motivation (3–4 sentences maximum per paragraph; compress ruthlessly)
- **Objectives** — from ideation or preregistration: 2–4 bullet points
- **Methods** — from experiment, data, or analysis phase: participants (N, demographics), design, recording, key analysis steps
- **Results** — from data-analyze phase: top 2–3 findings with effect sizes; list figure paths as `\includegraphics` stubs
- **Conclusions** — from paper or ideation phase: 3 bullet points maximum
- **References** — top 3–5 references most relevant to the poster (extract from ideation flow.md or paper references)
- **Acknowledgements / funding** — from project_config.md or grant-proposal phase if available

If a section has no data in `.neuroflow/`, insert a clearly marked placeholder (`PLACEHOLDER: ...`) and note it to the user.

---

## Step 4 — Generate LaTeX source

Using the `neuroflow:phase-poster` skill:

1. Select the template matching the user's choice from the template catalogue
2. Substitute all placeholder values with extracted content
3. Set the QR code URL (or remove the QR block if the user said "skip")
4. For each result figure, generate a `\includegraphics` stub with the extracted path and a placeholder caption
5. Produce the complete `.tex` file content

Show the user a preview summary:
```
Title: <extracted title>
Authors: <authors>
Sections: Introduction / Methods / Results (N figures) / Discussion / Conclusions / References
QR code: <URL or "none">
Template: <letter> — <size description>
```

Ask: "Generate this poster? (Y/n)"

---

## Step 5 — Iterative critic review loop

Once the user confirms, activate the worker-critic loop following `neuroflow:worker-critic`:

**Worker:** the poster generator (this command, operating on the `.tex` source)
**Critic:** the `poster-critic` agent
**Max iterations:** 3

**Iteration 1:** Pass the generated `.tex` source to `poster-critic` with the rubric:
- Content accuracy vs project memory
- Section balance and column proportions
- Poster legibility (font sizes, colour contrast, title prominence)
- QR code presence and placement (if requested)
- Figure stubs clearly labelled
- References present
- No blank or placeholder sections visible in the poster except explicitly noted ones

**On REJECTED:** Apply the critic's specific feedback bullets to the `.tex` source and resubmit.

**On APPROVED** (or after 3 iterations): proceed to Step 6.

Write the critic loop state to `.neuroflow/poster/critic-log.md` after each iteration.

---

## Step 6 — Save and report

1. Create `.neuroflow/poster/` if it does not exist.
2. Write the final `.tex` to `.neuroflow/poster/poster-YYYY-MM-DD.tex`. If the file exists, use `-v2`, `-v3`, etc.
3. Write `.neuroflow/poster/critic-log.md` with the full loop history.
4. Update `.neuroflow/flow.md` — add a `poster` entry with date and output path.

Tell the user:

> **Poster saved:** `.neuroflow/poster/poster-YYYY-MM-DD.tex`
>
> **To compile:**
> ```bash
> cd .neuroflow/poster
> pdflatex poster-YYYY-MM-DD.tex
> ```
> Or with latexmk: `latexmk -pdf poster-YYYY-MM-DD.tex`
>
> **Required LaTeX packages:** `tikzposter`, `qrcode`, `graphicx`, `booktabs`, `amsmath` (all in TeX Live ≥ 2020 / MiKTeX).
>
> **Figure stubs:** Replace each `\includegraphics{figures/...}` stub with the actual file. Use `.pdf` or `.eps` for vector figures.

If the critic loop halted at max iterations without approval, also say:

> **Note:** The critic loop reached the maximum 3 iterations without full approval. Unresolved issues are logged in `.neuroflow/poster/critic-log.md`. The current `.tex` is a working draft — review the critic log and make manual edits before printing.

---

## Step 7 — Suggest next step

- If the conference deadline is within 2 weeks (if known from `project_config.md`): remind the user to print at least 2 business days before the conference.
- Suggest `/neuroflow:slideshow` if the user also needs a talk for the same conference.
- Suggest `/neuroflow:paper` if the poster results are ready to be written up as a manuscript.
