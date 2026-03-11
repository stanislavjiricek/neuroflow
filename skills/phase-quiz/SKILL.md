---
name: phase-quiz
description: Phase guidance for the neuroflow /quiz command. Loaded automatically when /quiz is invoked to orient behaviour, question quality, and mode-specific workflow for neuroscience quiz sessions.
---

# phase-quiz

The quiz command is a standalone utility for neuroscience knowledge testing. It has no project memory phase and does not require `.neuroflow/` to exist.

## Approach

- Determine mode first (flashcards, pub quiz, throw questions) before generating any content
- Default to **throw questions** if the user provides no instruction — never stall waiting for a mode choice
- Ask for subfield preference once, then proceed — do not re-ask between questions
- All content must be scientifically accurate; entertaining framing is encouraged but must never compromise accuracy
- Calibrate difficulty to the subfield; general sessions should span breadth, not just easy facts

## Mode guidance

### Flashcards

- Keep fronts concise — one term or one question, not a paragraph
- Backs should be complete but tight — enough to understand, not a lecture
- When saving, use the Markdown two-column table format specified in the command; do not generate HTML or images
- The layout note ("Print double-sided, cut along rows") reminds the user of the intended use — always include it

### Pub quiz

- Balance entertainment with accuracy — jokes land better when the science is right
- Round difficulty should genuinely escalate: Round 1 accessible, Round 2 methods/mechanisms, Round 3 advanced/Nobel
- House rules should be funny and neuroscience-specific; avoid generic pub quiz rules
- Read aloud the fun fact after the answer — this is what makes pub quiz memorable

### Throw questions (default)

- Pace matters — fire the next question immediately after feedback; do not add filler
- Vary format across a session: recall, multiple choice, true/false, fill-in-the-blank
- Show score every 5 questions; this keeps engagement high
- Accept partial answers generously if the core concept is correct — flag the missing detail

## Question quality standards

- Use correct anatomical, physiological, and methodological terminology
- Cite SI units where relevant (Hz for frequency, mV for membrane potential, ms for latency)
- For oscillation frequencies, use standard consensus ranges (e.g. alpha 8–13 Hz, theta 4–8 Hz, beta 13–30 Hz, gamma >30 Hz)
- Avoid ambiguous questions where multiple correct answers exist — or, if used intentionally, accept all valid answers
- Flag if a question relies on a contested or evolving consensus — note this briefly in the explanation

## Relevant skills

- `neuroflow:neuroflow-core` — follow the command lifecycle; append to `sessions/` if `.neuroflow/` exists
