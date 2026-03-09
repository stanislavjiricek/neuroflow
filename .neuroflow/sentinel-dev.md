# sentinel-dev

Last run: 2026-03-09

## Issues found

### Check 1 — Folder name vs frontmatter name

**ISSUE 1.1** — `skills/skill-creator/SKILL.md`
- Folder name: `skill-creator`
- Frontmatter `name:` field: `Skill Development`
- These must match exactly. Fix: change the `name:` field in `skills/skill-creator/SKILL.md` from `Skill Development` to `skill-creator`.

---

### Check 4 — Dead references inside command files

**ISSUE 4.1** — `commands/experiment.md`
- References `neuroflow:psychopy-paradigm` skill — no folder `skills/psychopy-paradigm/` exists.
- References `neuroflow:lsl-integration` skill — no folder `skills/lsl-integration/` exists.
- References `neuroflow:marker-writing` skill — no folder `skills/marker-writing/` exists.
- Fix: either create these skills, or update the command body to remove or qualify the references (e.g. note them as planned/future skills).

**ISSUE 4.2** — `commands/tool-build.md`
- References `neuroflow:lsl-integration` skill — no folder `skills/lsl-integration/` exists.
- References `neuroflow:marker-writing` skill — no folder `skills/marker-writing/` exists.
- References `neuroflow:psychopy-paradigm` skill — no folder `skills/psychopy-paradigm/` exists.
- Fix: same as 4.1 above.

**ISSUE 4.3** — `commands/tool-validate.md`
- References `neuroflow:paradigm-auditor` agent — no file `agents/paradigm-auditor.md` exists.
- Fix: create the `paradigm-auditor` agent, or remove/qualify the reference.

**ISSUE 4.4** — `commands/data-preprocess.md`
- References `neuroflow:eeg-preprocessing` skill — no folder `skills/eeg-preprocessing/` exists.
- References `neuroflow:fmri-analysis` skill — no folder `skills/fmri-analysis/` exists.
- Fix: create these skills, or update the command body.

**ISSUE 4.5** — `commands/data-analyze.md`
- References `neuroflow:eeg-preprocessing` skill — no folder `skills/eeg-preprocessing/` exists.
- References `neuroflow:feature-extraction` skill — no folder `skills/feature-extraction/` exists.
- References `neuroflow:classification-clustering` skill — no folder `skills/classification-clustering/` exists.
- References `neuroflow:permutation-testing` skill — no folder `skills/permutation-testing/` exists.
- References `neuroflow:fmri-analysis` skill — no folder `skills/fmri-analysis/` exists.
- References `neuroflow:multimodal-analysis` skill — no folder `skills/multimodal-analysis/` exists.
- References `neuroflow:stats-auditor` agent — no file `agents/stats-auditor.md` exists.
- Fix: create the missing skills and agent, or update the command body to mark these as planned.

**ISSUE 4.6** — `commands/paper-write.md`
- References `neuroflow:latex-paper` skill — no folder `skills/latex-paper/` exists.
- References `neuroflow:journal-styles` skill — no folder `skills/journal-styles/` exists.
- Fix: create these skills, or update the command body.

**ISSUE 4.7** — `commands/paper-review.md`
- References `neuroflow:paper-review` as a skill in the body ("Use the `neuroflow:paper-review` skill") — no folder `skills/paper-review/` exists. The actual skill that provides this functionality is `neuroflow:review-neuro`.
- Fix: change `neuroflow:paper-review` to `neuroflow:review-neuro` in the body of `commands/paper-review.md`. This is a name mismatch between the command and the skill it should invoke.

---

### Check 6 — Naming overlaps

**ISSUE 6.1** — `commands/sentinel.md` and `agents/sentinel.md` share the identical name `sentinel`.
- The command is `/neuroflow:sentinel` and the agent is also named `sentinel`. This is intentional by design (the command calls the agent), but it is worth flagging: if a user or another file references `sentinel` without context, it is ambiguous whether the command or the agent is meant.
- Informational only. No fix required if the design is intentional, but a note in the agent's description clarifying it is invoked by the `/sentinel` command would reduce ambiguity.

---

## Passed checks

### Check 1 — Folder name vs frontmatter name (partial pass)

All skills except `skill-creator` pass:
- `skills/neuroflow-core/SKILL.md`: name `neuroflow-core` matches folder name. PASS
- `skills/neuroflow-develop/SKILL.md`: name `neuroflow-develop` matches folder name. PASS
- `skills/review-neuro/SKILL.md`: name `review-neuro` matches folder name. PASS

All agents pass:
- `agents/scholar.md`: name `scholar` matches filename. PASS
- `agents/sentinel.md`: name `sentinel` matches filename. PASS
- `agents/sentinel-dev.md`: name `sentinel-dev` matches filename. PASS

All commands pass:
- `commands/start.md`: name `start` matches filename. PASS
- `commands/ideation.md`: name `ideation` matches filename. PASS
- `commands/grant-proposal.md`: name `grant-proposal` matches filename. PASS
- `commands/experiment.md`: name `experiment` matches filename. PASS
- `commands/tool-build.md`: name `tool-build` matches filename. PASS
- `commands/tool-validate.md`: name `tool-validate` matches filename. PASS
- `commands/data.md`: name `data` matches filename. PASS
- `commands/data-preprocess.md`: name `data-preprocess` matches filename. PASS
- `commands/data-analyze.md`: name `data-analyze` matches filename. PASS
- `commands/paper-write.md`: name `paper-write` matches filename. PASS
- `commands/paper-review.md`: name `paper-review` matches filename. PASS
- `commands/notes.md`: name `notes` matches filename. PASS
- `commands/write-report.md`: name `write-report` matches filename. PASS
- `commands/phase.md`: name `phase` matches filename. PASS
- `commands/sentinel.md`: name `sentinel` matches filename. PASS

### Check 2 — README tables

All 15 command files in `commands/` have a row in the README Commands tables. PASS
- `/start`, `/ideation`, `/grant-proposal`, `/experiment`, `/tool-build`, `/tool-validate`, `/data`, `/data-preprocess`, `/data-analyze`, `/paper-write`, `/paper-review`, `/notes`, `/write-report`, `/phase`, `/sentinel` — all present and all link to files that exist.

All 4 skill folders in `skills/` have a row in the README Skills table. PASS
- `neuroflow:neuroflow-core`, `neuroflow:review-neuro`, `neuroflow:neuroflow-develop`, `neuroflow:skill-creator` — all present and all link to files that exist.

All 3 agent files in `agents/` have a row in the README Agents table. PASS
- `scholar`, `sentinel`, `sentinel-dev` — all present and all link to files that exist.

No README table row points to a file that does not exist. PASS

### Check 3 — Version sync

- `plugin.json` version: `0.1.1`
- README heading: `## What's new in 0.1.1`
- Versions match. PASS

### Check 5 — Command frontmatter completeness

All 15 command files have all five required frontmatter fields (`name`, `description`, `phase`, `reads`, `writes`). PASS
- `commands/start.md`: all fields present. PASS
- `commands/ideation.md`: all fields present. PASS
- `commands/grant-proposal.md`: all fields present. PASS
- `commands/experiment.md`: all fields present. PASS
- `commands/tool-build.md`: all fields present. PASS
- `commands/tool-validate.md`: all fields present. PASS
- `commands/data.md`: all fields present. PASS
- `commands/data-preprocess.md`: all fields present. PASS
- `commands/data-analyze.md`: all fields present. PASS
- `commands/paper-write.md`: all fields present. PASS
- `commands/paper-review.md`: all fields present. PASS
- `commands/notes.md`: all fields present. PASS
- `commands/write-report.md`: all fields present. PASS
- `commands/phase.md`: all fields present. PASS
- `commands/sentinel.md`: all fields present. PASS

### Check 6 — Naming overlaps (partial pass)

No skill name is identical or nearly identical to any command name:
- Skills: `neuroflow-core`, `neuroflow-develop`, `review-neuro`, `skill-creator`
- Commands: `start`, `ideation`, `grant-proposal`, `experiment`, `tool-build`, `tool-validate`, `data`, `data-preprocess`, `data-analyze`, `paper-write`, `paper-review`, `notes`, `write-report`, `phase`, `sentinel`
- No skill name collides with any command name. PASS
- The `sentinel` command / `sentinel` agent overlap is flagged in Issue 6.1 above (informational).
