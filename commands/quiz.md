---
name: quiz
description: Neuroscience quiz — test your knowledge with flashcards, a pub quiz, or rapid-fire questions. Covers general neuroscience or a chosen subfield.
phase: utility
reads:
  - .neuroflow/project_config.md
  - .neuroflow/flow.md
  - skills/phase-quiz/SKILL.md
writes:
  - .neuroflow/sessions/YYYY-MM-DD.md
---

# /quiz

Read the `neuroflow:phase-quiz` skill first. Then follow the neuroflow-core lifecycle: read `project_config.md` and `flow.md` if they exist.

## What this command does

Runs an interactive neuroscience quiz. Supports three modes:

- **flashcards** — question/answer cards that can be saved as a printable A4 PDF-ready layout
- **pubquiz** — entertaining neuroscience pub quiz questions with suggested house rules
- **throw questions** — rapid-fire Q&A (default if the user gives no instruction)

---

## Steps

### 1 — Mode selection

If the user has specified a mode in their invocation, use it directly. Otherwise, present the three options and ask:

> "Which quiz mode would you like?
> 1. **Flashcards** — Q&A cards you can save and print (A4 layout, both sides)
> 2. **Pub quiz** — fun questions with house rules for a neuroscience pub night
> 3. **Throw questions** — just fire questions at me (default)"

If the user says nothing or types any variation of "go", "start", "default" — use **throw questions**.

### 2 — Subfield selection

After mode is confirmed, ask:

> "Any particular area, or keep it general?
> Examples: neuroanatomy, EEG/oscillations, synaptic physiology, cognitive neuroscience, clinical neuroscience, neuroimaging, pharmacology, developmental neuroscience — or just say 'general'."

If the user skips this, default to **general neuroscience**.

### 3 — Run the chosen mode

#### Mode A — Flashcards

Generate a set of 10 flashcards (or as many as the user requests). Each card has:

- **Front:** a concise question or term
- **Back:** a clear, accurate answer (2–4 sentences max)

Calibrate difficulty to the subfield — use precise scientific language; do not oversimplify.

Example cards:
- Front: "What is the typical frequency range of alpha oscillations?" → Back: "Alpha oscillations occur in the 8–13 Hz range and are most prominent over occipital cortex. They are associated with relaxed wakefulness and visual idling. Alpha power typically increases when eyes are closed and suppresses when visual processing begins."
- Front: "Name the three layers of the meninges." → Back: "Working from outside in: dura mater (tough outer layer), arachnoid mater (middle, with the subarachnoid space below it), and pia mater (thin innermost layer directly adhering to the brain surface)."

After generating the cards, ask the user:

> "Would you like to save these as a printable layout?"

If yes: generate a Markdown file formatted for A4 printing:
- File: `quiz-flashcards-[subfield]-[YYYY-MM-DD].md`
- Layout: two-column table, front on the left, back on the right; rows are cards
- Header: small neuroflow logo reference (`<!-- neuroflow -->`) and date
- Footer note: "Print double-sided, cut along rows. neuroflow · neuroscience quiz"
- Save to the current working directory (not inside `.neuroflow/`)

#### Mode B — Pub quiz

Generate 15 questions across three rounds (5 per round), with increasing difficulty:

- **Round 1 — Warm-up:** accessible questions, broad neuroscience facts
- **Round 2 — Lab coat required:** more technical, methods and mechanisms
- **Round 3 — Nobel territory:** advanced, cutting-edge, or Nobel Prize–linked discoveries

For each question provide:
- Question text (entertaining but accurate)
- Answer
- A one-sentence "fun fact" to read aloud after revealing the answer

Also suggest **5 neuro-themed pub quiz house rules**, for example:
- "If you answer in Latin, it counts double (but you must use it correctly)."
- "The team that names the most cranial nerves in 30 seconds gets a bonus point."
- "Any question about the hippocampus must be answered while pointing to your own head."
- "Wrong answers about the cerebellum cost a point — it controls precision, after all."
- "First team to correctly identify a real vs made-up brain region wins a tiebreaker coin."

Keep the tone light and fun. Accuracy must still be maintained.

#### Mode C — Throw questions (default)

Fire one question at a time. After each answer, immediately give:
- ✅ Correct / ❌ Incorrect
- The correct answer (if wrong) or a reinforcing fact (if right)
- A brief explanation (1–3 sentences)

Then move to the next question without pause. Continue until the user says "stop", "enough", or "quit".

Keep track of score in a running tally shown after every 5 questions:
> "Score so far: 4 / 5 ✨"

Vary question format:
- Direct recall ("What does GABA stand for?")
- Multiple choice (offer 4 options occasionally)
- True / False
- Fill in the blank ("The _____ lobe is primarily responsible for auditory processing.")

---

## At end

- If `.neuroflow/` exists: append to `.neuroflow/sessions/YYYY-MM-DD.md` with a one-line entry: mode used, subfield, number of questions, score if applicable.
- If flashcard file was saved: confirm the save path to the user.
- Offer to run again in a different mode or subfield.
