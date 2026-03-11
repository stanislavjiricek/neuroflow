---
title: /interview
---

# `/neuroflow:interview`

**Interview preparation from either side of the table — generate tailored questions, run practice Q&A, and optionally evaluate readiness.**

`/interview` prepares you for interviews whether you are the interviewer or the interviewee. If `.neuroflow/project_config.md` exists, questions are grounded in your actual research context.

---

## When to use it

- You have an academic or industry interview coming up and want to practice
- You are hiring and want a structured, tailored question set
- You want to evaluate your readiness and get a gap analysis before the interview

---

## Two modes

Claude asks: **"Are you the interviewer or the interviewee?"**

=== "Interviewee"

    **Step 1 — Gather details**

    Claude asks:
    - What role or position are you interviewing for?
    - What is the lab, company, or organisation?
    - What topics or skills are likely to be assessed? (optional)

    **Step 2 — Generate likely questions**

    Based on role, organisation type, and your research context, Claude generates 10–15 questions grouped by topic:

    | Topic | Example questions |
    |---|---|
    | Research background | Tell me about your most significant project. What was the hypothesis and how did you test it? |
    | Technical skills | How do you approach preprocessing EEG data? What artifact rejection methods have you used? |
    | Problem-solving | Describe a time an analysis did not replicate. How did you diagnose it? |
    | Communication | How do you explain your research to a non-expert audience? |
    | Collaboration | Describe a disagreement with a co-author. How was it resolved? |
    | Motivation | Why this lab / position / field? |

    **Step 3 — Practice Q&A**

    Questions are presented one at a time. After each answer Claude gives brief feedback: what was strong, what could be clearer, and a suggested refinement (optional).

    **Step 4 — Evaluation summary (optional)**

    At the end, Claude provides:
    - Areas of strength
    - Areas to strengthen
    - 1–3 concrete improvement suggestions

=== "Interviewer"

    **Step 1 — Gather details**

    Claude asks:
    - What is the role or position you are hiring for?
    - What level? (student / postdoc / engineer / senior / other)
    - Any specific topics or skills to assess? (optional)

    **Step 2 — Generate question set**

    Claude produces a structured question set (8–12 questions) grouped by topic. Questions are tailored to the role level and any modality or method in your project context.

    **Step 3 — Run through the questions (optional)**

    Present each question one at a time. Note impressions as you go.

    **Step 4 — Save the question set**

    The final question set is printed as a clean markdown list. Suggested file name: `interview-questions-[role]-[date].md`.

---

## Files read and written

| Direction | Files |
|---|---|
| Reads | `.neuroflow/project_config.md`, `.neuroflow/flow.md` (if they exist) |
| Writes | `.neuroflow/sessions/YYYY-MM-DD.md` |

---

## Related commands

- [`/ideation`](ideation.md) — if you need to clarify your research contributions before an interview
- [`/write-report`](write-report.md) — generate a project summary you can reference during preparation
