---
name: interview
description: Interview preparation from either side of the table — determine whether you are the interviewer or interviewee, generate tailored questions grounded in your research context, run a practice Q&A, and optionally evaluate answers.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
writes:
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /interview

## What this command does

Helps with interview preparation from either side of the table. If `.neuroflow/project_config.md` exists, reads the user's research context so that questions can be grounded in their actual work.

---

## Step 1 — Determine role

Ask: **"Are you the interviewer or the interviewee?"**

- **Interviewer** → go to [Interviewer mode](#interviewer-mode)
- **Interviewee** → go to [Interviewee mode](#interviewee-mode)

---

## Step 2 — Read context

If `.neuroflow/project_config.md` exists, read it. Extract:

- Research question or topic
- Modality (EEG, fMRI, eye tracking, etc.)
- Tools and methods used
- Current phase and any completed work

Use this to personalize questions throughout the session. If `.neuroflow/` does not exist, ask the user for any relevant background before generating questions.

---

## Interviewer mode

### 2a — Gather interview details

Ask:

1. "What is the role or position you are hiring for?"
2. "What level is this role? (student / postdoc / engineer / senior / other)"
3. "Are there specific topics or skills you want to assess? (optional)"

If the project context includes a relevant modality or method, suggest including questions on those.

### 2b — Generate question set

Produce a structured question set grouped by topic. Default topics:

| Topic | Example questions |
|---|---|
| Research background | Tell me about your most significant project. What was the hypothesis and how did you test it? |
| Technical skills | How do you approach preprocessing EEG data? What artifact rejection methods have you used? |
| Problem-solving | Describe a time an analysis did not replicate. How did you diagnose it? |
| Communication | How do you explain your research to a non-expert audience? |
| Collaboration | Describe a disagreement with a co-author or collaborator. How was it resolved? |
| Motivation | Why this lab / position / field? |

If the role or project context points to a specific modality or method, add domain-specific questions (e.g., ICA, decoding pipelines, real-time systems, BIDS compliance, GLM).

Aim for 8–12 questions. After presenting the list, ask:

> "Would you like to add, remove, or refine any questions before we proceed?"

### 2c — Optional: run through the questions

Ask: **"Do you want to run through the questions now? I can model ideal answers, or you can note your impressions as we go."**

- If yes: present each question one at a time. After each, pause for the interviewer to note their impression, then continue.
- If no: save the question set and finish.

### 2d — Save and wrap up

Print the final question set as a clean markdown list. Suggest saving it to a file (e.g., `interview-questions-[role]-[date].md`).

Append a summary to `.neuroflow/sessions/YYYY-MM-DD.md`.

---

## Interviewee mode

### 2a — Gather interview details

Ask:

1. "What role or position are you interviewing for?"
2. "What is the lab, company, or organisation?"
3. "Do you know what topics or skills are likely to be assessed? (optional)"

### 2b — Generate likely questions

Based on the role, organisation type, and project context, generate a list of likely questions. Group by topic (same categories as Interviewer mode).

If `.neuroflow/project_config.md` exists, tailor questions to the user's actual research — for example, ask about their specific modality, their current pipeline, or their published or ongoing work.

Aim for 10–15 questions across all topics. After presenting the list, ask:

> "Would you like to add topics or adjust the focus before we practice?"

### 2c — Practice Q&A

Ask: **"Do you want to practice answering these questions now?"**

If yes:

1. Present questions one at a time.
2. The user types their answer.
3. After each answer, offer brief feedback:
   - What was strong
   - What could be clearer or more specific
   - A suggested refinement (ask the user if they want this before providing it)

Continue until all questions are done or the user stops. The user can say "skip", "next", or "stop" at any point.

### 2d — Evaluation summary (optional)

At the end of the practice session, ask: **"Would you like an overall evaluation of your readiness?"**

If yes, provide:

- Areas of strength — topics where answers were clear, specific, and confident
- Areas to strengthen — topics needing more preparation
- 1–3 concrete suggestions for improvement

### 2e — Save and wrap up

Summarise what was covered and any key preparation notes. Append to `.neuroflow/sessions/YYYY-MM-DD.md`.

---

## Phase suggestion (both modes)

At the end of any interview session, if `.neuroflow/project_config.md` exists, read the current `active_phase` and any `recommended_phases` already set.

Based on the interview content and the user's current research context, suggest which neuroflow phases they are likely to be moving through next. Use the full pipeline as reference:

```
ideation → preregistration → grant-proposal → experiment →
tool-build → tool-validate → data → data-preprocess →
data-analyze → paper → write-report →
notes → finance
```

Print a brief phase outlook at the end of the session:

```
Based on this session, here are the neuroflow phases most relevant to where you are heading:

  → data-analyze         ← your next likely phase
  → paper

Run /neuroflow:phase at any time to see your full phase map.
```

Only suggest phases that are genuinely relevant given what was discussed. Skip this block if the conversation was entirely unrelated to the user's research pipeline (e.g., pure practice Q&A with no pipeline context).
