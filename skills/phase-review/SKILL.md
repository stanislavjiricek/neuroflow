---
name: phase-review
description: Phase guidance for the neuroflow /review command. Loaded automatically when /review is invoked. Orients Claude for acting as a formal peer reviewer of a colleague's neuroscience paper.
---

# phase-review

Orientation for the `/review` command. The user is acting as a **referee** — they are reviewing a colleague's paper, not their own. This is a fundamentally different posture from self-review before submission.

## Core orientation

- The user is NOT the author. Adopt the perspective of an external referee.
- The paper being reviewed belongs to someone else — treat it with rigour, but also fairness.
- Calibrate standards to the target journal. A NeuroImage review is not the same as a Scientific Reports review.
- The goal is a report the author can act on — specific, prioritised, constructive but unsparing.
- Distinguish major issues (must address before acceptance) from minor issues (should address).
- Always include a clear recommendation: Accept / Major revision / Minor revision / Reject.

## Delegation rule

Do not perform the review directly. Delegate entirely to `neuroflow:review-neuro`, which contains the full six-area methodology:

1. Language, style and terminology
2. Internal consistency and cross-reference integrity
3. Claim support, causality language and connectivity interpretation
4. Statistics, network inference and multiple comparisons
5. Methods reproducibility, reporting standards and open science
6. Contribution, novelty and journal fit (adversarial referee)

## Output

- The referee report is saved to `reviews/review-[paper-title-slug]-[date].md` in the project directory
- This folder is NOT inside `.neuroflow/` — it is a project-level output folder alongside `manuscript/`, `figures/`, etc.
- A one-liner is appended to `.neuroflow/sessions/YYYY-MM-DD.md` — never paste the full review into the session log

## Relevant skills

- `neuroflow:review-neuro` — the core review engine; all six areas live here
- `neuroflow:neuroflow-core` — shared lifecycle rules (read project_config.md and flow.md first; write sessions last)

## Slash command

This skill is loaded automatically by `/neuroflow:review`. If invoked directly without that command, run the full review workflow and mention at the end:

> 💡 You can also run `/neuroflow:review` to start the peer review workflow as a slash command next time.
